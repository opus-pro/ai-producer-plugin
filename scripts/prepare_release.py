#!/usr/bin/env python3
"""Align local version files and create a release-log draft; no Git or network writes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from check_release_pr import (
    RELEASE_TEMPLATE, VERSION_FIELDS, precedence, reject_constant,
    release_log_path, unique_object, validate_release_log, version_from_documents,
)


def prepare_release(root: Path, version: str) -> Path:
    documents = {}
    for relative in VERSION_FIELDS:
        path = root / relative
        if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o111:
            raise ValueError(f"Version file must be regular and non-executable: {relative}")
        documents[relative] = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
    current = version_from_documents(documents)
    if precedence(version) <= precedence(current):
        raise ValueError(f"New version must be newer than {current}")
    log = root / release_log_path(version)
    if log.exists() or log.is_symlink():
        raise ValueError(f"Release log already exists: {log.name}")
    template = (root / RELEASE_TEMPLATE).read_text(encoding="utf-8")
    for field in ("version", "previous_version"):
        if "{{" + field + "}}" not in template:
            raise ValueError(f"Release template is missing the {field} placeholder")
    draft = template.replace("{{version}}", version).replace("{{previous_version}}", current)
    preview = draft.replace("{{pr_number}}", "1").replace("{{related_pr_number}}", "2")
    preview = re.sub(r"\{\{[^{}]+\}\}", "Draft", preview)
    validate_release_log(preview, version, previous_version=current)

    # Validate every input before modifying any file.
    for relative, fields in VERSION_FIELDS.items():
        for field in fields:
            parent = documents[relative]
            for key in field[:-1]:
                parent = parent[key]
            parent[field[-1]] = version
    for relative, document in documents.items():
        (root / relative).write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    log.write_text(draft, encoding="utf-8")
    return log


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="Target SemVer without the v prefix")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        log = prepare_release(args.repo, args.version)
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Prepared chore: release v{args.version}")
    print(f"Fill in {log.relative_to(args.repo)} before running python3 scripts/test.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
