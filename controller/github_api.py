"""
controller/github_api.py

Thin wrapper around the GitHub Contents API.

GitHub's Contents API requires the current file's `sha` when overwriting
an existing file via PUT — otherwise the request is rejected with a 409/422.
This module always fetches the SHA first, then performs the update.
"""

from __future__ import annotations

import base64
import json
from typing import Optional, Tuple

import requests

from . import config


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_file_sha(path_in_repo: str) -> Optional[str]:
    """
    Return the current `sha` of a file in the repo, or None if the file
    does not exist yet (first-time upload).
    """
    url = config.contents_url(path_in_repo)
    resp = requests.get(
        url,
        headers=_headers(),
        params={"ref": config.GITHUB_BRANCH},
        timeout=15,
    )

    if resp.status_code == 404:
        return None

    resp.raise_for_status()
    return resp.json().get("sha")


def get_file_json(path_in_repo: str) -> Tuple[dict, Optional[str]]:
    """
    Fetch and decode a JSON file from the repo.
    Returns (parsed_json_dict, sha). If the file does not exist,
    returns ({}, None).
    """
    url = config.contents_url(path_in_repo)
    resp = requests.get(
        url,
        headers=_headers(),
        params={"ref": config.GITHUB_BRANCH},
        timeout=15,
    )

    if resp.status_code == 404:
        return {}, None

    resp.raise_for_status()
    payload = resp.json()
    decoded = base64.b64decode(payload["content"]).decode("utf-8")
    return json.loads(decoded), payload.get("sha")


def upload_file(
    path_in_repo: str,
    content_bytes: bytes,
    commit_message: str,
    sha: Optional[str] = None,
) -> dict:
    """
    Create or overwrite a file in the repo via PUT /repos/{owner}/{repo}/contents/{path}.

    If `sha` is provided, GitHub treats this as an update to an existing file.
    If `sha` is None, GitHub treats this as a brand-new file.
    """
    url = config.contents_url(path_in_repo)

    body = {
        "message": commit_message,
        "content": base64.b64encode(content_bytes).decode("utf-8"),
        "branch": config.GITHUB_BRANCH,
    }
    if sha:
        body["sha"] = sha

    resp = requests.put(url, headers=_headers(), data=json.dumps(body), timeout=30)
    resp.raise_for_status()
    return resp.json()


def upload_image(local_image_path: str, commit_message: str) -> dict:
    """
    Upload/overwrite the wallpaper image. Automatically fetches the
    existing SHA (if any) so the update does not get rejected.
    """
    with open(local_image_path, "rb") as f:
        content_bytes = f.read()

    existing_sha = get_file_sha(config.WALLPAPER_PATH_IN_REPO)
    return upload_file(
        config.WALLPAPER_PATH_IN_REPO,
        content_bytes,
        commit_message,
        sha=existing_sha,
    )


def update_config_json(new_config: dict, commit_message: str) -> dict:
    """
    Overwrite config.json with `new_config`. Automatically fetches the
    existing SHA so GitHub accepts the update.
    """
    existing_sha = get_file_sha(config.CONFIG_JSON_PATH_IN_REPO)
    content_bytes = json.dumps(new_config, indent=2).encode("utf-8")
    return upload_file(
        config.CONFIG_JSON_PATH_IN_REPO,
        content_bytes,
        commit_message,
        sha=existing_sha,
    )
