#!/usr/bin/env python3
"""Check a local AI Producer workspace without network, media decoding, or rendering."""

import argparse
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
from editing_script_sync import EDITING_SCRIPT, sync_workspace, validate_workspace

CSS_URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.I)

# What the service accepts, by extension. Any other type, a script or an .svg included, is
# rejected at signing and refused at commit as unpromotable_type; vector graphics go inline
# in the HTML, and scripts are the ones the project already carries.
PROMOTABLE_SUFFIXES = {
    ".html", ".htm", ".css", ".json",
    ".png", ".jpg", ".jpeg", ".webp", ".gif",
    ".woff", ".woff2", ".ttf", ".otf",
    ".mp4", ".mov", ".webm",
    ".mp3", ".wav", ".m4a", ".ogg",
}


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []
        self.styles = []
        self.in_style = False
        self.template_depth = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "template":
            self.template_depth += 1
        self.elements.append((tag, values, self.template_depth))
        if "style" in values:
            self.styles.append(values["style"] or "")
        if tag == "style":
            self.in_style = True

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False
        if tag == "template":
            self.template_depth = max(0, self.template_depth - 1)

    def handle_data(self, data):
        if self.in_style:
            self.styles.append(data)


def check(root, remote_files=()):
    root = Path(root).resolve()
    errors, warnings = [], []
    documents = {}
    declared = set()

    def issue(collection, code, path=None, attribute=None):
        item = {"code": code}
        if path is not None:
            item["file"] = path.relative_to(root).as_posix()
        if attribute:
            item["attribute"] = attribute
        if item not in collection:
            collection.append(item)

    for name in remote_files:
        if name.startswith("render-engine/"):
            name = name[len("render-engine/"):]
        candidate = (root / name).resolve()
        if urlsplit(name).scheme or not candidate.is_relative_to(root):
            issue(errors, "invalid_service_file")
        else:
            declared.add(candidate)

    def reference(value, owner, attribute, base=None):
        """Resolve one reference. Media, images, stylesheets and data-* references in
        an HTML document resolve from the root, whichever directory holds it, because
        the editor mounts a composition's template into index.html. A script src and
        a url() in a .css file resolve from their own file, as the export's page load
        and CSS do (the editor re-points a composition's vendor script by file name)."""
        if not value or value.startswith(("#", "data:")):
            return None
        parts = urlsplit(value)
        if parts.scheme or parts.netloc:
            issue(errors, "remote_reference_unsupported", owner, attribute)
            return None
        candidate = ((base or root) / unquote(parts.path)).resolve()
        if not candidate.is_relative_to(root):
            issue(errors, "reference_outside_workspace", owner, attribute)
            return None
        if not candidate.is_file() and candidate not in declared:
            issue(errors, "missing_local_reference", owner, attribute)
        return candidate

    for path in sorted(root.rglob("*")):
        # Hidden entries are editor and OS metadata, never part of a publication.
        if not path.is_file() or any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        suffix = path.suffix.lower()
        if suffix not in PROMOTABLE_SUFFIXES and path.resolve() not in declared:
            issue(errors, "unpromotable_type", path)
            continue
        if suffix not in {".html", ".css"}:
            continue
        if not path.resolve().is_relative_to(root):
            issue(errors, "symlink_outside_workspace", path)
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            issue(errors, "unreadable_text", path)
            continue
        if suffix == ".css":
            for match in CSS_URL.finditer(source):
                reference(match[2], path, "css-url", base=path.parent)
            continue
        doc = Document()
        doc.feed(source)
        documents[path] = doc
        for tag, attrs, depth in doc.elements:
            for key in ("src", "href", "data-composition-src", "data-pip-src"):
                if key in attrs:
                    reference(attrs[key], path, key, base=path.parent if tag == "script" else None)
            for key in ("data-start", "data-media-start", "data-duration"):
                if key not in attrs:
                    continue
                try:
                    number = float(attrs[key])
                    valid = math.isfinite(number) and (number > 0 if key == "data-duration" else number >= 0)
                except (ValueError, TypeError):
                    valid = False
                if not valid:
                    issue(errors, "invalid_timing", path, key)
            if tag == "video" and (path != root / "index.html" or depth):
                issue(warnings, "nested_video_requires_player_validation", path)
        for style in doc.styles:
            for match in CSS_URL.finditer(style):
                reference(match[2], path, "css-url")

    index = documents.get(root / "index.html")
    stages = [] if index is None else [attrs for _, attrs, depth in index.elements
        if attrs.get("id") == "stage" and depth == 0]
    if len(stages) != 1 or stages[0].get("data-composition-id") != "finecut-root":
        issue(errors, "missing_or_invalid_root")
    for path, doc in documents.items():
        for _, attrs, _ in doc.elements:
            if "data-composition-src" not in attrs:
                continue
            target = reference(attrs["data-composition-src"], path, "data-composition-src")
            child = documents.get(target)
            if child is None:
                # A composition the service built and staged (a caption layer) is declared
                # with --remote-file and cannot be read here; report it, but only an
                # undeclared missing composition is an error.
                declared_remote = target is not None and target in declared
                issue(warnings if declared_remote else errors, "composition_not_locally_inspectable", path)
                continue
            identifier = attrs.get("data-composition-id")
            matches = [values for _, values, depth in child.elements
                if depth > 0 and identifier and values.get("data-composition-id") == identifier]
            if len(matches) != 1:
                issue(errors, "composition_id_mismatch", path)
    script = root / EDITING_SCRIPT
    if script.exists() or script in declared:
        try:
            validate_workspace(root)
        except (ValueError, OSError, UnicodeError) as error:
            code = str(error) if isinstance(error, ValueError) else "editing_script_unreadable"
            issue(errors, code, script)
    return {"ok": not errors, "html_files": len(documents), "errors": errors, "warnings": warnings,
            "scope": "Static checks only; no playback, editability, or export validation."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--remote-file", action="append", default=[],
                        help="Workspace-relative file confirmed staged by the service; repeat per file")
    parser.add_argument("--sync-editing-script", action="store_true",
                        help="Synchronize the fetched editing document before checking; upload it with index.html")
    args = parser.parse_args()
    synchronized_files = None
    if args.sync_editing_script:
        try:
            synchronized_files = sync_workspace(args.workspace)["files"]
        except (ValueError, OSError, UnicodeError) as error:
            code = str(error) if isinstance(error, ValueError) else "editing_script_unreadable"
            print(json.dumps({"ok": False, "errors": [{"code": code}], "warnings": []}))
            return 1
    result = check(args.workspace, args.remote_file)
    if synchronized_files is not None:
        result["synchronized_files"] = synchronized_files
    print(json.dumps(result, separators=(",", ":")))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
