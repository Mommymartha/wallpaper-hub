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

import logging
import time

from . import config
from . import updater


def _configure_logging() -> None:
    config.ensure_cache_dir()
    logging.basicConfig(
        filename=config.LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def main() -> None:
    _configure_logging()
    logger = logging.getLogger("wallpaper_agent")
    logger.info("Wallpaper Fleet Agent starting. Poll interval: %ss",
                config.POLL_INTERVAL_SECONDS)

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
