import glob
import json
import os
import subprocess
import time

from .parse import parse_rsync_progress
from .state import (
    INSTALL_STEPS, MNT, LOG_PATH,
    log, set_state, step_percent,
)

CONSOLE_KEYMAP = {"gb": "uk", "br": "br-abnt2"}


def run(cmd, **kw):
    """Run a command list, tee output to log, raise on failure."""
    log("+ " + " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if res.stdout:
        log(res.stdout)
    if res.stderr:
        log(res.stderr)
    if res.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed ({res.returncode}): {res.stderr.strip()}")
    return res


def chroot(cmd_str):
    """Run a bash string inside the installed system via arch-chroot."""
    run(["arch-chroot", MNT, "/bin/bash", "-c", cmd_str])


def is_uefi():
    """True if the live system booted in UEFI mode."""
    return os.path.isdir("/sys/firmware/efi")


def do_autopart(disk):
    """Wipe disk, create partitions, format them. Returns {root_part, efi_part or None}."""
    uefi = is_uefi()

    run(["wipefs", "-a", disk])

    if uefi:
        # GPT: 512M EFI (type=uefi) + rest Linux
        sfdisk_input = "label: gpt\n,512M,U\n,,L\n"
    else:
        # MBR: whole disk Linux, bootable
        sfdisk_input = "label: dos\n,,83,*\n"

    res = subprocess.run(
        ["sfdisk", "--no-reread", disk],
        input=sfdisk_input, text=True, capture_output=True,
    )
    log("sfdisk stdout: " + res.stdout)
    log("sfdisk stderr: " + res.stderr)
    if res.returncode != 0:
        raise RuntimeError(f"sfdisk failed: {res.stderr.strip()}")

    subprocess.run(["partprobe", disk], capture_output=True)
    time.sleep(1)

    # Discover created partition paths via lsblk
    res2 = subprocess.run(
        ["lsblk", "-J", "-o", "NAME,TYPE", disk],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(res2.stdout)
    parts = []
    for dev in data.get("blockdevices", []):
        for child in dev.get("children", []):
            if child.get("type") == "part":
                parts.append("/dev/" + child["name"])
    parts.sort()

    if uefi:
        if len(parts) < 2:
            raise RuntimeError(f"Expected 2 partitions after sfdisk, got: {parts}")
        efi_part, root_part = parts[0], parts[1]
        run(["mkfs.vfat", "-F32", efi_part])
        run(["mkfs.ext4", "-F", root_part])
        return {"root_part": root_part, "efi_part": efi_part}
    else:
        if len(parts) < 1:
            raise RuntimeError(f"Expected 1 partition after sfdisk, got: {parts}")
        root_part = parts[0]
        run(["mkfs.ext4", "-F", root_part])
        return {"root_part": root_part, "efi_part": None}


def copy_airootfs():
    """rsync /run/archiso/airootfs -> /mnt with live percent into the copy step."""
    src = "/run/archiso/airootfs/"
    proc = subprocess.Popen(
        ["rsync", "-aAXH", "--info=progress2", src, MNT + "/"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    for line in proc.stdout:
        pct = parse_rsync_progress(line)
        if pct is not None:
            set_state(percent=step_percent(2, pct))
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("rsync copy failed")


def sync_upperdir():
    """Copy live-session writes (cowspace upperdir) into the installed root."""
    matches = glob.glob("/run/archiso/cowspace/**/upperdir", recursive=True)
    matches = [m for m in matches if "/x86_64/" in m]
    if matches:
        run(["rsync", "-aAXH", matches[0] + "/", MNT + "/"])


def configure_system():
    """Generate fstab, set machine ID, write mkinitcpio preset, rebuild initramfs."""
    chroot("systemd-machine-id-setup")
    res = subprocess.run(["genfstab", "-U", MNT], capture_output=True, text=True, check=True)
    with open(MNT + "/etc/fstab", "a") as f:
        f.write(res.stdout)
    preset = (
        "PRESETS=('default' 'fallback')\n"
        "ALL_kver='/boot/vmlinuz-linux'\n"
        "ALL_config='/etc/mkinitcpio.conf'\n"
        'default_image="/boot/initramfs-linux.img"\n'
        'fallback_image="/boot/initramfs-linux-fallback.img"\n'
        'fallback_options="-S autodetect"\n'
    )
    with open(MNT + "/etc/mkinitcpio.d/linux.preset", "w") as f:
        f.write(preset)
    chroot("sed -i 's/^COMPRESSION=\"xz\"/#COMPRESSION=\"xz\"/' /etc/mkinitcpio.conf")
    chroot("sed -i 's/^COMPRESSION_OPTIONS=/#COMPRESSION_OPTIONS=/' /etc/mkinitcpio.conf")
    hooks = "base systemd autodetect microcode modconf kms keyboard keymap sd-vconsole block filesystems fsck"
    chroot(f"sed -i -E 's|^HOOKS=.*|HOOKS=({hooks})|' /etc/mkinitcpio.conf")
    chroot("mkinitcpio -p linux")


def configure_timezone(timezone):
    """Symlink the chosen timezone and sync the hardware clock."""
    chroot(f"ln -sf /usr/share/zoneinfo/{timezone} /etc/localtime")
    chroot("hwclock --systohc")


def configure_locale(locale):
    """Enable locale in locale.gen, generate it, write locale.conf."""
    with open(MNT + "/etc/locale.gen", "a") as f:
        f.write(f"{locale} UTF-8\n")
    chroot("locale-gen")
    with open(MNT + "/etc/locale.conf", "w") as f:
        f.write(f"LANG={locale}\n")


def configure_keymap(layout, username):
    """Write vconsole.conf and update xkb layout in the installed user's WM config."""
    console_km = CONSOLE_KEYMAP.get(layout, layout)
    with open(MNT + "/etc/vconsole.conf", "w") as f:
        f.write(f"KEYMAP={console_km}\n")
    mango_cfg_host = MNT + f"/home/{username}/.config/mango/config.conf"
    if os.path.exists(mango_cfg_host):
        chroot(f"sed -i 's/^xkb_rules_layout=.*/xkb_rules_layout={layout}/' /home/{username}/.config/mango/config.conf")


def configure_hostname(hostname):
    """Write /etc/hostname and /etc/hosts."""
    with open(MNT + "/etc/hostname", "w") as f:
        f.write(hostname + "\n")
    hosts = (
        "127.0.0.1   localhost\n"
        "::1         localhost\n"
        f"127.0.1.1   {hostname}.localdomain {hostname}\n"
    )
    with open(MNT + "/etc/hosts", "w") as f:
        f.write(hosts)


def configure_user(username, password):
    """Rename the 'live' user to the chosen username, set password, fix ownership."""
    live = "live"
    subprocess.run(
        ["arch-chroot", MNT, "chpasswd"],
        input=f"{live}:{password}\n", text=True, check=True,
    )
    chroot(f"find /home/{live} -type f -exec sed -i 's/{live}/{username}/g' {{}} +")
    for f in ("group", "gshadow", "passwd", "shadow"):
        chroot(f"sed -i 's/{live}/{username}/g' /etc/{f}")
    chroot(f"mv /home/{live} /home/{username}")
    chroot(f"chown -R {username}:users /home/{username}")


def install_grub(root_part, uefi):
    """Install GRUB for UEFI (x86_64-efi) or BIOS (i386-pc) and generate grub.cfg."""
    if uefi:
        chroot("grub-install --target=x86_64-efi --efi-directory=/boot "
               "--bootloader-id=GRUB --recheck")
    else:
        res = subprocess.run(["lsblk", "-no", "pkname", root_part],
                             capture_output=True, text=True)
        disk = "/dev/" + res.stdout.strip().splitlines()[0]
        run(["grub-install", "--target=i386-pc",
             "--boot-directory=" + MNT + "/boot", disk])
    chroot("grub-mkconfig -o /boot/grub/grub.cfg")


def cleanup():
    """Remove live-only scripts and services; lock down sudo for the installed system."""
    for p in (
        "/home/*/Scripts/abinstall",
        "/home/*/Scripts/fb-install",
        "/home/*/Scripts/abi-install",
        "/home/*/Scripts/abi-installer.py",
        "/home/*/Scripts/lib",
        "/etc/systemd/system/getty@tty1.service.d",
        "/etc/skel",
    ):
        chroot(f"rm -rf {p}")
    chroot("sed -i '/fruitbang\\.install/d' /etc/hosts")
    chroot("sed -i 's/volatile/auto/g' /etc/systemd/journald.conf.d/volatile-storage.conf 2>/dev/null || true")
    chroot("mv /etc/systemd/journald.conf.d/volatile-storage.conf /etc/systemd/journald.conf.d/auto-storage.conf 2>/dev/null || true")
    chroot("unlink /etc/systemd/system/multi-user.target.wants/pacman-init.service 2>/dev/null || true")
    chroot("rm -f /etc/systemd/system/pacman-init.service")
    chroot("rm -f /etc/systemd/system/default.target")
    chroot("rm -f /etc/systemd/system/etc-pacman.d-gnupg.mount")
    chroot("sed -i '/^Hidden=true/d' /usr/share/applications/gparted.desktop 2>/dev/null || true")
    chroot("sed -i 's/^%wheel ALL=(ALL:ALL) NOPASSWD: ALL/# %wheel ALL=(ALL:ALL) NOPASSWD: ALL/' /etc/sudoers")
    chroot("sed -i 's/^# %wheel ALL=(ALL:ALL) ALL$/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers")


def do_install(cfg):
    """Background install worker. cfg keys: root_part, efi_part, hostname, username, password."""
    try:
        set_state(step=INSTALL_STEPS[0], percent=step_percent(0, 100))
        uefi = is_uefi()

        set_state(step=INSTALL_STEPS[1], percent=step_percent(1, 50))
        run(["mount", cfg["root_part"], MNT])
        if uefi and cfg.get("efi_part"):
            run(["mkdir", "-p", MNT + "/boot"])
            run(["mount", cfg["efi_part"], MNT + "/boot"])
        set_state(percent=step_percent(1, 100))

        set_state(step=INSTALL_STEPS[2], percent=step_percent(2, 0))
        copy_airootfs()

        set_state(step=INSTALL_STEPS[3], percent=step_percent(3, 50))
        sync_upperdir()
        set_state(percent=step_percent(3, 100))

        set_state(step=INSTALL_STEPS[4], percent=step_percent(4, 20))
        configure_system()
        set_state(percent=step_percent(4, 100))

        set_state(step=INSTALL_STEPS[5], percent=step_percent(5, 20))
        configure_hostname(cfg["hostname"])
        set_state(percent=step_percent(5, 50))
        configure_timezone(cfg.get("timezone", "UTC"))
        configure_locale(cfg.get("locale", "en_GB.UTF-8"))
        set_state(percent=step_percent(5, 100))

        set_state(step=INSTALL_STEPS[6], percent=step_percent(6, 50))
        configure_user(cfg["username"], cfg["password"])
        configure_keymap(cfg.get("keymap", "us"), cfg["username"])
        set_state(percent=step_percent(6, 100))

        set_state(step=INSTALL_STEPS[7], percent=step_percent(7, 20))
        install_grub(cfg["root_part"], uefi)
        set_state(percent=step_percent(7, 100))

        set_state(step=INSTALL_STEPS[8], percent=step_percent(8, 50))
        cleanup()
        set_state(step="Done", percent=100, done=True)
    except Exception as e:
        log("ERROR: " + str(e))
        set_state(error=str(e))
