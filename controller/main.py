"""
controller/main.py

CLI entrypoint for pushing a new wallpaper to the fleet.

Usage:
    python -m controller.main path/to/new_wallpaper.jpg
    python -m controller.main path/to/new_wallpaper.jpg --message "Q3 branding update"

Flow:
    1. Validate configuration (token, repo).
    2. Upload the image, overwriting wallpaper.jpg (fetching SHA first).
    3. Fetch config.json, bump its version, overwrite it (fetching SHA first).
    Client agents polling raw.githubusercontent.com will pick up the new
    version on their next 60-second cycle and re-download the image.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from . import config
from . import github_api


def bump_version(current: dict) -> dict:
    """
    Increment an integer version counter and stamp the update time.
    Starts at 1 if no version exists yet.
    """
    next_version = int(current.get("version", 0)) + 1
    return {
        "version": next_version,
        "image_file": config.WALLPAPER_PATH_IN_REPO,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def push_wallpaper(image_path: str, message: str) -> None:
    config.validate()

    print(f"[1/3] Uploading image: {image_path}")
    github_api.upload_image(image_path, commit_message=f"{message} (image)")
    print("      Done.")

    print("[2/3] Fetching current config.json ...")
    current_config, _ = github_api.get_file_json(config.CONFIG_JSON_PATH_IN_REPO)

    new_config = bump_version(current_config)
    print(f"      New version: {new_config['version']}")

    print("[3/3] Updating config.json ...")
    github_api.update_config_json(new_config, commit_message=f"{message} (v{new_config['version']})")
    print("      Done.")

    print(f"\nFleet update published. Clients will apply v{new_config['version']} "
          f"within 60 seconds of their next poll.")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Push a new wallpaper image to the fleet via GitHub."
    )
    parser.add_argument("image_path", help="Path to the local .jpg to distribute")
    parser.add_argument(
        "--message",
        default="Wallpaper update",
        help="Commit message prefix used for both the image and config.json commits",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    try:
        push_wallpaper(args.image_path, args.message)
    except EnvironmentError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print(f"Image not found: {args.image_path}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001 - CLI top-level, show the real error
        print(f"Failed to push update: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
