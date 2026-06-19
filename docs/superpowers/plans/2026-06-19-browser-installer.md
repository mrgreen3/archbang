# FruitBang Browser Installer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `abinstall`'s role with a browser-based FruitBang installer — a Python stdlib HTTP server serving a single-page HTML wizard, launched via `fb-install` from a terminal.

**Architecture:** Single self-contained `fb-installer.py` (Python stdlib only: `http.server`, `subprocess`, `threading`, `json`, `re`). Pure logic (validation, parsing) lives in importable module-level functions so they can be unit-tested on the host. Destructive disk operations run in a background install thread and are verified manually in QEMU. A bash launcher `fb-install` starts the server and opens Firefox.

**Tech Stack:** Python 3 stdlib, bash, HTML/CSS/vanilla JS (inline strings), rsync, arch-chroot, grub. Tests: pytest (host-side, pure functions only).

---

## File Structure

| File | Responsibility |
|------|----------------|
| `airootfs/usr/local/bin/fb-installer.py` | Server, routes, install thread, embedded HTML/CSS/JS, pure helper functions |
| `airootfs/etc/skel/Scripts/fb-install` | Bash launcher: start server, open Firefox |
| `tests/test_fb_installer.py` | Host-side pytest for pure functions (validation, parsing) |

Pure functions exposed for testing (no side effects):
- `validate_name(s)` → bool — hostname/username regex check
- `parse_lsblk(json_str)` → list[dict] — block device parse
- `parse_rsync_progress(line)` → int | None — percent from rsync `--info=progress2` line
- `step_percent(step_index, sub_pct)` → int — weighted overall percent

The server, threading, and subprocess calls are NOT unit-tested — verified in QEMU.

**Note on environment:** Edit and commit these files locally. Building the ISO and QEMU testing happens on the Alpine build VM per project workflow. The pytest steps run on the host (local) — install pytest first.

---

## Task 1: Project test scaffold

**Files:**
- Create: `tests/test_fb_installer.py`
- Create: `airootfs/usr/local/bin/fb-installer.py` (stub)

- [ ] **Step 1: Install pytest on host**

Run: `pip install --user pytest` (or `pacman -S python-pytest` if preferred)
Expected: pytest available on PATH.

- [ ] **Step 2: Create installer stub so the test file can import it**

Create `airootfs/usr/local/bin/fb-installer.py`:

```python
#!/usr/bin/env python3
"""FruitBang browser installer — Python stdlib HTTP server + HTML wizard."""

import json
import re

# --- Pure helpers (unit-tested) ---

# Step weights must sum to 100. Index aligns with INSTALL_STEPS order.
STEP_WEIGHTS = [2, 3, 60, 5, 8, 2, 5, 10, 5]

NAME_RE = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")
```

- [ ] **Step 3: Write a failing import test**

Create `tests/test_fb_installer.py`:

```python
import importlib.util
import pathlib

SPEC_PATH = pathlib.Path(__file__).parent.parent / "airootfs/usr/local/bin/fb-installer.py"


def load_mod():
    spec = importlib.util.spec_from_file_location("fb_installer", SPEC_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_step_weights_sum_to_100():
    mod = load_mod()
    assert sum(mod.STEP_WEIGHTS) == 100
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/Projects/fruitbang && python -m pytest tests/test_fb_installer.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
cd ~/Projects/fruitbang
git add tests/test_fb_installer.py airootfs/usr/local/bin/fb-installer.py
git commit -m "Add fb-installer test scaffold and stub"
```

---

## Task 2: Name validation

**Files:**
- Modify: `airootfs/usr/local/bin/fb-installer.py`
- Test: `tests/test_fb_installer.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_fb_installer.py`:

```python
def test_validate_name_accepts_simple():
    mod = load_mod()
    assert mod.validate_name("kev") is True
    assert mod.validate_name("fruit_bang") is True
    assert mod.validate_name("test-host") is True


def test_validate_name_rejects_bad():
    mod = load_mod()
    assert mod.validate_name("") is False
    assert mod.validate_name("1host") is False        # starts with digit
    assert mod.validate_name("Has Space") is False
    assert mod.validate_name("UPPER") is False
    assert mod.validate_name("inject;rm") is False
    assert mod.validate_name("a" * 33) is False        # too long
```

- [ ] **Step 2: Run to verify failure**

Run: `cd ~/Projects/fruitbang && python -m pytest tests/test_fb_installer.py -k validate_name -v`
Expected: FAIL — `AttributeError: module has no attribute 'validate_name'`.

