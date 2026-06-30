import json
import os
import subprocess
import threading

from http.server import BaseHTTPRequestHandler

from .ui import PAGE_HTML
from .parse import parse_lsblk, parse_lsblk_disks, validate_install_cfg, validate_custom_layout
from .state import STATE, STATE_LOCK, INSTALL_RUNNING, new_state, log
from .system import do_autopart, do_custompart, do_install, is_uefi, is_live_medium
from .hwinfo import collect_hardware

# Requests must carry one of these Host headers. The server binds localhost only,
# but that alone doesn't stop another browser tab POSTing here: ui.py sends
# text/plain bodies, which skip CORS preflight, so cross-origin/DNS-rebind
# requests would otherwise reach the API. Port mirrors abi-installer.py PORT.
ALLOWED_HOSTS = frozenset({
    "127.0.0.1:7777",
    "localhost:7777",
    "archbang.install:7777",
})


def _part_type(path):
    """Return lsblk TYPE for path, or None if path is missing/not a blockdev."""
    res = subprocess.run(["lsblk", "-no", "TYPE", path],
                         capture_output=True, text=True)
    return res.stdout.strip().splitlines()[0] if res.returncode == 0 else None


def _validate_target_part(path, label):
    """Return error string if path is not a usable partition, else None."""
    if not path:
        return None
    if not os.path.exists(path):
        return f"{label} {path} not found"
    t = _part_type(path)
    if t != "part":
        return f"{label} {path} is not a partition"
    if is_live_medium(path):
        return f"{label} {path} is on the live install medium"
    return None


class Handler(BaseHTTPRequestHandler):
    """Minimal HTTP handler: serves the installer page and JSON API routes."""

    def _send(self, code, body, ctype="application/json"):
        """Send HTTP response with status code, body bytes or str, and content type."""
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, obj, code=200):
        """Serialise obj to JSON and send with optional status code."""
        self._send(code, json.dumps(obj))

    def _host_ok(self):
        """True if the request's Host header is an expected local value."""
        return self.headers.get("Host", "") in ALLOWED_HOSTS

    def log_message(self, *a):
        pass  # silence default stderr logging

    def do_GET(self):
        """Serve the installer page and read-only API endpoints."""
        if not self._host_ok():
            return self._json({"ok": False, "error": "forbidden host"}, 403)
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
        elif self.path == "/api/hardware":
            try:
                data = collect_hardware()
                self._json({"ok": True, "hardware": data})
            except Exception as exc:
                self._json({"ok": False, "error": str(exc)}, 500)
        elif self.path == "/api/progress":
            with STATE_LOCK:
                self._json(dict(STATE))
        else:
            self._json({"ok": False, "error": "not found"}, 404)

    def do_POST(self):
        """Handle write actions: autopart, partition validate, install, reboot."""
        if not self._host_ok():
            return self._json({"ok": False, "error": "forbidden host"}, 403)
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            return self._json({"ok": False, "error": "bad content-length"}, 400)
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
            types = res.stdout.strip().splitlines()
            if not types or types[0] != "disk":
                return self._json({"ok": False, "error": f"{disk} is not a whole disk"}, 400)
            if is_live_medium(disk):
                return self._json({"ok": False,
                                   "error": f"{disk} is the live install medium — refusing to erase"}, 400)
            try:
                parts = do_autopart(disk)
                return self._json({"ok": True, **parts})
            except Exception as e:
                log("autopart ERROR: " + str(e))
                return self._json({"ok": False, "error": str(e)}, 500)

        elif self.path == "/api/custompart":
            disk = body.get("disk", "")
            if not disk or not os.path.exists(disk):
                return self._json({"ok": False, "error": "disk not found"}, 400)
            res = subprocess.run(["lsblk", "-no", "TYPE", disk],
                                 capture_output=True, text=True)
            types = res.stdout.strip().splitlines()
            if not types or types[0] != "disk":
                return self._json({"ok": False, "error": f"{disk} is not a whole disk"}, 400)
            if is_live_medium(disk):
                return self._json({"ok": False,
                                   "error": f"{disk} is the live install medium — refusing to erase"}, 400)
            parts = body.get("parts", [])
            err = validate_custom_layout(parts, is_uefi())
            if err:
                return self._json({"ok": False, "error": err}, 400)
            try:
                result = do_custompart(disk, parts, is_uefi())
                return self._json({"ok": True, **result})
            except Exception as e:
                log("custompart ERROR: " + str(e))
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
            for key, label in (("root_part", "root"), ("efi_part", "EFI"),
                               ("swap_part", "swap"), ("home_part", "home")):
                err = _validate_target_part(body.get(key), label)
                if err:
                    return self._json({"ok": False, "error": err}, 400)
            with STATE_LOCK:
                if INSTALL_RUNNING.is_set():
                    return self._json({"ok": False, "error": "install already in progress"}, 409)
                INSTALL_RUNNING.set()
                STATE.update(new_state())
            threading.Thread(target=do_install, args=(body,), daemon=True).start()
            self._json({"ok": True})

        elif self.path == "/api/reboot":
            self._json({"ok": True})
            subprocess.Popen(["reboot"])
        else:
            self._json({"ok": False, "error": "not found"}, 404)
