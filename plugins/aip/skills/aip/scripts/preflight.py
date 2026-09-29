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

# Files the service writes in the same commit that first names them, so a document may load
# one before it exists locally or in the workspace.
SERVICE_WRITTEN = ("public/vendor/three.min.js",)

# The commit's code-drawn rules, judged on a document whose script paints a canvas; the
# composition skill's code-drawn reference explains each code. Comments never count, and
# the clock and determinism rules skip string literals too.
JS_STRING_OR_COMMENT = re.compile(
    r"(?P<str>\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`)"
    r"|(?P<block>/\*.*?\*/)|(?P<line>//[^\n]*)", re.S)
DRAWS = re.compile(r"\.\s*getContext\s*\(|\bWebGLRenderer\s*\(")
WEBGL = re.compile(r"""\.\s*getContext\s*\(\s*(['"`])(?:experimental-)?webgl2?\1|\bWebGLRenderer\s*\(""")
RELEASE = re.compile(r"\b(?:loseContext|forceContextLoss)\s*\(")
CLOCK = re.compile(r"\b(?:requestAnimationFrame|setAnimationLoop|setTimeout|setInterval)\b")
NONDETERMINISTIC = re.compile(
    r"\bMath\s*\.\s*random\b|\bDate\s*\.\s*now\b|\bnew\s+Date\b|\bperformance\s*\.\s*now\b")
THREE_SRC = re.compile(r"(?:^|/)three(?:\.min)?\.js$")
# A read of the global that tests it; a bare `const T = window.THREE` at the top level does not.
THREE_GUARD = re.compile(
    r"!\s*window\s*\.\s*THREE\b|\bif\s*\(\s*window\s*\.\s*THREE\b"
    r"|\bwindow\s*\.\s*THREE\s*(?:&&|\|\||\?(?!\.)|[!=]==?)|\btypeof\s+(?:window\s*\.\s*)?THREE\b")
# The `type` values a browser runs as JavaScript, compared without MIME parameters.
EXECUTABLE_SCRIPT_TYPES = {
    "", "module", "application/ecmascript", "application/javascript", "application/x-ecmascript",
    "application/x-javascript", "text/ecmascript", "text/javascript", "text/javascript1.0",
    "text/javascript1.1", "text/javascript1.2", "text/javascript1.3", "text/javascript1.4",
    "text/javascript1.5", "text/jscript", "text/livescript", "text/x-ecmascript", "text/x-javascript",
}


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []
        self.styles = []
        self.scripts = []
        self.in_style = False
        self.in_script = False
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
        if tag == "script" and "src" not in values:
            declared = (values.get("type") or "").split(";", 1)[0].strip().lower()
            self.in_script = declared in EXECUTABLE_SCRIPT_TYPES

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False
        if tag == "script":
            self.in_script = False
        if tag == "template":
            self.template_depth = max(0, self.template_depth - 1)

    def handle_data(self, data):
        if self.in_style:
            self.styles.append(data)
        if self.in_script:
            self.scripts.append(data)


def code_drawn(doc):
    """The code-drawn error and warning codes one parsed document earns."""
    source = "\n".join(doc.scripts)
    with_strings = JS_STRING_OR_COMMENT.sub(lambda match: match.group("str") or " ", source)
    code = JS_STRING_OR_COMMENT.sub(" ", source)
    draws = DRAWS.search(with_strings) is not None
    loads_three = any(tag == "script" and THREE_SRC.search((attrs.get("src") or "").split("?")[0])
        for tag, attrs, _ in doc.elements)
    errors, warnings = [], []
    if draws and CLOCK.search(code):
        errors.append("code_drawn_clock")
    if WEBGL.search(with_strings) and not RELEASE.search(code):
        errors.append("webgl_context_not_released")
    if loads_three and not THREE_GUARD.search(code):
        warnings.append("three_used_before_load")
    if draws and NONDETERMINISTIC.search(code):
        warnings.append("code_drawn_nondeterministic")
    return errors, warnings


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

    declared.update((root / name).resolve() for name in SERVICE_WRITTEN)
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
        drawn_errors, drawn_warnings = code_drawn(doc)
        for code in drawn_errors:
            issue(errors, code, path)
        for code in drawn_warnings:
            issue(warnings, code, path)
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
                # The caption layer the service built and staged is declared with
                # --remote-file and cannot be read here, so it is reported as a warning.
                # Every other missing composition, declared or not, stays an error: its
                # id and contents were never checked.
                service_caption = (target is not None and target in declared
                    and attrs.get("data-composition-id") == "narrator-captions")
                issue(warnings if service_caption else errors, "composition_not_locally_inspectable", path)
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
