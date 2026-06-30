"""Hardware info collector for the installer.

This is a minimal port of the beerfetch sysinfo logic adapted for the
ArchBang installer palette. It uses only the Python standard library.
"""

import json
import os
import shlex
import subprocess


def _run(cmd):
    """Run a command and return stdout, ignoring non-zero exits."""
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout


def _is_uefi():
    return os.path.isdir("/sys/firmware/efi")


def _parse_cpu(lscpu_json):
    fields = {}

    def walk(node):
        f = node.get("field", "").rstrip(":")
        if f:
            fields[f] = node.get("data", "")
        for child in node.get("children", []):
            walk(child)

    try:
        for node in json.loads(lscpu_json).get("lscpu", []):
            walk(node)
    except (ValueError, AttributeError):
        pass

    return {
        "model": fields.get("Model name", "unknown"),
        "logical": fields.get("CPU(s)", ""),
        "arch": fields.get("Architecture", ""),
    }


def _parse_mem(meminfo):
    for line in meminfo.splitlines():
        if line.startswith("MemTotal:"):
            try:
                return f"{int(line.split()[1]) / (1024 * 1024):.1f}G"
            except (IndexError, ValueError):
                pass
    return ""


def _parse_disks(lsblk_json):
    disks = []
    try:
        for dev in json.loads(lsblk_json).get("blockdevices", []):
            if dev.get("type") == "disk":
                disks.append({
                    "path": "/dev/" + dev["name"],
                    "size": dev.get("size", ""),
                    "model": (dev.get("model") or "").strip(),
                })
    except (ValueError, AttributeError):
        pass
    return disks


def _parse_lspci(lspci_mm):
    gpus = []
    wifi = None
    for line in lspci_mm.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parts = shlex.split(line)
        except ValueError:
            continue
        if len(parts) < 4:
            continue
        cls, vendor, device = parts[1], parts[2], parts[3]
        label = f"{vendor} {device}".strip()
        if any(k in cls for k in ("VGA", "3D", "Display")):
            gpus.append(label)
        elif "Network controller" in cls and wifi is None:
            wifi = label
    return {"gpu": gpus, "wifi": wifi}


def collect_hardware():
    """Return a dict with CPU, memory, disks, firmware, GPU, and Wi-Fi info."""
    lscpu = _run(["lscpu", "-J"])
    try:
        with open("/proc/meminfo") as f:
            meminfo = f.read()
    except OSError:
        meminfo = ""
    lsblk = _run(["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MODEL"])
    lspci = _run(["lspci", "-mm"])

    result = {
        "cpu": _parse_cpu(lscpu),
        "mem": {"total": _parse_mem(meminfo)},
        "disks": _parse_disks(lsblk),
        "firmware": "UEFI" if _is_uefi() else "BIOS",
    }
    result.update(_parse_lspci(lspci))
    return result
