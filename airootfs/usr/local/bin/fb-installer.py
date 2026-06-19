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
