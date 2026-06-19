#!/usr/bin/env python3
"""FruitBang browser installer — Python stdlib HTTP server + HTML wizard."""

import json
import re

# --- Pure helpers (unit-tested) ---

# Step weights must sum to 100. Index aligns with INSTALL_STEPS order.
STEP_WEIGHTS = [2, 3, 60, 5, 8, 2, 5, 10, 5]

NAME_RE = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")


def validate_name(s):
    """True if s is a safe hostname/username (lowercase, no shell metachars)."""
    return bool(NAME_RE.match(s))


def parse_lsblk(json_str):
    """Parse `lsblk -J` output into a flat list of partitions.

    Returns list of {"path": "/dev/sda1", "size": "512M"}.
    Only type=="part" entries are returned (disks excluded).
    """
    data = json.loads(json_str)
    out = []

    def walk(node):
        if node.get("type") == "part":
            out.append({"path": "/dev/" + node["name"], "size": node.get("size", "")})
        for child in node.get("children", []):
            walk(child)

    for dev in data.get("blockdevices", []):
        walk(dev)
    return out


RSYNC_PCT_RE = re.compile(r"\s(\d{1,3})%")


def parse_rsync_progress(line):
    """Extract integer percent from an rsync --info=progress2 line, or None."""
    m = RSYNC_PCT_RE.search(line)
    if not m:
        return None
    pct = int(m.group(1))
    return pct if 0 <= pct <= 100 else None


def step_percent(step_index, sub_pct):
    """Overall percent given the current step index and its sub-progress (0-100)."""
    prior = sum(STEP_WEIGHTS[:step_index])
    current = STEP_WEIGHTS[step_index] * (sub_pct / 100.0)
    return int(prior + current)


# Human-readable label per install step; index aligns with STEP_WEIGHTS.
INSTALL_STEPS = [
    "Detecting firmware mode",
    "Mounting partitions",
    "Copying system files",
    "Syncing live session changes",
    "Configuring fstab and initramfs",
    "Setting hostname",
    "Creating user account",
    "Installing bootloader",
    "Cleaning up",
]


def new_state():
    """Fresh shared install state dict."""
    return {"percent": 0, "step": "", "done": False, "error": None}


import subprocess
import threading

LOG_PATH = "/tmp/fb-install.log"
MNT = "/mnt"

# Module-level shared state and lock (single install at a time).
STATE = new_state()
STATE_LOCK = threading.Lock()


def log(msg):
    with open(LOG_PATH, "a") as f:
        f.write(msg + "\n")


def set_state(**kw):
    with STATE_LOCK:
        STATE.update(kw)


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
    run(["arch-chroot", MNT, "/bin/bash", "-c", cmd_str])


def is_uefi():
    import os
    return os.path.isdir("/sys/firmware/efi")


def do_install(cfg):
    """Background install worker. cfg keys: root_part, efi_part, hostname, username, password."""
    try:
        # Step 0: firmware
        set_state(step=INSTALL_STEPS[0], percent=step_percent(0, 100))
        uefi = is_uefi()

        # Step 1: mount
        set_state(step=INSTALL_STEPS[1], percent=step_percent(1, 50))
        run(["mount", cfg["root_part"], MNT])
        if uefi and cfg.get("efi_part"):
            run(["mkdir", "-p", MNT + "/boot"])
            run(["mount", cfg["efi_part"], MNT + "/boot"])
        set_state(percent=step_percent(1, 100))

        # Step 2: copy airootfs with live progress
        set_state(step=INSTALL_STEPS[2], percent=step_percent(2, 0))
        copy_airootfs()

        # Step 3: sync cowspace upperdir
        set_state(step=INSTALL_STEPS[3], percent=step_percent(3, 50))
        sync_upperdir()
        set_state(percent=step_percent(3, 100))

        # Step 4: fstab, mkinitcpio, machine-id
        set_state(step=INSTALL_STEPS[4], percent=step_percent(4, 20))
        configure_system()
        set_state(percent=step_percent(4, 100))

        # Step 5: hostname
        set_state(step=INSTALL_STEPS[5], percent=step_percent(5, 50))
        configure_hostname(cfg["hostname"])
        set_state(percent=step_percent(5, 100))

        # Step 6: user
        set_state(step=INSTALL_STEPS[6], percent=step_percent(6, 50))
        configure_user(cfg["username"], cfg["password"])
        set_state(percent=step_percent(6, 100))

        # Step 7: bootloader
        set_state(step=INSTALL_STEPS[7], percent=step_percent(7, 20))
        install_grub(cfg["root_part"], uefi)
        set_state(percent=step_percent(7, 100))

        # Step 8: cleanup
        set_state(step=INSTALL_STEPS[8], percent=step_percent(8, 50))
        cleanup()
        set_state(step="Done", percent=100, done=True)
    except Exception as e:
        log("ERROR: " + str(e))
        set_state(error=str(e))


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
    import glob
    matches = glob.glob("/run/archiso/cowspace/*/x86_64/upperdir")
    if matches:
        run(["rsync", "-aAXH", matches[0] + "/", MNT + "/"])


def configure_system():
    chroot("systemd-machine-id-setup")
    res = subprocess.run(["genfstab", "-U", MNT], capture_output=True, text=True)
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
    chroot("mkinitcpio -p linux")


def configure_hostname(hostname):
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
    for p in (
        "/home/*/Scripts/abinstall",
        "/home/*/Scripts/fb-install",
        "/etc/systemd/system/getty@tty1.service.d",
        "/etc/skel",
    ):
        chroot(f"rm -rf {p}")
    chroot("sed -i 's/^%wheel ALL=(ALL:ALL) NOPASSWD: ALL/# %wheel ALL=(ALL:ALL) NOPASSWD: ALL/' /etc/sudoers")
    chroot("sed -i 's/^# %wheel ALL=(ALL:ALL) ALL$/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers")
