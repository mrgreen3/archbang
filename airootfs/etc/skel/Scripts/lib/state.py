import threading

LOG_PATH = "/tmp/fb-install.log"
MNT = "/mnt"

# Step weights must sum to 100. Index aligns with INSTALL_STEPS order.
STEP_WEIGHTS = [2, 3, 60, 5, 8, 2, 5, 10, 5]

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

STATE_LOCK = threading.Lock()


def new_state():
    """Fresh shared install state dict."""
    return {"percent": 0, "step": "", "done": False, "error": None}


# Module-level shared state (single install at a time).
STATE = new_state()


def step_percent(step_index, sub_pct):
    """Overall percent given the current step index and its sub-progress (0-100)."""
    prior = sum(STEP_WEIGHTS[:step_index])
    current = STEP_WEIGHTS[step_index] * (sub_pct / 100.0)
    return int(prior + current)


def log(msg):
    """Append a line to the install log file."""
    with open(LOG_PATH, "a") as f:
        f.write(msg + "\n")


def set_state(**kw):
    """Thread-safe update of the shared install state dict."""
    with STATE_LOCK:
        STATE.update(kw)
