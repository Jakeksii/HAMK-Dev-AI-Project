"""
Makes sure the user is logged in to Google before the Calendar MCP server starts.

The OAuth keys file is expected at the repo root: gcp-oauth.keys.json
If there is no saved login token (or it is about to expire), this runs
`npx -y @cocal/google-calendar-mcp auth`, which opens the browser once.

Manual use:
    python -m src.capabilities.google_auth          # log in only if needed
    python -m src.capabilities.google_auth --force  # always log in again
"""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# This file is src/capabilities/google_auth.py, so the repo root is two levels up.
REPO_ROOT = Path(__file__).resolve().parents[2]
KEYS_FILE = REPO_ROOT / "gcp-oauth.keys.json"
SERVER_PACKAGE = "@cocal/google-calendar-mcp"

# Apps in "Testing" status get refresh tokens that expire after 7 days,
# so we log in again a little before that.
MAX_LOGIN_AGE_SECONDS = 6 * 24 * 3600


class GoogleAuthError(Exception):
    """Raised when the Google login can't be done."""
    pass


def _token_path() -> Path:
    """Where the MCP server saves its login token (same rules the server uses)."""
    custom = os.environ.get("GOOGLE_CALENDAR_MCP_TOKEN_PATH")
    if custom:
        return Path(custom)
    config_home = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(config_home) / "google-calendar-mcp" / "tokens.json"


def _marker_path() -> Path:
    """Small file where we remember when the last login happened."""
    return _token_path().parent / "last-login.txt"


def _needs_login() -> bool:
    token = _token_path()
    marker = _marker_path()
    if not token.exists() or token.stat().st_size == 0:
        return True
    if not marker.exists():
        return True
    try:
        last_login = float(marker.read_text().strip())
    except ValueError:
        return True
    return time.time() - last_login > MAX_LOGIN_AGE_SECONDS


def _run_login() -> None:
    if not KEYS_FILE.exists():
        raise GoogleAuthError(
            f"OAuth keys file not found: {KEYS_FILE}. "
            "Put gcp-oauth.keys.json in the repo root."
        )

    # On Windows npx is npx.cmd, shutil.which finds the right one.
    npx = shutil.which("npx")
    if npx is None:
        raise GoogleAuthError("npx was not found. Install Node.js and try again.")

    env = os.environ.copy()
    env["GOOGLE_OAUTH_CREDENTIALS"] = str(KEYS_FILE)

    print("Google login needed. A browser window will open, log in and allow calendar access.")
    print('If Google says "Google hasn\'t verified this app", click Continue.')
    result = subprocess.run([npx, "-y", SERVER_PACKAGE, "auth"], env=env)
    if result.returncode != 0:
        raise GoogleAuthError(f"Google login failed (exit code {result.returncode}).")

    if not _token_path().exists():
        raise GoogleAuthError("Login finished but no token was saved. Try again.")

    _marker_path().parent.mkdir(parents=True, exist_ok=True)
    _marker_path().write_text(str(time.time()))
    print("Google login done.")


def ensure_logged_in(force: bool = False) -> None:
    """Logs the user in if there is no valid saved login. Does nothing otherwise."""
    if force or _needs_login():
        _run_login()


if __name__ == "__main__":
    try:
        ensure_logged_in(force="--force" in sys.argv)
        print("Logged in. Token:", _token_path())
    except GoogleAuthError as err:
        print("Error:", err)
        sys.exit(1)