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
