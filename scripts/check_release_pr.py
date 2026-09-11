#!/usr/bin/env python3
"""Check release PR titles, changed files, and version fields without checkout."""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
from pathlib import Path


LATEST_VERSION_FILE = "releases/latest_version.json"
RELEASE_TEMPLATE = "releases/template.md"
LOG_SECTIONS = ("Changes", "Compatibility", "Validation")
REPOSITORY_URL = "https://github.com/opus-pro/ai-producer-plugin"
PR_LINK = re.compile(r"\[#([1-9][0-9]*)\]\(" + re.escape(REPOSITORY_URL) + r"/pull/\1\)")
VERSION_FIELDS = {
    LATEST_VERSION_FILE: (("version",),),
    "plugins/aip/.codex-plugin/plugin.json": (("version",),),
    "plugins/aip/.claude-plugin/plugin.json": (("version",),),
    ".claude-plugin/marketplace.json": (("plugins", 0, "version"),),
    "plugins/aip/.mcp.json": (
        ("mcpServers", "aip", "headers", "X-AIP-Plugin-Version"),
        ("mcpServers", "aip", "http_headers", "X-AIP-Plugin-Version"),
    ),
}
SEMVER = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
)
TITLE = re.compile(r"chore: release v(.+)")


def precedence(version: str) -> tuple:
    """Return SemVer precedence, excluding build metadata."""
    match = SEMVER.fullmatch(version)
    if not match:
        raise ValueError(f"Invalid semantic version: {version!r}")
    major, minor, patch, prerelease, _ = match.groups()
    identifiers = []
    if prerelease is not None:
        for identifier in prerelease.split("."):
            if identifier.isascii() and identifier.isdigit():
                if len(identifier) > 1 and identifier.startswith("0"):
                    raise ValueError(f"Invalid semantic version: {version!r}")
                identifiers.append((0, int(identifier)))
            else:
                identifiers.append((1, identifier))
    suffix = (1,) if prerelease is None else (0, tuple(identifiers))
    return (int(major), int(minor), int(patch), suffix)


def git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "--no-replace-objects", "-C", str(repo), *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise ValueError(f"Git {args[0]} failed; fetch the base and head commits with full history")
    return result.stdout


def unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise ValueError(f"Invalid JSON constant: {value!r}")


def version_from_documents(documents: dict, *, allow_legacy: bool = False) -> str:
    """Check the canonical version and every host-specific copy."""
    versions = []
    for path, fields in VERSION_FIELDS.items():
        if allow_legacy and path == LATEST_VERSION_FILE and path not in documents:
            continue
        try:
            document = documents[path]
            if path == LATEST_VERSION_FILE and set(document) != {"version"}:
                raise ValueError("The latest-version file must contain only the version key")
            for field in fields:
                value = document
                for key in field:
                    value = value[key]
                if not isinstance(value, str):
                    raise ValueError("Version must be a string")
                precedence(value)
                versions.append(value)
        except (ValueError, KeyError, IndexError, TypeError, UnicodeError) as error:
            raise ValueError(f"Invalid version file {path}: {error}") from error
    if len(set(versions)) != 1:
        raise ValueError("All six version fields must match across the five version files")
    return versions[0]


def regular_blob(repo: Path, ref: str, path: str) -> bytes:
    if not git(repo, "ls-tree", ref, "--", path).startswith(b"100644 blob "):
        raise ValueError(f"Release file must exist as a regular, non-executable file: {path}")
    return git(repo, "show", f"{ref}:{path}")


def snapshot(repo: Path, ref: str, *, allow_legacy: bool = False) -> tuple[dict, str]:
    documents = {}
    for path in VERSION_FIELDS:
        # A merge base may predate the introduction of the release directory.
        if allow_legacy and path == LATEST_VERSION_FILE and not git(repo, "ls-tree", ref, "--", path):
            continue
        try:
            documents[path] = json.loads(
                regular_blob(repo, ref, path),
                object_pairs_hook=unique_object, parse_constant=reject_constant,
            )
        except (ValueError, UnicodeError) as error:
            raise ValueError(f"Invalid version file {path}: {error}") from error
    version = version_from_documents(documents, allow_legacy=allow_legacy)
    return documents, version


def release_log_path(version: str) -> str:
    return f"releases/v{version}.md"


def validate_changes(contents: str) -> None:
    categories = re.split(r"^### (.+)$", contents, flags=re.MULTILINE)
    if len(categories) < 3 or categories[0].strip():
        raise ValueError("Changes must group concise entries under category headings")
    for category, body in zip(categories[1::2], categories[2::2]):
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        if not lines:
            raise ValueError(f"Omit empty change categories: {category}")
        for line in lines:
            entry = re.fullmatch(r"- (.+?) \((.+)\)\.?", line)
            if not entry or not all(PR_LINK.fullmatch(link) for link in entry[2].split(", ")):
                raise ValueError("Each change must end with one or more matching PR-number links")


