"""Keep progressive AIP publications on one approved speaker timeline."""

from __future__ import annotations

from html.parser import HTMLParser
import math


_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
_EPSILON = 1e-6


class _Node:
    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children = []


class _IndexParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.document = _Node("document", {}, None)
        self.stack = [self.document]
        self.invalid = False

    def handle_starttag(self, tag, attrs):
        if len({key for key, _ in attrs}) != len(attrs):
            self.invalid = True
        node = _Node(tag, dict(attrs), self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in _VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if len(self.stack) == 1 or self.stack[-1].tag != tag:
            self.invalid = True
            return
        self.stack.pop()


def _fail(code):
    raise ValueError(code)


def _number(value, code, *, positive=False):
    try:
        number = float(value)
    except (TypeError, ValueError):
        _fail(code)
    if not math.isfinite(number) or (number <= 0 if positive else number < 0):
        _fail(code)
    return number


def _integer(value, code):
    try:
        number = int(value)
    except (TypeError, ValueError):
        _fail(code)
    if str(number) != str(value):
        _fail(code)
    return number


def _descendants(node):
    for child in node.children:
        yield child
        yield from _descendants(child)


def _classes(node):
    return set((node.attrs.get("class") or "").split())


def _speaker_snapshot(nodes):
    clips = []
    ids = set()
    pairs = {}
    for node in nodes:
        if node.tag not in {"video", "audio"} or "speaker-clip" not in _classes(node):
            continue
        attrs = node.attrs
        identifier = attrs.get("id")
        hf_id = attrs.get("data-hf-id")
        source = attrs.get("src")
        if not identifier or identifier in ids or not hf_id or not source:
            _fail("invalid_speaker_clip")
        ids.add(identifier)
        clip = {
            "id": identifier, "tag": node.tag, "src": source,
            "start": _number(attrs.get("data-start"), "invalid_speaker_timing"),
            "duration": _number(attrs.get("data-duration"), "invalid_speaker_timing", positive=True),
            "media_start": _number(attrs.get("data-media-start"), "invalid_speaker_timing"),
            "track": _integer(attrs.get("data-track-index"), "invalid_speaker_track"),
            "volume": _number(attrs.get("data-volume"), "invalid_speaker_volume"),
            "hf_id": hf_id,
        }
        if clip["volume"] > 1:
            _fail("invalid_speaker_volume")
        pairs.setdefault(hf_id, []).append(clip)
        clips.append(clip)
    if not clips or "speaker" not in ids or "speaker-audio" not in ids:
        _fail("missing_speaker_av")
    for pair in pairs.values():
        if len(pair) != 2 or {item["tag"] for item in pair} != {"video", "audio"}:
            _fail("unpaired_speaker_av")
        if pair[0]["start"] != pair[1]["start"] or pair[0]["duration"] != pair[1]["duration"]:
            _fail("unpaired_speaker_av")
    return tuple(sorted((tuple(sorted(item.items())) for item in clips)))


def _coverage(clips, duration):
    for tag in ("video", "audio"):
        spans = sorted((dict(item)["start"], dict(item)["duration"]) for item in clips if dict(item)["tag"] == tag)
        if not spans:
            _fail("missing_speaker_av")
        cursor = 0.0
        for start, length in spans:
            if not math.isclose(start, cursor, abs_tol=_EPSILON):
                _fail("incomplete_speaker_coverage")
            cursor = start + length
        if not math.isclose(cursor, duration, abs_tol=_EPSILON):
            _fail("incomplete_speaker_coverage")


def inspect_index(html_text):
    """Return the non-caption effect and immutable-speaker semantics of one index."""
    if not isinstance(html_text, str):
        _fail("invalid_index_html")
    parser = _IndexParser()
    try:
        parser.feed(html_text)
        parser.close()
    except Exception:
        _fail("invalid_index_html")
    if parser.invalid or len(parser.stack) != 1:
        _fail("invalid_index_html")
    stage_nodes = [node for node in _descendants(parser.document) if node.attrs.get("id") == "stage"]
    roots = [node for node in stage_nodes if node.attrs.get("data-composition-id") == "finecut-root"]
    if len(stage_nodes) != 1 or len(roots) != 1:
        _fail("invalid_root")
    root = roots[0]
    duration = _number(root.attrs.get("data-duration"), "invalid_root_duration", positive=True)
    if not math.isclose(_number(root.attrs.get("data-start"), "invalid_root_timing"), 0.0, abs_tol=_EPSILON):
        _fail("invalid_root_timing")
    nodes = list(_descendants(root))
    speaker = _speaker_snapshot(nodes)
    _coverage(speaker, duration)
    effects = {}
    for node in nodes:
        if "visual-host" not in _classes(node):
            continue
        attrs = node.attrs
        identifier = attrs.get("data-composition-id")
        if not identifier:
            _fail("invalid_visual_host")
        if identifier == "narrator-captions":
            continue
        if identifier in effects:
            _fail("duplicate_effect_id")
        source = attrs.get("data-composition-src")
        if not source:
            _fail("invalid_visual_host")
        effects[identifier] = {
            "id": identifier, "src": source,
            "start": _number(attrs.get("data-start"), "invalid_visual_timing"),
            "duration": _number(attrs.get("data-duration"), "invalid_visual_timing", positive=True),
            "track": _integer(attrs.get("data-track-index"), "invalid_visual_track"),
        }
    return {"duration": duration, "effects": effects, "speaker": speaker}


def validate_progress(baseline_html, previous_html, candidate_html, planned_duration):
    """Accept exactly one new visual host while holding the approved edit fixed."""
    baseline = inspect_index(baseline_html)
    previous = inspect_index(previous_html)
    planned = _number(planned_duration, "invalid_planned_duration", positive=True)
    for snapshot in (baseline, previous):
        if not math.isclose(snapshot["duration"], planned, abs_tol=_EPSILON):
            _fail("planned_duration_mismatch")
        if snapshot["speaker"] != baseline["speaker"]:
            _fail("speaker_timeline_changed")
    return validate_checkpoint_progress(baseline, previous["effects"], candidate_html, planned)


def validate_checkpoint_progress(baseline, previous_effects, candidate_html, planned_duration):
    """Validate one step from semantic state saved between model checkpoints."""
    planned = _number(planned_duration, "invalid_planned_duration", positive=True)
    if not isinstance(baseline, dict) or not isinstance(previous_effects, dict):
        _fail("invalid_progress_state")
    candidate = inspect_index(candidate_html)
    for snapshot in (baseline, candidate):
        if not math.isclose(snapshot.get("duration", -1), planned, abs_tol=_EPSILON):
            _fail("planned_duration_mismatch")
        if snapshot.get("speaker") != baseline.get("speaker"):
            _fail("speaker_timeline_changed")
    if baseline["effects"]:
        _fail("baseline_has_visual_effects")
    candidate_effects = candidate["effects"]
    if len(candidate_effects) != len(previous_effects) + 1:
        _fail("invalid_effect_transition")
    for identifier, effect in previous_effects.items():
        if candidate_effects.get(identifier) != effect:
            _fail("existing_effect_changed")
    return candidate
