import json
import re

NAME_RE = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")
RSYNC_PCT_RE = re.compile(r"\s(\d{1,3})%")

# Allowlists mirror the <select> option values in lib/ui.py. Any value reaching
# validate_install_cfg flows into root arch-chroot shell strings (see lib/system.py),
# so only these known-safe strings are accepted. Keep in sync with ui.py dropdowns.
VALID_TIMEZONES = frozenset({
    "Europe/London", "Europe/Dublin", "Europe/Lisbon", "Europe/Paris",
    "Europe/Brussels", "Europe/Amsterdam", "Europe/Berlin", "Europe/Vienna",
    "Europe/Zurich", "Europe/Madrid", "Europe/Rome", "Europe/Warsaw",
    "Europe/Stockholm", "Europe/Oslo", "Europe/Copenhagen", "Europe/Helsinki",
    "Europe/Athens", "Europe/Bucharest", "Europe/Moscow", "Europe/Istanbul",
    "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
    "America/Toronto", "America/Montreal", "America/Vancouver", "America/Sao_Paulo", "America/Mexico_City",
    "America/Argentina/Buenos_Aires",
    "Asia/Dubai", "Asia/Kolkata", "Asia/Bangkok", "Asia/Singapore",
    "Asia/Shanghai", "Asia/Tokyo", "Asia/Seoul", "Asia/Jerusalem",
    "Africa/Johannesburg", "Africa/Cairo", "Australia/Sydney", "Pacific/Auckland",
    "UTC",
})
VALID_LOCALES = frozenset({
    "en_GB.UTF-8", "en_US.UTF-8", "de_DE.UTF-8", "fr_FR.UTF-8", "es_ES.UTF-8",
    "it_IT.UTF-8", "pt_PT.UTF-8", "pt_BR.UTF-8", "nl_NL.UTF-8", "pl_PL.UTF-8",
    "ru_RU.UTF-8", "sv_SE.UTF-8", "nb_NO.UTF-8", "da_DK.UTF-8", "fi_FI.UTF-8",
    "zh_CN.UTF-8", "ja_JP.UTF-8", "ko_KR.UTF-8",
})
VALID_KEYMAPS = frozenset({
    "us", "gb", "de", "fr", "es", "it", "pt", "br", "nl", "pl",
    "ru", "se", "no", "dk", "fi", "be", "ch",
})



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


PART_SIZE_RE = re.compile(r"^\d{1,6}(\.\d{1,2})?[MGT]$")
VALID_FS = frozenset({"ext4", "btrfs", "xfs"})
VALID_ROLES = frozenset({"efi", "root", "swap", "home"})


def _size_to_mib(size):
    """Convert a validated size string (e.g. '512M', '30G') to MiB as a float."""
    num, unit = float(size[:-1]), size[-1]
    return num * {"M": 1, "G": 1024, "T": 1024 * 1024}[unit]


def validate_custom_layout(parts, uefi):
    """Return an error string if the custom partition layout is invalid, else None.

    parts: ordered list of {"size": "30G" | "", "role": ..., "fs": ...}.
    Only the final entry may omit size, which means "use the remaining space".
    Every value here either feeds an sfdisk script (sizes, strictly regex-checked)
    or maps to a fixed argv (roles -> type codes, fs -> mkfs binary); no field
    reaches a shell. Keep the allowlists in sync with ui.py.
    """
    if not isinstance(parts, list) or not parts:
        return "no partitions defined"
    if len(parts) > 8:
        return "too many partitions (max 8)"

    roles = []
    for p in parts:
        if not isinstance(p, dict):
            return "malformed partition entry"
        role = p.get("role")
        if role not in VALID_ROLES:
            return f"invalid role: {role!r}"
        roles.append(role)

    if roles.count("root") != 1:
        return "exactly one root partition is required"
    if roles.count("swap") > 1:
        return "at most one swap partition"
    if roles.count("home") > 1:
        return "at most one home partition"

    if uefi:
        if roles.count("efi") != 1:
            return "UEFI requires exactly one EFI partition"
    else:
        if roles.count("efi") != 0:
            return "EFI partition is only used in UEFI mode"
        if len(parts) > 4:
            return "MBR supports at most 4 partitions"

    last = len(parts) - 1
    for i, p in enumerate(parts):
        size = (p.get("size") or "").strip()
        if size == "":
            if i != last:
                return "only the last partition may use remaining space"
        elif not PART_SIZE_RE.match(size):
            return f"invalid size: {p.get('size')!r} (use e.g. 512M, 30G)"

        if p["role"] in ("root", "home") and p.get("fs", "ext4") not in VALID_FS:
            return f"invalid filesystem: {p.get('fs')!r}"

        if p["role"] == "efi":
            if size == "":
                return "EFI partition needs an explicit size (e.g. 512M)"
            if _size_to_mib(size) < 256:
                return "EFI partition should be at least 256M"

    return None


def parse_rsync_progress(line):
    """Extract integer percent from an rsync --info=progress2 line, or None."""
    m = RSYNC_PCT_RE.search(line)
    if not m:
        return None
    pct = int(m.group(1))
    return pct if 0 <= pct <= 100 else None


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
    if cfg.get("timezone", "America/Montreal") not in VALID_TIMEZONES:
        return "invalid timezone"
    if cfg.get("locale", "en_US.UTF-8") not in VALID_LOCALES:
        return "invalid locale"
    if cfg.get("keymap", "us") not in VALID_KEYMAPS:
        return "invalid keymap"
    return None
