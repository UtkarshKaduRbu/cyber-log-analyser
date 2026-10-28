"""
Email configuration (backend only).

1. SENDER credentials - edit the two constants below (or set the environment
   variables ALERT_SENDER_EMAIL / ALERT_APP_PASSWORD, which take priority).
   Use a Gmail *App Password* (16 characters), not your normal password.
   Never share or upload this file with real credentials filled in.

2. RECIPIENTS - managed from the dashboard (Alert Config) and saved permanently
   in data/recipients.json, so they are still there after a restart.
"""
import json
import os
import re

# ----------------------- EDIT THESE TWO LINES -----------------------
SENDER_EMAIL = "utkarshkadu6969@gmail.com"      # e.g. "your.soc.alerts@gmail.com"
APP_PASSWORD = "ENTER YOUR PASSKEY"      # e.g. "abcd efgh ijkl mnop"
# --------------------------------------------------------------------

RECIPIENTS_PATH = os.path.join("data", "recipients.json")
DEFAULT_RECIPIENTS = ["24kaduu@rbunagpur.in"]
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def get_sender():
    """Returns (sender_email, app_password); environment variables override the constants."""
    email = os.environ.get("ALERT_SENDER_EMAIL", SENDER_EMAIL).strip()
    password = os.environ.get("ALERT_APP_PASSWORD", APP_PASSWORD).replace(" ", "").strip()
    return email, password


def is_valid_email(addr):
    return bool(_EMAIL_RE.match((addr or "").strip()))


def load_recipients():
    """Saved recipient list; creates the file with the default on first run."""
    try:
        with open(RECIPIENTS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [e for e in data if isinstance(e, str) and is_valid_email(e)]
    except (OSError, json.JSONDecodeError):
        pass
    save_recipients(DEFAULT_RECIPIENTS)
    return list(DEFAULT_RECIPIENTS)


def save_recipients(recipients):
    os.makedirs(os.path.dirname(RECIPIENTS_PATH), exist_ok=True)
    with open(RECIPIENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(recipients, f, indent=2)


def add_recipient(addr):
    """Returns (ok, message). Rejects invalid and duplicate addresses."""
    addr = (addr or "").strip().lower()
    if not is_valid_email(addr):
        return False, "Enter a valid email address."
    current = load_recipients()
    if addr in [r.lower() for r in current]:
        return False, f"{addr} is already saved."
    save_recipients(current + [addr])
    return True, f"Saved {addr}."


def remove_recipient(addr):
    save_recipients([r for r in load_recipients() if r != addr])