- [ ] **Step 3: Implement**

Add to `fb-installer.py` under the helpers section:

```python
def validate_name(s):
    """True if s is a safe hostname/username (lowercase, no shell metachars)."""
    return bool(NAME_RE.match(s))
```

- [ ] **Step 4: Run to verify pass**

Run: `cd ~/Projects/fruitbang && python -m pytest tests/test_fb_installer.py -k validate_name -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
cd ~/Projects/fruitbang
git add tests/test_fb_installer.py airootfs/usr/local/bin/fb-installer.py
git commit -m "Add name validation for hostname/username"
```

---

## Task 3: lsblk parsing

**Files:**
- Modify: `airootfs/usr/local/bin/fb-installer.py`
- Test: `tests/test_fb_installer.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_fb_installer.py`:

```python
LSBLK_SAMPLE = '''{
  "blockdevices": [
    {"name":"sda","size":"20G","type":"disk","children":[
      {"name":"sda1","size":"512M","type":"part"},
      {"name":"sda2","size":"19.5G","type":"part"}
    ]}
  ]
}'''


def test_parse_lsblk_returns_partitions():
    mod = load_mod()
    parts = mod.parse_lsblk(LSBLK_SAMPLE)
    paths = [p["path"] for p in parts]
    assert "/dev/sda1" in paths
    assert "/dev/sda2" in paths
    # disks themselves excluded — only partitions selectable
    assert "/dev/sda" not in paths


def test_parse_lsblk_includes_size():
    mod = load_mod()
    parts = mod.parse_lsblk(LSBLK_SAMPLE)
    sda1 = next(p for p in parts if p["path"] == "/dev/sda1")
    assert sda1["size"] == "512M"
```

- [ ] **Step 2: Run to verify failure**

Run: `cd ~/Projects/fruitbang && python -m pytest tests/test_fb_installer.py -k lsblk -v`
Expected: FAIL — no attribute `parse_lsblk`.

- [ ] **Step 3: Implement**

Add to `fb-installer.py`:

```python
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
```

- [ ] **Step 4: Run to verify pass**

Run: `cd ~/Projects/fruitbang && python -m pytest tests/test_fb_installer.py -k lsblk -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
cd ~/Projects/fruitbang
git add tests/test_fb_installer.py airootfs/usr/local/bin/fb-installer.py
git commit -m "Add lsblk JSON parsing for partition list"
```

---

## Task 4: rsync progress parsing + weighted percent

**Files:**
- Modify: `airootfs/usr/local/bin/fb-installer.py`
- Test: `tests/test_fb_installer.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_fb_installer.py`:

```python
def test_parse_rsync_progress_extracts_percent():
    mod = load_mod()
    # rsync --info=progress2 line format
    line = "    1,234,567  45%   12.3MB/s    0:00:10"
    assert mod.parse_rsync_progress(line) == 45


def test_parse_rsync_progress_none_when_absent():
    mod = load_mod()
    assert mod.parse_rsync_progress("sending incremental file list") is None


def test_step_percent_weights():
    mod = load_mod()
    # before step 0 starts, sub_pct 0 -> 0
    assert mod.step_percent(0, 0) == 0
    # step index 2 (copy) at 50% sub -> prior weights (2+3=5) + 0.5*60 = 35
    assert mod.step_percent(2, 50) == 35
    # final step fully done -> 100
    assert mod.step_percent(8, 100) == 100
```

- [ ] **Step 2: Run to verify failure**

Run: `cd ~/Projects/fruitbang && python -m pytest tests/test_fb_installer.py -k "rsync or step_percent" -v`
Expected: FAIL — attributes missing.

- [ ] **Step 3: Implement**

Add to `fb-installer.py`:

```python
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
```

- [ ] **Step 4: Run to verify pass**

Run: `cd ~/Projects/fruitbang && python -m pytest tests/test_fb_installer.py -k "rsync or step_percent" -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
cd ~/Projects/fruitbang
git add tests/test_fb_installer.py airootfs/usr/local/bin/fb-installer.py
git commit -m "Add rsync progress and weighted step percent helpers"
```

---

## Task 5: Install state model + step definitions

**Files:**
- Modify: `airootfs/usr/local/bin/fb-installer.py`
- Test: `tests/test_fb_installer.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_fb_installer.py`:

