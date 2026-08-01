"""
client/windows_api.py

Thin wrapper around the Win32 API needed to change the desktop wallpaper
silently: SystemParametersInfoW with SPI_SETDESKWALLPAPER.

This module intentionally does nothing except talk to the OS — no
network calls, no polling logic — so it stays trivially testable and
reusable.
"""

import ctypes
import os

SPI_SETDESKWALLPAPER = 0x0014
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDCHANGE = 0x02


def set_wallpaper(image_path: str) -> bool:
    """
    Apply `image_path` as the current desktop wallpaper.

    Returns True on success, False if the Win32 call reports failure.
    Raises FileNotFoundError if the image does not exist locally, and
    OSError if called on a non-Windows platform (this module is
    Windows-only by design).
    """
    if not os.name == "nt":
        raise OSError("windows_api.set_wallpaper() can only run on Windows.")

    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Wallpaper image not found: {image_path}")

    # SystemParametersInfoW expects an absolute, normalized path.
    abs_path = os.path.abspath(image_path)

    result = ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER,
        0,
        abs_path,
        SPIF_UPDATEINIFILE | SPIF_SENDCHANGE,
    )

    # SystemParametersInfoW returns a nonzero value on success.
    return bool(result)
