"""
client/main_agent.py

Entrypoint for the background Client Agent.

Design goals:
    - Runs forever, polling every POLL_INTERVAL_SECONDS.
    - NEVER crashes or shows a console error to the user, even if:
        * the network is down
        * DNS resolution fails
        * GitHub returns a 5xx / rate-limits us
        * config.json is temporarily malformed
        * the Win32 call itself fails
    - Errors are logged to a local file (for troubleshooting) but never
      raised to the user or written to stdout/stderr, since this process
      is intended to run completely hidden (see the .vbs wrapper / Task
      Scheduler setup instructions).
"""

from __future__ import annotations

import os
import sys
import time
import winreg
import logging
import tkinter as tk
from tkinter import messagebox

from . import config
from . import updater


def _configure_logging() -> None:
    config.ensure_cache_dir()
    logging.basicConfig(
        filename=config.LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def add_to_startup(logger: logging.Logger) -> None:
    """Silently adds this executable to the Windows Startup folder via a VBScript wrapper."""
    if getattr(sys, 'frozen', False):
        app_path = sys.executable
    else:
        app_path = os.path.abspath(__file__)

    # Find the current user's Windows Startup folder
    startup_dir = os.path.join(
        os.environ["APPDATA"], 
        r"Microsoft\Windows\Start Menu\Programs\Startup"
    )
    
    # We create a .vbs file instead of a .bat file so it launches 100% invisibly
    vbs_path = os.path.join(startup_dir, "WallpaperFleetAgent.vbs")

    try:
        with open(vbs_path, "w") as f:
            f.write('Set WshShell = CreateObject("WScript.Shell")\n')
            f.write(f'WshShell.Run chr(34) & "{app_path}" & chr(34), 0\n')
            f.write('Set WshShell = Nothing\n')
        
        logger.info("Successfully created startup VBScript in %s", startup_dir)
    except Exception as exc:
        logger.warning("Failed to create startup script: %s", exc)

def main() -> None:
    _configure_logging()
    logger = logging.getLogger("wallpaper_agent")
    logger.info("Wallpaper Fleet Agent starting. Poll interval: %ss",
                config.POLL_INTERVAL_SECONDS)

    # 1. Embed into Windows startup immediately
    add_to_startup(logger)

    # 2. Show a quick confirmation popup to the user
    root = tk.Tk()
    root.withdraw()  # Hides the ugly default empty window
    root.attributes("-topmost", True)  # Forces popup to appear on top of other apps
    messagebox.showinfo(
        "Agent Active", 
        "Wallpaper Fleet Agent is now running in the background!\n\nIt will automatically launch whenever you turn on your PC."
    )
    root.destroy()   # Cleans up the tk instance so it doesn't linger

    # 3. Start the normal agent loop
    while True:
        try:
            updater.run_update_check()
        except Exception as exc:  # noqa: BLE001 - intentional catch-all
            # This is the resilience requirement: ANY failure during a
            # polling cycle (network down, bad JSON, Win32 failure, etc.)
            # is logged locally and swallowed. The agent must never crash
            # and never surface an error to the user. It simply waits for
            # the next cycle and tries again.
            logger.warning("Update check failed (will retry next cycle): %s", exc)

        time.sleep(config.POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()