```python
def test_initial_state_shape():
    mod = load_mod()
    st = mod.new_state()
    assert st["percent"] == 0
    assert st["done"] is False
    assert st["error"] is None
    assert st["step"] == ""


def test_install_steps_match_weights():
    mod = load_mod()
    # one label per weight
    assert len(mod.INSTALL_STEPS) == len(mod.STEP_WEIGHTS)
```

- [ ] **Step 2: Run to verify failure**

Run: `cd ~/Projects/fruitbang && python -m pytest tests/test_fb_installer.py -k "state or install_steps" -v`
Expected: FAIL — missing `new_state` / `INSTALL_STEPS`.

- [ ] **Step 3: Implement**

Add to `fb-installer.py`:

```python
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
```

- [ ] **Step 4: Run to verify pass**

Run: `cd ~/Projects/fruitbang && python -m pytest tests/test_fb_installer.py -k "state or install_steps" -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
cd ~/Projects/fruitbang
git add tests/test_fb_installer.py airootfs/usr/local/bin/fb-installer.py
git commit -m "Add install state model and step labels"
```

---

## Task 6: Install thread (destructive ops — no unit test)

**Files:**
- Modify: `airootfs/usr/local/bin/fb-installer.py`

This task wires the real disk operations, adapted from the existing `abinstall` logic. Verified in QEMU (Task 10), not by pytest.

- [ ] **Step 1: Add subprocess helpers and the install worker**

Add to `fb-installer.py` (after the pure helpers):

```python
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
```

- [ ] **Step 2: Add the per-step implementation functions**

Add to `fb-installer.py`. These adapt the proven logic from `airootfs/etc/skel/Scripts/abinstall`:

```python
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
    # fstab
    res = subprocess.run(["genfstab", "-U", MNT], capture_output=True, text=True)
    with open(MNT + "/etc/fstab", "a") as f:
        f.write(res.stdout)
    # standard (non-archiso) mkinitcpio preset
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
    # set password on live account via chpasswd stdin (never on cmdline)
    subprocess.run(
        ["arch-chroot", MNT, "chpasswd"],
        input=f"{live}:{password}\n", text=True, check=True,
    )
    # rename live -> username inside config files and account DBs
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
        # BIOS: install to parent disk of root partition
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
    # require password on installed system
    chroot("sed -i 's/^%wheel ALL=(ALL:ALL) NOPASSWD: ALL/# %wheel ALL=(ALL:ALL) NOPASSWD: ALL/' /etc/sudoers")
    chroot("sed -i 's/^# %wheel ALL=(ALL:ALL) ALL$/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers")
```

- [ ] **Step 3: Run host tests to confirm no import breakage**

Run: `cd ~/Projects/fruitbang && python -m pytest tests/test_fb_installer.py -v`
Expected: PASS (all prior tests still pass — module imports cleanly).

- [ ] **Step 4: Commit**

```bash
cd ~/Projects/fruitbang
git add airootfs/usr/local/bin/fb-installer.py
git commit -m "Add install thread and per-step disk operations"
```

---

## Task 7: HTTP server + routes

**Files:**
- Modify: `airootfs/usr/local/bin/fb-installer.py`

- [ ] **Step 1: Add the request handler and routes**

Add to `fb-installer.py`:

```python
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 7777


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

        if self.path == "/api/partition":
            # Validate selected partitions exist as block devices.
            import os
            for key in ("root_part", "efi_part"):
                p = body.get(key)
                if p and not os.path.exists(p):
                    return self._json({"ok": False, "error": f"{p} not found"}, 400)
            if not body.get("root_part"):
                return self._json({"ok": False, "error": "root partition required"}, 400)
            self._json({"ok": True})

        elif self.path == "/api/install":
            # Reset state and validate inputs before launching thread.
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
```

- [ ] **Step 2: Add a validate_install_cfg test**

Add to `tests/test_fb_installer.py`:

```python
def test_validate_install_cfg():
    mod = load_mod()
    ok = {"root_part": "/dev/sda2", "hostname": "fruit",
          "username": "kev", "password": "x"}
    assert mod.validate_install_cfg(ok) is None
    assert mod.validate_install_cfg({**ok, "hostname": "Bad Host"})
    assert mod.validate_install_cfg({**ok, "username": "1bad"})
    assert mod.validate_install_cfg({**ok, "password": ""})
    assert mod.validate_install_cfg({**ok, "root_part": ""})
```

- [ ] **Step 3: Add a PAGE_HTML placeholder so the module imports**