def validate_release_log(contents: str, version: str, *, previous_version: str | None = None) -> None:
    if not contents.splitlines() or contents.splitlines()[0] != f"# v{version}":
        raise ValueError(f"Release log must start with '# v{version}'")
    if re.search(r"\{\{.*?\}\}", contents, re.DOTALL):
        raise ValueError("Release log still contains template placeholders")
    visible = re.sub(r"<!--.*?-->", "", contents, flags=re.DOTALL).strip()
    body, _, footer = visible.rpartition("\n")
    comparison = re.fullmatch(r"\*\*Full Changelog\*\*: \[v(.+?)\.\.\.v(.+?)\]\(([^)]+)\)", footer)
    if not comparison:
        raise ValueError("Release log must end with a Full Changelog comparison link")
    previous, target, url = comparison.groups()
    if target != version or url != f"{REPOSITORY_URL}/compare/v{previous}...v{version}":
        raise ValueError("Full Changelog link must match its label and the release version")
    if precedence(previous) >= precedence(version):
        raise ValueError("Full Changelog must compare an earlier version to this release")
    if previous_version is not None and previous != previous_version:
        raise ValueError(f"Full Changelog must start from base version {previous_version}")

    sections = re.split(r"^## (.+)$", body, flags=re.MULTILINE)
    headings = sections[1::2]
    if headings != [section for section in LOG_SECTIONS if section in headings]:
        raise ValueError("Release log sections must be an ordered subset of Changes, Compatibility, and Validation")
    for heading, body in zip(headings, sections[2::2]):
        if not re.search(r"[A-Za-z0-9]", body):
            raise ValueError(f"Release log section must be filled in: {heading}")
        if heading == "Changes":
            validate_changes(body)


def without_versions(document: dict, fields: tuple) -> str:
    result = copy.deepcopy(document)
    for field in fields:
        parent = result
        for key in field[:-1]:
            parent = parent[key]
        parent[field[-1]] = None
    # Serialization also distinguishes JSON booleans from numeric values.
    return json.dumps(result, sort_keys=True)


def check_release_pr(repo: Path, base: str, head: str, title: str) -> str:
    base = git(repo, "rev-parse", "--verify", "--end-of-options", f"{base}^{{commit}}").decode().strip()
    head = git(repo, "rev-parse", "--verify", "--end-of-options", f"{head}^{{commit}}").decode().strip()
    ancestor = git(repo, "merge-base", base, head).decode().strip()
    before, old_version = snapshot(repo, ancestor, allow_legacy=True)
    after, new_version = snapshot(repo, head)
    base_documents, base_version = snapshot(repo, base, allow_legacy=True)
    version_changed = old_version != new_version
    release_title = TITLE.fullmatch(title)
    log_path = release_log_path(new_version)
    changed = {
        path.decode("utf-8", errors="surrogateescape")
        for path in git(repo, "diff", "--no-ext-diff", "--no-textconv", "--name-only", "--no-renames", "-z", ancestor, head, "--").split(b"\0")
        if path
    }
    changed_logs = {path for path in changed if path.startswith("releases/v") and path.endswith(".md")}

    if not version_changed and release_title is None and not title.startswith("chore(release)"):
        bootstrap = LATEST_VERSION_FILE not in before and LATEST_VERSION_FILE not in base_documents
        if changed_logs and not bootstrap:
            raise ValueError("Release logs require a version update; historical logs cannot be changed")
        for path in sorted(changed_logs):
            historical_version = path[len("releases/v"):-len(".md")]
            if precedence(historical_version) > precedence(new_version):
                raise ValueError("Initial release history cannot include versions newer than the declared version")
            if git(repo, "ls-tree", ancestor, "--", path) or git(repo, "ls-tree", base, "--", path):
                raise ValueError("Initial release history may only add logs; historical logs cannot be changed")
            contents = regular_blob(repo, head, path).decode("utf-8")
            # Archived releases predate the PR-link and comparison-link format.
            if not contents.startswith(f"# v{historical_version}\n") or not contents.split("\n", 1)[1].strip():
                raise ValueError(f"Historical release log must have a matching version heading and content: {path}")
            if re.search(r"\{\{.*?\}\}", contents, re.DOTALL):
                raise ValueError("Historical release log still contains template placeholders")
        validate_release_log(regular_blob(repo, head, log_path).decode("utf-8"), new_version)
        return "OK: no version change; ordinary PR"
    if not release_title:
        raise ValueError("Version updates require a separate PR titled chore: release vX.Y.Z")
    if release_title[1] != new_version:
        raise ValueError(f"PR title must match the version files: chore: release v{new_version}")
    if not version_changed:
        raise ValueError("A release PR must change the version")

    unexpected = changed - (VERSION_FIELDS.keys() | {log_path})
    if unexpected:
        raise ValueError(f"Release PRs may only change the five version files and the new release log; unexpected paths: {sorted(unexpected)!r}")
    for path, fields in VERSION_FIELDS.items():
        original = before.get(path, {"version": old_version})
        if without_versions(original, fields) != without_versions(after[path], fields):
            raise ValueError(f"Release PRs may only change version fields, not other content in {path}")

    if precedence(new_version) <= max(precedence(old_version), precedence(base_version)):
        raise ValueError(f"Release version must be newer than both {old_version} and base version {base_version}")
    if log_path not in changed or git(repo, "ls-tree", ancestor, "--", log_path) or git(repo, "ls-tree", base, "--", log_path):
        raise ValueError(f"Release PR must add a new release log: {log_path}")
    validate_release_log(regular_blob(repo, head, log_path).decode("utf-8"), new_version, previous_version=base_version)
    return f"OK: release {old_version} -> {new_version}; title, file scope, all six version fields, and release log match"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base", required=True, help="Fetched PR base commit")
    parser.add_argument("--head", required=True, help="Fetched PR head commit")
    parser.add_argument("--title", required=True, help="Current PR title")
    args = parser.parse_args()
    try:
        print(check_release_pr(args.repo, args.base, args.head, args.title))
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
