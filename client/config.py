"""
client/config.py

Configuration for the Client Agent. These values must match the
repository the Controller publishes to (see controller/config.py).

No secrets are needed here: the client only ever performs anonymous
GET requests against public raw.githubusercontent.com URLs.
"""

import os

# --- Must match the Controller's target repo --------------------------------
GITHUB_OWNER = "Mommymartha"
GITHUB_REPO = "wallpaper-hub"
GITHUB_BRANCH = "main"

CONFIG_JSON_FILENAME = "config.json"
DEFAULT_IMAGE_FILENAME = "wallpaper.jpg"

# --- Raw content base URL ----------------------------------------------------
RAW_BASE_URL = (
    f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/{GITHUB_BRANCH}"
)

CONFIG_JSON_URL = f"{RAW_BASE_URL}/{CONFIG_JSON_FILENAME}"


def image_url(image_filename: str) -> str:
    """Build the raw URL for whatever image file config.json currently points to."""
    return f"{RAW_BASE_URL}/{image_filename}"


# --- Polling behavior ---------------------------------------------------------
POLL_INTERVAL_SECONDS = 60
HTTP_TIMEOUT_SECONDS = 15

# --- Local cache (per-user, no admin rights required) --------------------------
_APPDATA = os.getenv("LOCALAPPDATA") or os.path.expanduser("~")
CACHE_DIR = os.path.join(_APPDATA, "WallpaperFleetManager")
LOCAL_IMAGE_PATH = os.path.join(CACHE_DIR, "current_wallpaper.jpg")
LOCAL_VERSION_FILE = os.path.join(CACHE_DIR, "version.txt")
LOG_FILE = os.path.join(CACHE_DIR, "agent.log")


def ensure_cache_dir() -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