Add near the top of `fb-installer.py` (real HTML lands in Task 8):

```python
PAGE_HTML = "<!doctype html><title>FruitBang Installer</title>"
```

- [ ] **Step 4: Run tests**

Run: `cd ~/Projects/fruitbang && python -m pytest tests/test_fb_installer.py -v`
Expected: PASS (all pass, including new `validate_install_cfg`).

- [ ] **Step 5: Smoke-test the server starts (host, non-destructive)**

Run: `cd ~/Projects/fruitbang && timeout 2 python airootfs/usr/local/bin/fb-installer.py; echo "exit $?"`
Expected: prints "FruitBang installer running at http://localhost:7777", then exits on timeout (exit 124). No traceback.

- [ ] **Step 6: Commit**

```bash
cd ~/Projects/fruitbang
git add tests/test_fb_installer.py airootfs/usr/local/bin/fb-installer.py
git commit -m "Add HTTP server, routes, and config validation"
```

---

## Task 8: Embedded HTML wizard

**Files:**
- Modify: `airootfs/usr/local/bin/fb-installer.py`

- [ ] **Step 1: Replace the PAGE_HTML placeholder with the full wizard**

Replace the `PAGE_HTML = ...` line in `fb-installer.py` with:

```python
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
           padding:10px 18px; font-family:monospace; font-size:1em; cursor:pointer; }
  button:disabled { opacity:0.4; cursor:default; }
  label { display:block; margin:8px 0; }
  input[type=text], input[type=password] {
    background:#2c261d; color:#c9c0b0; border:1px solid #c9b890;
    border-radius:6px; padding:6px; font-family:monospace; width:100%; box-sizing:border-box; }
  .warn { color:#e0a060; border:1px solid #e0a060; border-radius:6px; padding:10px; }
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
  <div class="warn"><b>Warning:</b> Installing will erase data on the target partition.
  Back up anything important first.</div>
  <p>Requirements: booted from FruitBang live ISO, 20GB+ target disk.</p>
  <button onclick="show('disk')">Begin</button>
</div>

<div id="p-disk" class="panel">
  <h2>Select Partitions</h2>
  <p>Choose the root partition (and EFI partition if UEFI).</p>
  <div id="disks">Loading...</div>
  <label>Root partition: <select id="root"></select></label>
  <label>EFI partition (UEFI only, else leave blank):
    <select id="efi"><option value="">none</option></select></label>
  <button onclick="show('part')">Continue</button>
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
  <button onclick="startInstall()">Install</button>
</div>

<div id="p-done" class="panel">
  <h2>Installation Complete</h2>
  <p>Remove the ISO and reboot.</p>
  <button onclick="doReboot()">Reboot</button>
</div>

<script>
const sel = {};  // chosen partitions carried from disk panel
function show(name) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('p-' + name).classList.add('active');
}
function showErr(msg) {
  const e = document.getElementById('err');
  e.textContent = msg; e.style.display = msg ? 'block' : 'none';
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
async function startInstall() {
  showErr('');
  const pw1 = document.getElementById('pw1').value;
  if (pw1 !== document.getElementById('pw2').value) return showErr('Passwords do not match');
  const cfg = Object.assign({}, sel, {
    hostname: document.getElementById('hostname').value,
    username: document.getElementById('username').value,
    password: pw1,
  });
  const r = await fetch('/api/install', {method:'POST', body: JSON.stringify(cfg)});
  const d = await r.json();
  if (!d.ok) return showErr(d.error);
  show('install');
  poll();
}
async function poll() {
  const r = await fetch('/api/progress'); const s = await r.json();
  document.getElementById('fill').style.width = s.percent + '%';
  document.getElementById('step').textContent = s.step + ' (' + s.percent + '%)';
  if (s.error) { showErr(s.error); return; }
  if (s.done) { show('done'); return; }
  setTimeout(poll, 2000);
}
async function doReboot() { await fetch('/api/reboot', {method:'POST', body:'{}'}); }
loadDisks();
</script>
</body>
</html>"""
```

- [ ] **Step 2: Run host tests (import must still succeed)**

Run: `cd ~/Projects/fruitbang && python -m pytest tests/test_fb_installer.py -v`
Expected: PASS (all).

- [ ] **Step 3: Smoke-test page serves**

