"""Offline checks for effect hosts (zoom, filter, shake, flash) in index.html.

An effect is an empty visual host the editor lists and edits and the service's engine
replays; the aip-composition skill owns the contract. These checks
mirror what the service accepts, so a host that passes here is one the editor shows.
"""

import math
import re

ENGINE = "public/vendor/speaker-effects.js"
TRACKS = {"zoom": "20", "filter": "21", "shake": "22", "flash": "23"}
MAX_SCALE = 3.0
MAX_RAMP = 10.0
MAX_AMPLITUDE = 60.0
FREQUENCY_RANGE = (1.0, 30.0)
COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
ANCHOR_TOLERANCE = 0.02

_FUNCTION = (
    r"(?:(?:grayscale|sepia|saturate|contrast|brightness|invert)\(\d{1,3}(?:\.\d{1,4})?%?\)"
    r"|hue-rotate\(-?\d{1,3}(?:\.\d{1,4})?deg\)"
    r"|blur\(\d{1,2}(?:\.\d{1,4})?px\))"
)
FILTER = re.compile(rf"^{_FUNCTION}(?:\s+{_FUNCTION}){{0,7}}$")
_COORD = r"-?\d{1,4}(?:\.\d{1,4})?(?:%|px)"
ORIGIN = re.compile(rf"^{_COORD}\s+{_COORD}$")


def _number(value, default=None):
    if value is None or str(value).strip() == "":
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _source_at(clips, start):
    """The source second playing at output second ``start``, or None off the cut."""
    for attrs in clips:
        clip_start = _number(attrs.get("data-start"))
        clip_duration = _number(attrs.get("data-duration"))
        media_start = _number(attrs.get("data-media-start"), 0.0)
        if None in (clip_start, clip_duration, media_start):
            continue
        if clip_start <= start < clip_start + clip_duration:
            return media_start + (start - clip_start)
    return None


def _value_codes(kind, attrs, duration):
    codes = []
    ramp_in = _number(attrs.get("data-effect-in"), 0.0)
    ramp_out = _number(attrs.get("data-effect-out"), 0.0)
    if ramp_in is None or ramp_out is None or not (0 <= ramp_in <= MAX_RAMP and 0 <= ramp_out <= MAX_RAMP):
        codes.append("invalid_speaker_effect_ramp")
    elif ramp_in + ramp_out > duration:
        codes.append("speaker_effect_ramps_exceed_window")
    if kind == "filter":
        if not FILTER.match((attrs.get("data-effect-filter") or "").strip()):
            codes.append("invalid_speaker_effect_filter")
        return codes
    if kind == "shake":
        return codes + _shake_codes(attrs)
    if kind == "flash":
        return codes + _flash_codes(attrs)
    scale = _number(attrs.get("data-effect-scale"))
    if scale is None or not 1 < scale <= MAX_SCALE:
        codes.append("invalid_speaker_effect_scale")
    origin = attrs.get("data-effect-origin")
    if origin is not None and not ORIGIN.match(origin.strip()):
        codes.append("invalid_speaker_effect_origin")
    return codes


def _optional(attrs, name):
    """An optional value: absent or blank is None, otherwise its text."""
    value = attrs.get(name)
    return None if value is None or str(value).strip() == "" else str(value).strip()


def _shake_codes(attrs):
    codes = []
    amplitude = _number(attrs.get("data-effect-amplitude"))
    if amplitude is None or not 0 < amplitude <= MAX_AMPLITUDE:
        codes.append("invalid_speaker_effect_amplitude")
    frequency = _optional(attrs, "data-effect-frequency")
    low, high = FREQUENCY_RANGE
    if frequency is not None and not low <= (_number(frequency) or -1.0) <= high:
        codes.append("invalid_speaker_effect_frequency")
    return codes


def _flash_codes(attrs):
    codes = []
    color = _optional(attrs, "data-effect-color")
    if color is not None and not COLOR.match(color):
        codes.append("invalid_speaker_effect_color")
    opacity = _optional(attrs, "data-effect-opacity")
    if opacity is not None and not 0 < (_number(opacity) or 0.0) <= 1:
        codes.append("invalid_speaker_effect_opacity")
    return codes


def _host_codes(attrs, clips):
    kind = attrs.get("data-aip-effect")
    if kind not in TRACKS or "visual-host" not in (attrs.get("class") or "").split() or not attrs.get(
        "data-composition-id"
    ):
        return ["invalid_speaker_effect"], None
    codes = []
    if "data-composition-src" in attrs:
        codes.append("speaker_effect_has_composition")
    if attrs.get("data-hide-captions") != "false":
        codes.append("speaker_effect_hides_captions")
    if "data-no-timeline" not in attrs:
        codes.append("speaker_effect_waits_for_timeline")
    if attrs.get("data-track-index") != TRACKS[kind]:
        codes.append("speaker_effect_track")
    start = _number(attrs.get("data-start"))
    duration = _number(attrs.get("data-duration"))
    if start is None or duration is None or duration <= 0:
        return codes, None  # the timing check reports the attribute itself
    codes.extend(_value_codes(kind, attrs, duration))
    anchor = _number(attrs.get("data-src-anchor"))
    expected = _source_at(clips, start)
    if anchor is None:
        codes.append("speaker_effect_anchor_missing")
    elif expected is not None and abs(anchor - expected) > ANCHOR_TOLERANCE:
        codes.append("speaker_effect_anchor_mismatch")
    return codes, (kind, start, start + duration)


def check(elements):
    """Error codes for the effect hosts among ``index.html``'s ``(tag, attrs, depth)``
    elements, in the order found; empty when there are none or all are valid."""
    top = [(tag, attrs) for tag, attrs, depth in elements if depth == 0]
    clips = [attrs for tag, attrs in top if tag == "video" and attrs.get("data-track-index") == "0"]
    codes, windows = [], {kind: [] for kind in TRACKS}
    hosts = [attrs for _, attrs in top if attrs.get("data-aip-effect") is not None]
    for attrs in hosts:
        host_codes, window = _host_codes(attrs, clips)
        codes.extend(host_codes)
        if window is not None:
            windows[window[0]].append(window[1:])
    for spans in windows.values():
        spans.sort()
        if any(later[0] < earlier[1] for earlier, later in zip(spans, spans[1:])):
            codes.append("speaker_effect_overlap")
    engine_loaded = any(tag == "script" and (attrs.get("src") or "").strip() == ENGINE for tag, attrs in top)
    if hosts and not engine_loaded:
        codes.append("speaker_effect_engine_missing")
    return list(dict.fromkeys(codes))
