#!/usr/bin/env python3
"""FruitBang browser installer — Python stdlib HTTP server + HTML wizard."""

import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 7777

PAGE_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FruitBang Installer</title>
<style>
  body { background:#201b14; color:#c9c0b0; font-family:monospace;
         max-width:640px; margin:40px auto; padding:0 16px; line-height:1.5; }
  h1, h2 { color:#c9b890; }
  .panel { display:none; }
  .panel.active { display:block; }
  button { background:#c9b890; color:#201b14; border:none; border-radius:6px;
           padding:10px 18px; font-family:monospace; font-size:1em; cursor:pointer; margin-right:8px; }
  button:disabled { opacity:0.4; cursor:default; }
  button.danger { background:#e06060; color:#fff; }
  label { display:block; margin:8px 0; }
  input[type=text], input[type=password] {
    background:#2c261d; color:#c9c0b0; border:1px solid #c9b890;
    border-radius:6px; padding:6px; font-family:monospace; width:100%; box-sizing:border-box; }
  select {
    background:#2c261d; color:#c9c0b0; border:1px solid #c9b890;
    border-radius:6px; padding:6px; font-family:monospace; }
  .warn { color:#e0a060; border:1px solid #e0a060; border-radius:6px; padding:10px; margin-bottom:12px; }
  .err  { color:#e06060; border:1px solid #e06060; border-radius:6px; padding:10px; margin:10px 0; }
  #bar { background:#2c261d; border-radius:6px; height:24px; overflow:hidden; margin:12px 0; }
  #fill { background:#c9b890; height:100%; width:0%; transition:width 0.3s; }
  pre { background:#2c261d; border-radius:6px; padding:8px; font-size:0.85em; white-space:pre-wrap; }
</style>
</head>
<body>
<h1>FruitBang Installer</h1>
<div id="err" class="err" style="display:none"></div>

<div id="p-welcome" class="panel active">
  <div class="warn"><b>Warning:</b> Installing will erase data on the target disk.
  Back up anything important first.</div>
  <p>Requirements: booted from FruitBang live ISO, 20GB+ target disk.</p>
  <button onclick="show('mode')">Begin</button>
</div>

<div id="p-mode" class="panel">
  <h2>Partitioning</h2>
  <p><b>Auto</b> — wipe a whole disk and partition it automatically.</p>
  <p><b>Manual</b> — you have already partitioned; select existing partitions.</p>
  <button onclick="showAuto()">Auto — erase whole disk</button>
  <button onclick="showManual()">Manual — select partitions</button>
</div>

<div id="p-autodisk" class="panel">
  <h2>Auto-partition</h2>
  <div class="warn"><b>WARNING: All data on the selected disk will be permanently erased.</b></div>
  <label>Disk: <select id="wholedisk"></select></label>
  <p id="autodisk-uefi"></p>
  <button class="danger" onclick="confirmAutopart()">Erase disk and partition</button>
</div>

<div id="p-disk" class="panel">
  <h2>Select Partitions</h2>
  <p>Choose the root partition (and EFI partition if UEFI).</p>
  <div id="disks">Loading...</div>
  <label>Root partition: <select id="root"></select></label>
  <label>EFI partition (UEFI only, else leave blank):
    <select id="efi"><option value="">none</option></select></label>
  <button onclick="checkPartitions()">Continue</button>
</div>

<div id="p-part" class="panel">
  <h2>Partition the Disk</h2>
  <p>If your disk is not yet partitioned, open a terminal and run:</p>
  <pre>sudo cfdisk /dev/sdX</pre>
  <p>Create a root partition (and a 512M EFI partition for UEFI). Return here when done.</p>
  <button onclick="checkPartitions()">Continue</button>
</div>

<div id="p-install" class="panel">
  <h2>Installing</h2>
  <div id="bar"><div id="fill"></div></div>
  <p id="step">Starting...</p>
  <pre id="logtail"></pre>
</div>

<div id="p-configure" class="panel">
  <h2>Configure System</h2>
  <label>Hostname: <input type="text" id="hostname" value="fruitbang"></label>
  <label>Username: <input type="text" id="username"></label>
  <label>Password: <input type="password" id="pw1"></label>
  <label>Confirm password: <input type="password" id="pw2"></label>
  <label>Timezone:
    <select id="timezone">
      <optgroup label="Europe">
        <option value="Europe/London" selected>Europe/London</option>
        <option value="Europe/Dublin">Europe/Dublin</option>
        <option value="Europe/Lisbon">Europe/Lisbon</option>
        <option value="Europe/Paris">Europe/Paris</option>
        <option value="Europe/Brussels">Europe/Brussels</option>
        <option value="Europe/Amsterdam">Europe/Amsterdam</option>
        <option value="Europe/Berlin">Europe/Berlin</option>
        <option value="Europe/Vienna">Europe/Vienna</option>
        <option value="Europe/Zurich">Europe/Zurich</option>
        <option value="Europe/Madrid">Europe/Madrid</option>
        <option value="Europe/Rome">Europe/Rome</option>
        <option value="Europe/Warsaw">Europe/Warsaw</option>
        <option value="Europe/Stockholm">Europe/Stockholm</option>
        <option value="Europe/Oslo">Europe/Oslo</option>
        <option value="Europe/Copenhagen">Europe/Copenhagen</option>
        <option value="Europe/Helsinki">Europe/Helsinki</option>
        <option value="Europe/Athens">Europe/Athens</option>
        <option value="Europe/Bucharest">Europe/Bucharest</option>
        <option value="Europe/Moscow">Europe/Moscow</option>
        <option value="Europe/Istanbul">Europe/Istanbul</option>
      </optgroup>
      <optgroup label="America">
        <option value="America/New_York">America/New_York</option>
        <option value="America/Chicago">America/Chicago</option>
        <option value="America/Denver">America/Denver</option>
        <option value="America/Los_Angeles">America/Los_Angeles</option>
        <option value="America/Toronto">America/Toronto</option>
        <option value="America/Vancouver">America/Vancouver</option>
        <option value="America/Sao_Paulo">America/Sao_Paulo</option>
        <option value="America/Mexico_City">America/Mexico_City</option>
        <option value="America/Argentina/Buenos_Aires">America/Argentina/Buenos_Aires</option>
      </optgroup>
      <optgroup label="Asia">
        <option value="Asia/Dubai">Asia/Dubai</option>
        <option value="Asia/Kolkata">Asia/Kolkata</option>
        <option value="Asia/Bangkok">Asia/Bangkok</option>
        <option value="Asia/Singapore">Asia/Singapore</option>
        <option value="Asia/Shanghai">Asia/Shanghai</option>
        <option value="Asia/Tokyo">Asia/Tokyo</option>
        <option value="Asia/Seoul">Asia/Seoul</option>
        <option value="Asia/Jerusalem">Asia/Jerusalem</option>
      </optgroup>
      <optgroup label="Africa / Pacific / Other">
        <option value="Africa/Johannesburg">Africa/Johannesburg</option>
        <option value="Africa/Cairo">Africa/Cairo</option>
        <option value="Australia/Sydney">Australia/Sydney</option>
        <option value="Pacific/Auckland">Pacific/Auckland</option>
        <option value="UTC">UTC</option>
      </optgroup>
    </select>
  </label>
  <label>Locale:
    <select id="locale">
      <option value="en_GB.UTF-8" selected>en_GB.UTF-8 (English UK)</option>
      <option value="en_US.UTF-8">en_US.UTF-8 (English US)</option>
      <option value="de_DE.UTF-8">de_DE.UTF-8 (German)</option>
      <option value="fr_FR.UTF-8">fr_FR.UTF-8 (French)</option>
      <option value="es_ES.UTF-8">es_ES.UTF-8 (Spanish)</option>
      <option value="it_IT.UTF-8">it_IT.UTF-8 (Italian)</option>
      <option value="pt_PT.UTF-8">pt_PT.UTF-8 (Portuguese)</option>
      <option value="pt_BR.UTF-8">pt_BR.UTF-8 (Brazilian Portuguese)</option>
      <option value="nl_NL.UTF-8">nl_NL.UTF-8 (Dutch)</option>
      <option value="pl_PL.UTF-8">pl_PL.UTF-8 (Polish)</option>
      <option value="ru_RU.UTF-8">ru_RU.UTF-8 (Russian)</option>
      <option value="sv_SE.UTF-8">sv_SE.UTF-8 (Swedish)</option>
      <option value="nb_NO.UTF-8">nb_NO.UTF-8 (Norwegian)</option>
      <option value="da_DK.UTF-8">da_DK.UTF-8 (Danish)</option>
      <option value="fi_FI.UTF-8">fi_FI.UTF-8 (Finnish)</option>
      <option value="zh_CN.UTF-8">zh_CN.UTF-8 (Chinese Simplified)</option>
      <option value="ja_JP.UTF-8">ja_JP.UTF-8 (Japanese)</option>
      <option value="ko_KR.UTF-8">ko_KR.UTF-8 (Korean)</option>
    </select>
  </label>
  <label>Keyboard layout:
    <select id="keymap">
      <option value="us">US English</option>
      <option value="gb" selected>UK English</option>
      <option value="de">German</option>
      <option value="fr">French</option>
      <option value="es">Spanish</option>
      <option value="it">Italian</option>
      <option value="pt">Portuguese</option>
      <option value="br">Brazilian Portuguese</option>
      <option value="nl">Dutch</option>
      <option value="pl">Polish</option>
      <option value="ru">Russian</option>
      <option value="se">Swedish</option>
      <option value="no">Norwegian</option>
      <option value="dk">Danish</option>
      <option value="fi">Finnish</option>
      <option value="be">Belgian</option>
      <option value="ch">Swiss</option>
    </select>
  </label>
  <button onclick="startInstall()">Install</button>
</div>

<div id="p-done" class="panel">
  <h2>Installation Complete</h2>
  <p>Remove the ISO and reboot.</p>
  <button onclick="doReboot()">Reboot</button>
</div>

<script>
const sel = {};  // chosen partitions carried through panels
function show(name) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('p-' + name).classList.add('active');
}
function showErr(msg) {
  const e = document.getElementById('err');
  e.textContent = msg; e.style.display = msg ? 'block' : 'none';
}
async function showAuto() {
  showErr('');
  const r = await fetch('/api/whole_disks'); const d = await r.json();
  const s = document.getElementById('wholedisk');
  s.innerHTML = '';
  if (!d.disks.length) { showErr('No disks found'); return; }
  d.disks.forEach(p => s.add(new Option(p.path + ' (' + p.size + ')', p.path)));
  document.getElementById('autodisk-uefi').textContent =
    d.uefi ? 'UEFI mode: will create 512M EFI + root partitions (GPT).'
           : 'BIOS mode: will create single root partition (MBR).';
  show('autodisk');
}
async function confirmAutopart() {
  showErr('');
  const disk = document.getElementById('wholedisk').value;
  if (!disk) return showErr('No disk selected');
  const btn = document.querySelector('#p-autodisk .danger');
  btn.disabled = true; btn.textContent = 'Partitioning…';
  const r = await fetch('/api/autopart', {method:'POST', body: JSON.stringify({disk})});
  const d = await r.json();
  btn.disabled = false; btn.textContent = 'Erase disk and partition';
  if (!d.ok) return showErr(d.error);
  sel.root_part = d.root_part;
  sel.efi_part = d.efi_part || '';
  show('configure');
}
async function showManual() {
  showErr('');
  await loadDisks();
  show('disk');
}
async function loadDisks() {
  const r = await fetch('/api/disks'); const d = await r.json();
  const root = document.getElementById('root'), efi = document.getElementById('efi');
  document.getElementById('disks').textContent =
    d.disks.map(p => p.path + ' (' + p.size + ')').join(', ') || 'none found';
  d.disks.forEach(p => {
    root.add(new Option(p.path + ' (' + p.size + ')', p.path));
    efi.add(new Option(p.path + ' (' + p.size + ')', p.path));
  });
}
async function checkPartitions() {
  showErr('');
  sel.root_part = document.getElementById('root').value;
  sel.efi_part = document.getElementById('efi').value;
  const r = await fetch('/api/partition', {method:'POST',
    body: JSON.stringify(sel)});
  const d = await r.json();
  if (!d.ok) return showErr(d.error);
  show('configure');
}
let _maxPct = 0;
async function startInstall() {
  showErr('');
  const pw1 = document.getElementById('pw1').value;
  if (pw1 !== document.getElementById('pw2').value) return showErr('Passwords do not match');
  const cfg = Object.assign({}, sel, {
    hostname: document.getElementById('hostname').value,
    username: document.getElementById('username').value,
    password: pw1,
    timezone: document.getElementById('timezone').value,
    locale: document.getElementById('locale').value,
    keymap: document.getElementById('keymap').value,
  });
  const r = await fetch('/api/install', {method:'POST', body: JSON.stringify(cfg)});
  const d = await r.json();
  if (!d.ok) return showErr(d.error);
  _maxPct = 0;
  show('install');
  poll();
}
async function poll() {
  const r = await fetch('/api/progress'); const s = await r.json();
  if (s.percent > _maxPct) _maxPct = s.percent;
  document.getElementById('fill').style.width = _maxPct + '%';
  document.getElementById('step').textContent = s.step + ' (' + _maxPct + '%)';
  if (s.error) { showErr(s.error); return; }
  if (s.done) { show('done'); return; }
  setTimeout(poll, 2000);
}
async function doReboot() { await fetch('/api/reboot', {method:'POST', body:'{}'}); }
</script>
</body>
</html>"""

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


def parse_lsblk_disks(json_str):
    """Parse `lsblk -J` output, return whole disks only (type==disk)."""
    data = json.loads(json_str)
    out = []
    for dev in data.get("blockdevices", []):
        if dev.get("type") == "disk":
            out.append({"path": "/dev/" + dev["name"], "size": dev.get("size", "")})
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
    "Setting hostname, timezone and locale",
    "Creating user account",
    "Installing bootloader",
    "Cleaning up",
]


def new_state():
    """Fresh shared install state dict."""
    return {"percent": 0, "step": "", "done": False, "error": None}


import os
import subprocess
import threading
import time

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

        # Step 5: hostname, timezone, locale, keymap
        set_state(step=INSTALL_STEPS[5], percent=step_percent(5, 20))
        configure_hostname(cfg["hostname"])
        set_state(percent=step_percent(5, 50))
        configure_timezone(cfg.get("timezone", "UTC"))
        configure_locale(cfg.get("locale", "en_GB.UTF-8"))
        configure_keymap(cfg.get("keymap", "us"), cfg["username"])
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
    matches = glob.glob("/run/archiso/cowspace/**/upperdir", recursive=True)
    matches = [m for m in matches if "/x86_64/" in m]
    if matches:
        run(["rsync", "-aAXH", matches[0] + "/", MNT + "/"])


def configure_system():
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


CONSOLE_KEYMAP = {"gb": "uk", "br": "br-abnt2"}

VALID_LAYOUTS = {
    "us", "gb", "de", "fr", "es", "it", "pt", "br",
    "nl", "pl", "ru", "se", "no", "dk", "fi", "be", "ch",
}

VALID_TIMEZONES = {
    "Europe/London", "Europe/Dublin", "Europe/Lisbon", "Europe/Paris",
    "Europe/Brussels", "Europe/Amsterdam", "Europe/Berlin", "Europe/Vienna",
    "Europe/Zurich", "Europe/Madrid", "Europe/Rome", "Europe/Warsaw",
    "Europe/Stockholm", "Europe/Oslo", "Europe/Copenhagen", "Europe/Helsinki",
    "Europe/Athens", "Europe/Bucharest", "Europe/Moscow", "Europe/Istanbul",
    "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
    "America/Toronto", "America/Vancouver", "America/Sao_Paulo", "America/Mexico_City",
    "America/Argentina/Buenos_Aires", "Asia/Dubai", "Asia/Kolkata", "Asia/Bangkok",
    "Asia/Singapore", "Asia/Shanghai", "Asia/Tokyo", "Asia/Seoul", "Asia/Jerusalem",
    "Africa/Johannesburg", "Africa/Cairo", "Australia/Sydney", "Pacific/Auckland", "UTC",
}

VALID_LOCALES = {
    "en_GB.UTF-8", "en_US.UTF-8", "de_DE.UTF-8", "fr_FR.UTF-8", "es_ES.UTF-8",
    "it_IT.UTF-8", "pt_PT.UTF-8", "pt_BR.UTF-8", "nl_NL.UTF-8", "pl_PL.UTF-8",
    "ru_RU.UTF-8", "sv_SE.UTF-8", "nb_NO.UTF-8", "da_DK.UTF-8", "fi_FI.UTF-8",
    "zh_CN.UTF-8", "ja_JP.UTF-8", "ko_KR.UTF-8",
}


def configure_timezone(timezone):
    chroot(f"ln -sf /usr/share/zoneinfo/{timezone} /etc/localtime")
    chroot("hwclock --systohc")


def configure_locale(locale):
    with open(MNT + "/etc/locale.gen", "a") as f:
        f.write(f"{locale} UTF-8\n")
    chroot("locale-gen")
    with open(MNT + "/etc/locale.conf", "w") as f:
        f.write(f"LANG={locale}\n")


def configure_keymap(layout, username):
    console_km = CONSOLE_KEYMAP.get(layout, layout)
    with open(MNT + "/etc/vconsole.conf", "w") as f:
        f.write(f"KEYMAP={console_km}\n")
    # Set xkb layout in the installed user's MangoWM config
    mango_cfg = MNT + f"/home/{username}/.config/mango/config.conf"
    chroot(f"sed -i 's/^xkb_rules_layout=.*/xkb_rules_layout={layout}/' {mango_cfg}")


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
    # Switch journald from volatile (live) to auto (installed)
    chroot("sed -i 's/volatile/auto/g' /etc/systemd/journald.conf.d/volatile-storage.conf 2>/dev/null || true")
    chroot("mv /etc/systemd/journald.conf.d/volatile-storage.conf /etc/systemd/journald.conf.d/auto-storage.conf 2>/dev/null || true")
    # Remove live-only services
    chroot("unlink /etc/systemd/system/multi-user.target.wants/pacman-init.service 2>/dev/null || true")
    chroot("rm -f /etc/systemd/system/pacman-init.service")
    chroot("rm -f /etc/systemd/system/default.target")
    chroot("rm -f /etc/systemd/system/etc-pacman.d-gnupg.mount")
    # Restore gparted visibility in the menu
    chroot("sed -i '/^Hidden=true/d' /usr/share/applications/gparted.desktop 2>/dev/null || true")
    chroot("sed -i 's/^%wheel ALL=(ALL:ALL) NOPASSWD: ALL/# %wheel ALL=(ALL:ALL) NOPASSWD: ALL/' /etc/sudoers")
    chroot("sed -i 's/^# %wheel ALL=(ALL:ALL) ALL$/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers")


# --- HTTP server ---


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj))

    def log_message(self, *a):
        pass  # silence default stderr logging

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._send(200, PAGE_HTML, "text/html")
        elif self.path == "/api/disks":
            res = subprocess.run(["lsblk", "-J", "-o", "NAME,SIZE,TYPE"],
                                 capture_output=True, text=True)
            self._json({"ok": True, "disks": parse_lsblk(res.stdout)})
        elif self.path == "/api/whole_disks":
            res = subprocess.run(["lsblk", "-J", "-o", "NAME,SIZE,TYPE"],
                                 capture_output=True, text=True)
            self._json({
                "ok": True,
                "disks": parse_lsblk_disks(res.stdout),
                "uefi": is_uefi(),
            })
        elif self.path == "/api/progress":
            with STATE_LOCK:
                self._json(dict(STATE))
        else:
            self._json({"ok": False, "error": "not found"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode() if length else "{}"
        try:
            body = json.loads(raw)
        except ValueError:
            return self._json({"ok": False, "error": "bad json"}, 400)

        if self.path == "/api/autopart":
            disk = body.get("disk", "")
            if not disk or not os.path.exists(disk):
                return self._json({"ok": False, "error": "disk not found"}, 400)
            res = subprocess.run(["lsblk", "-no", "TYPE", disk],
                                 capture_output=True, text=True)
            if res.stdout.strip().splitlines()[0] != "disk":
                return self._json({"ok": False, "error": f"{disk} is not a whole disk"}, 400)
            try:
                parts = do_autopart(disk)
                return self._json({"ok": True, **parts})
            except Exception as e:
                log("autopart ERROR: " + str(e))
                return self._json({"ok": False, "error": str(e)}, 500)

        elif self.path == "/api/partition":
            for key in ("root_part", "efi_part"):
                p = body.get(key)
                if p and not os.path.exists(p):
                    return self._json({"ok": False, "error": f"{p} not found"}, 400)
            if not body.get("root_part"):
                return self._json({"ok": False, "error": "root partition required"}, 400)
            self._json({"ok": True})

        elif self.path == "/api/install":
            err = validate_install_cfg(body)
            if err:
                return self._json({"ok": False, "error": err}, 400)
            with STATE_LOCK:
                STATE.update(new_state())
            threading.Thread(target=do_install, args=(body,), daemon=True).start()
            self._json({"ok": True})

        elif self.path == "/api/reboot":
            self._json({"ok": True})
            subprocess.Popen(["reboot"])
        else:
            self._json({"ok": False, "error": "not found"}, 404)


def validate_install_cfg(cfg):
    """Return error string if cfg invalid, else None."""
    if not cfg.get("root_part"):
        return "root partition required"
    if not validate_name(cfg.get("hostname", "")):
        return "invalid hostname"
    if not validate_name(cfg.get("username", "")):
        return "invalid username"
    if not cfg.get("password"):
        return "password required"
    if cfg.get("timezone", "UTC") not in VALID_TIMEZONES:
        return "invalid timezone"
    if cfg.get("locale", "en_GB.UTF-8") not in VALID_LOCALES:
        return "invalid locale"
    if cfg.get("keymap", "us") not in VALID_LAYOUTS:
        return "invalid keyboard layout"
    return None


def main():
    open(LOG_PATH, "w").close()
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"FruitBang installer running at http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