Run:
```bash
cd ~/Projects/fruitbang
python airootfs/usr/local/bin/fb-installer.py & SRV=$!
sleep 1
curl -s http://localhost:7777/ | grep -c "FruitBang Installer"
kill $SRV
```
Expected: prints a count ≥ 1 (HTML served).

- [ ] **Step 4: Commit**

```bash
cd ~/Projects/fruitbang
git add airootfs/usr/local/bin/fb-installer.py
git commit -m "Add embedded HTML installer wizard"
```

---

## Task 9: Bash launcher + permissions

**Files:**
- Create: `airootfs/etc/skel/Scripts/fb-install`

- [ ] **Step 1: Create the launcher**

Create `airootfs/etc/skel/Scripts/fb-install`:

```bash
#!/bin/bash
# Launch the FruitBang browser installer.
set -e

PORT=7777
SCRIPT=/usr/local/bin/fb-installer.py

if ! command -v firefox >/dev/null 2>&1; then
  echo "Firefox not found." >&2
  exit 1
fi

echo "Starting FruitBang installer..."
sudo python3 "$SCRIPT" &
SRV=$!

# Wait for the port to accept connections (max ~10s)
for i in $(seq 1 20); do
  if curl -s "http://localhost:${PORT}/" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

firefox "http://localhost:${PORT}"

# When Firefox closes, stop the server.
sudo kill "$SRV" 2>/dev/null || true
```

- [ ] **Step 2: Make launcher and installer executable**

Run:
```bash
cd ~/Projects/fruitbang
chmod 0755 airootfs/etc/skel/Scripts/fb-install
chmod 0755 airootfs/usr/local/bin/fb-installer.py
ls -l airootfs/etc/skel/Scripts/fb-install airootfs/usr/local/bin/fb-installer.py
```
Expected: both show `-rwxr-xr-x`.

- [ ] **Step 3: Verify profiledef.sh sets file permissions for the new files**

Run: `grep -n "file_permissions" -A 20 ~/Projects/fruitbang/profiledef.sh`
Expected: see the `file_permissions` array. If `/usr/local/bin/fb-installer.py` and `/etc/skel/Scripts/fb-install` are not listed with `0:0:755` (and Scripts dir is handled), add them. Example lines to add inside the array:

```bash
  ["/usr/local/bin/fb-installer.py"]="0:0:755"
  ["/etc/skel/Scripts/fb-install"]="0:0:755"
```

(Existing `abinstall` entry shows the established pattern — match it.)

- [ ] **Step 4: Commit**

```bash
cd ~/Projects/fruitbang
git add airootfs/etc/skel/Scripts/fb-install profiledef.sh
git commit -m "Add fb-install launcher and file permissions"
```

---

## Task 10: QEMU integration test (manual, on build VM)

**Files:** none — verification only.

This is the real test of the destructive paths. Per project workflow: push from local, pull and build on the Alpine VM. **Do not run QEMU automatically** — the user runs it manually (see project memory).

- [ ] **Step 1: Push to remote**

```bash
cd ~/Projects/fruitbang && git push
```

- [ ] **Step 2: On the build VM — pull and build**

```bash
cd ~/greenbang 2>/dev/null || cd ~/fruitbang
git pull
# run the archiso build (mkarchiso) as per project build process
```

- [ ] **Step 3: User boots the ISO in QEMU (BIOS mode) and verifies:**

- [ ] `fb-install` in foot opens Firefox to the wizard
- [ ] Welcome → Disk Select shows real partitions from `/api/disks`
- [ ] Partition Notice: `cfdisk` in a second terminal works, Continue validates
- [ ] Configure: hostname/username/password form accepts input, rejects mismatched passwords
- [ ] Install: progress bar advances, copy step shows real rsync percent
- [ ] Completes without error; installed system boots; user can log in with chosen credentials and password is required for sudo

- [ ] **Step 4: Repeat in UEFI mode**

Boot QEMU with OVMF firmware; confirm EFI partition mount + `grub-install --target=x86_64-efi` path works and the installed system boots.

- [ ] **Step 5: Record result**

If pass: note in project memory that the browser installer is verified. If fail: capture `/tmp/fb-install.log` from the live session, file the failing step, and iterate.

---

## Done Criteria

- All host pytest tests pass (`python -m pytest tests/ -v`)
- `fb-installer.py` and `fb-install` are executable and shipped via `profiledef.sh`
- `abinstall` retained, unchanged
- No new packages added to `packages.x86_64`
- Full wizard verified end-to-end in QEMU (BIOS and UEFI), installed system boots
