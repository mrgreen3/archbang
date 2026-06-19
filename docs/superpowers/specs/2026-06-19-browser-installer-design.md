# FruitBang Browser Installer — Design Spec

**Date:** 2026-06-19  
**Status:** Approved  
**Replaces:** `airootfs/etc/skel/Scripts/abinstall` (bash TUI)

---

## Overview

Replace the existing `abinstall` bash TUI installer with a browser-based wizard served by a Python stdlib HTTP server. User runs `fb-install` in a terminal; Python starts on `localhost:7777`; Firefox opens automatically. No added packages required — Python is already present on the Arch live ISO.

---

## Architecture

```
fb-install (bash launcher)
  └── sudo python3 /usr/local/bin/fb-installer.py
        ├── http.server on 127.0.0.1:7777
        ├── /                → single-page HTML wizard
        ├── /api/disks       → JSON list of block devices
        ├── /api/partition   → validates partitions exist after user runs cfdisk
        ├── /api/install     → starts install thread, returns job ID
        ├── /api/progress    → polls install progress (percent + step string)
        └── /api/configure   → applies hostname / user / bootloader post-install
```

**Launcher** (`/usr/local/bin/fb-install`, bash):
```bash
#!/bin/bash
sudo python3 /usr/local/bin/fb-installer.py &
sleep 1
firefox http://localhost:7777
```

State lives in a Python dict in memory. One install at a time. Install thread writes progress; poll endpoint reads it. Log written to `/tmp/fb-install.log`.

---

## Wizard Flow

Single HTML page, JS state machine. No page reloads. Panels shown/hidden by JS.

```
[Welcome] → [Disk Select] → [Partition Notice] → [Install] → [Configure] → [Done]
```

| Panel | Description |
|-------|-------------|
| **Welcome** | Data-loss warning, system requirements (live env, 20GB+ disk), Begin button |
| **Disk Select** | GET `/api/disks` → radio list of block devices with size. User picks root partition + EFI partition (UEFI only) |
| **Partition Notice** | Instructs user to open terminal, run `cfdisk /dev/sdX`. Continue button POSTs to `/api/partition` to validate partitions exist |
| **Install** | POST `/api/install`, progress bar polls `/api/progress` every 2s, last 3 log lines below bar |
| **Configure** | Form: hostname, username, password (×2 confirm). POST `/api/configure` |
| **Done** | "Remove ISO and reboot." Reboot button calls `sudo reboot` |

---

## Install Steps & Progress Weights

| # | Step | Weight |
|---|------|--------|
| 1 | Detect UEFI/BIOS, validate live env | 2% |
| 2 | Mount selected partitions | 3% |
| 3 | Copy airootfs → /mnt | 60% |
| 4 | Sync cowspace upperdir | 5% |
| 5 | Configure fstab, mkinitcpio, machine-id | 8% |
| 6 | Set hostname + /etc/hosts | 2% |
| 7 | Create user, set password | 5% |
| 8 | Install GRUB (UEFI or BIOS auto-detected) | 10% |
| 9 | Cleanup (remove live artifacts, fix sudoers) | 5% |

Step 3 uses `rsync --info=progress2` output parsed for bytes-transferred to give real sub-progress within the 60% band.

Poll response:
```json
{"percent": 42, "step": "Copying system files...", "done": false, "error": null}
```

On `done: true` → browser advances to Configure panel.

---

## Error Handling

- All `/api/*` endpoints return `{"ok": false, "error": "message"}` on failure
- Install thread catches exceptions, sets `state["error"]`; poll surfaces it
- Browser shows red error banner + Retry button (resets install state)
- Full log at `/tmp/fb-install.log` for terminal inspection

---

## Security

Server binds `127.0.0.1` only. Runs as root — mitigations:

- All disk/partition inputs validated against live block device list before use
- `subprocess` calls use list args — never `shell=True` with user-supplied data
- Hostname and username validated against `^[a-z_][a-z0-9_-]{0,31}$`
- Passwords passed via `chpasswd` stdin pipe — never on command line
- Server shuts down after reboot or on SIGINT

---

## Styling

Matches FruitBang palette:
- Background: `#201b14`
- Text: `#c9c0b0`
- Accent: `#c9b890`
- Border radius: 6px
- Font: system monospace

---

## Scope (MVP)

Covers: disk selection, partitioning handoff, system copy, hostname, user creation, GRUB.  
Out of scope for MVP: locale, timezone, mirrors, LVM, LUKS, keyboard layout (post-install via standard tools).

---

## Files Changed

| File | Action |
|------|--------|
| `airootfs/etc/skel/Scripts/abinstall` | Remove |
| `airootfs/usr/local/bin/fb-installer.py` | Add (Python server + HTML) |
| `airootfs/usr/local/bin/fb-install` | Add (bash launcher, executable) |
| `packages.x86_64` | No changes — Python stdlib only |

---

## Testing

Manual QEMU verification required before ship:
1. Boot ISO in QEMU (BIOS mode)
2. Run `fb-install` in foot terminal
3. Complete full wizard flow
4. Verify installed system boots
5. Repeat in UEFI mode
