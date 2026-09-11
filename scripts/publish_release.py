#!/usr/bin/env python3
"""Publish the declared version from a main-branch push, without replacing tags."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from check_release_pr import (
    LATEST_VERSION_FILE, VERSION_FIELDS, precedence, reject_constant,
    release_log_path, unique_object, validate_release_log, version_from_documents,
)


REPOSITORY = "opus-pro/ai-producer-plugin"


def github_request(method: str, path: str, payload: dict | None = None) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "aip-release-workflow",
    }
    # Public tag lookups need no credentials. Only mutations use the job token.
    if method != "GET":
        headers["Authorization"] = f"Bearer {os.environ['GH_TOKEN']}"
    request = Request(
        f"https://api.github.com/repos/{REPOSITORY}/{path}",
        data=None if payload is None else json.dumps(payload).encode("utf-8"),
        method=method,
        headers=headers,
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        try:
            details = json.loads(error.read(8192))
            message = details.get("message") if isinstance(details, dict) else None
            if isinstance(message, str) and message.strip():
                token = os.environ.get("GH_TOKEN")
                if token:
                    message = message.replace(token, "[redacted]")
                error.msg = " ".join(message.split())[:1000]
        except (ValueError, UnicodeError):
            pass
        finally:
            error.close()
        raise


def tag_exists(api, tag: str) -> bool:
    try:
        api("GET", f"git/ref/tags/{quote(tag, safe='')}")
    except HTTPError as error:
        if error.code == 404:
            return False
        raise
    return True


def read_document(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o111:
        raise ValueError(f"Version file must be regular and non-executable: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object, parse_constant=reject_constant)


def publish_release(root: Path, sha: str, api=github_request) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Publication requires the triggering commit SHA")
    latest = root / LATEST_VERSION_FILE
    if not latest.exists() and not latest.is_symlink():
        return "SKIP: latest_version.json is absent"
    document = read_document(latest)
    if not isinstance(document, dict) or set(document) != {"version"} or not isinstance(document["version"], str):
        raise ValueError("latest_version.json must contain only a version string")
    version = document["version"]
    rank = precedence(version)
    tag = f"v{version}"
    log = root / release_log_path(version)
    if not log.exists() and not log.is_symlink():
        return f"SKIP: no release log for {tag}"
    if log.is_symlink() or not log.is_file() or log.stat().st_mode & 0o111:
        raise ValueError("Release log must be regular and non-executable")
    if tag_exists(api, tag):
        return f"SKIP: tag {tag} already exists; tag and release left unchanged"

    documents = {path: read_document(root / path) for path in VERSION_FIELDS}
    version_from_documents(documents)
    notes = log.read_text(encoding="utf-8")
    validate_release_log(notes, version)
    try:
        # Creating a ref fails if it exists; never update or force-push a tag.
        api("POST", "git/refs", {"ref": f"refs/tags/{tag}", "sha": sha})
    except HTTPError as error:
        if error.code in (409, 422) and tag_exists(api, tag):
            return f"SKIP: tag {tag} was created concurrently; tag and release left unchanged"
        raise

    try:
        release = api("POST", "releases", {
            "tag_name": tag,
            "target_commitish": sha,
            "name": tag,
            "body": notes,
            "draft": False,
            "prerelease": rank[3][0] == 0,
            "make_latest": "false" if rank[3][0] == 0 else "legacy",
            "generate_release_notes": False,
        })
    except (OSError, ValueError) as error:
        raise RuntimeError(
            f"Tag {tag} was created, but release creation failed ({error}). "
            "The tag is preserved and reruns will skip it; a maintainer must create the missing release."
        ) from error
    return f"Published {release['html_url']}"


def main() -> int:
    try:
        if (os.environ.get("GITHUB_EVENT_NAME"), os.environ.get("GITHUB_REF"), os.environ.get("GITHUB_REPOSITORY")) != (
            "push", "refs/heads/main", REPOSITORY,
        ):
            raise ValueError("Publication is restricted to main-branch pushes in the upstream repository")
        if not os.environ.get("GH_TOKEN"):
            raise ValueError("Publication requires the workflow's GITHUB_TOKEN with contents: write")
        print(publish_release(Path(__file__).resolve().parents[1], os.environ.get("GITHUB_SHA", "")))
    except HTTPError as error:
        print(f"ERROR: GitHub API returned HTTP {error.code}: {error.reason}", file=sys.stderr)
        return 1
    except (OSError, URLError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
