"""
client/updater.py

Core update logic:
    1. Fetch config.json from the raw GitHub URL.
    2. Compare its "version" field to the last version applied locally.
    3. If changed, download the referenced image and apply it via
       windows_api.set_wallpaper().
    4. Persist the new version locally so we don't re-download every cycle.

This module raises exceptions on failure (network errors, bad JSON, etc.).
It deliberately does NOT swallow errors itself — that responsibility
belongs to the polling loop in main_agent.py, which must keep running
no matter what. Keeping the try/except at the top level makes the
"fail silently and retry next cycle" behavior explicit and easy to audit.
"""

from __future__ import annotations

import logging
import os

import requests

from . import config
from . import windows_api

logger = logging.getLogger("wallpaper_agent")


def _read_local_version() -> int:
    """Return the last applied version, or -1 if none has been applied yet."""
    if not os.path.isfile(config.LOCAL_VERSION_FILE):
        return -1
    try:
        with open(config.LOCAL_VERSION_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except (ValueError, OSError):
        # Corrupted or unreadable version file - treat as "never applied"
        # so the agent re-syncs on the next successful cycle.
        return -1


def _write_local_version(version: int) -> None:
    with open(config.LOCAL_VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(str(version))


def _fetch_remote_config() -> dict:
    resp = requests.get(config.CONFIG_JSON_URL, timeout=config.HTTP_TIMEOUT_SECONDS)
    resp.raise_for_status()
    return resp.json()


def _download_image(remote_image_filename: str, destination_path: str) -> None:
    url = config.image_url(remote_image_filename)
    resp = requests.get(url, timeout=config.HTTP_TIMEOUT_SECONDS, stream=True)
    resp.raise_for_status()

    tmp_path = destination_path + ".tmp"
    with open(tmp_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    # Atomic-ish replace so a half-written file is never picked up.
    os.replace(tmp_path, destination_path)


def run_update_check() -> bool:
    """
    Perform a single check-and-apply cycle.

    Returns True if a new wallpaper was applied, False if already up to date.
    Raises on any network/parsing/OS error - caller is responsible for
    catching and continuing the polling loop.
    """
    config.ensure_cache_dir()

    remote_config = _fetch_remote_config()
    remote_version = int(remote_config["version"])
    remote_image_filename = remote_config.get(
        "image_file", config.DEFAULT_IMAGE_FILENAME
    )

    local_version = _read_local_version()

    if remote_version == local_version:
        logger.debug("Already up to date (version %s).", local_version)
        return False

    logger.info(
        "New version detected: %s -> %s. Downloading...",
        local_version,
        remote_version,
    )
    _download_image(remote_image_filename, config.LOCAL_IMAGE_PATH)

    windows_api.set_wallpaper(config.LOCAL_IMAGE_PATH)
    _write_local_version(remote_version)

    logger.info("Applied wallpaper version %s.", remote_version)
    return True
