#!/usr/bin/env python3
"""Synchronize a fetched EditingScript with a single-source speaker cut, offline.

Only the AV and caption projections change. Unsupported media clocks or a mounted
caption renderer that would need rebaking are refused before any file is written.
"""

import argparse
from copy import deepcopy
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from html.parser import HTMLParser
import json
import math
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import unquote, urlsplit


EDITING_SCRIPT = "compositions/editing-script.json"
AV_TRACK_ID = "t-av"
RAW_AUDIO = {"public/source.mp3", "public/source.enhanced.mp3"}
REMOVAL_REASON = {"kind": "agent", "by": "lui"}
TIMES = ("srcStart", "srcEnd", "timelineIn", "timelineOut")
MAX_WORKSPACE_TEXT_BYTES = 32 * 1024 * 1024
TIMING_TOLERANCE_MS = Decimal("1")


def _require(condition, code):
    if not condition:
        raise ValueError(code)


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _local_path(value):
    _require(isinstance(value, str) and bool(value), "editing_script_unsupported_source")
    parsed = urlsplit(value)
    _require(not (parsed.scheme or parsed.netloc or parsed.query or parsed.fragment),
             "editing_script_unsupported_source")
    path = unquote(parsed.path)
    while path.startswith("./"):
        path = path[2:]
    _require(not path.startswith("/") and ".." not in path.split("/"),
             "editing_script_unsupported_source")
    return path


def _decimal_milliseconds(value):
    try:
        number = Decimal(str(value))
        _require(number.is_finite() and number >= 0, "editing_script_invalid_timing")
        return number * 1000
    except (InvalidOperation, TypeError, OverflowError):
        raise ValueError("editing_script_invalid_timing") from None


def _round_milliseconds(value):
    try:
        return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, OverflowError):
        raise ValueError("editing_script_invalid_timing") from None


def _milliseconds(value):
    return _round_milliseconds(_decimal_milliseconds(value))


class _Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []
        self.templates = 0

    def handle_starttag(self, tag, attrs):
        keys = [key for key, _ in attrs]
        _require(len(set(keys)) == len(keys), "editing_script_duplicate_attribute")
        if tag == "template":
            self.templates += 1
        if not self.templates:
            self.elements.append((tag, dict(attrs)))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "template":
            self.templates = max(0, self.templates - 1)


def _timing(attrs, single):
    for key in ("data-playback-rate", "data-playbackrate", "data-speed", "playbackrate"):
        if key in attrs:
            _require(attrs[key] in {"1", "1.0"}, "editing_script_unsupported_speed")
    _require("data-duration" in attrs, "editing_script_invalid_timing")
    if not single:
        _require("data-start" in attrs and "data-media-start" in attrs,
                 "editing_script_invalid_timing")
    start = _decimal_milliseconds(attrs.get("data-start", "0"))
    source = _decimal_milliseconds(attrs.get("data-media-start", "0"))
    duration = _decimal_milliseconds(attrs["data-duration"])
    _require(duration > 0, "editing_script_invalid_timing")
    return start, source, duration


def _speaker_cut(html, source):
    _require(not re.search(r"\.playbackRate\s*=", html), "editing_script_unsupported_speed")
    document = _Document()
    document.feed(html)
    elements = document.elements
    stages = [attrs for _, attrs in elements if attrs.get("id") == "stage"]
    _require(len(stages) == 1, "editing_script_missing_stage")
    stage = stages[0]
    _require(stage.get("data-composition-id") == "finecut-root"
             and _milliseconds(stage.get("data-start", "0")) == 0,
             "editing_script_invalid_stage")
    total = _decimal_milliseconds(stage.get("data-duration"))
    video_path = _local_path(source["path"])
    lanes = {}
    for tag in ("video", "audio"):
        key = "speaker" if tag == "video" else "speaker-audio"
        candidates = [attrs for item_tag, attrs in elements if item_tag == tag
                      and (attrs.get("id") == key
                           or "speaker-clip" in attrs.get("class", "").split())]
        _require(bool(candidates), "editing_script_missing_speaker_lane")
        _require(candidates[0].get("id") == key, "editing_script_speaker_order")
        ids = [attrs.get("id") for attrs in candidates]
        _require(all(ids) and len(set(ids)) == len(ids), "editing_script_duplicate_speaker_id")
        single = len(candidates) == 1 and "speaker-clip" not in candidates[0].get("class", "").split()
        lane = []
        for attrs in candidates:
            _require(single or "speaker-clip" in attrs.get("class", "").split(),
                     "editing_script_ambiguous_speaker_lane")
            path = _local_path(attrs.get("src"))
            _require(path == video_path if tag == "video" else path in RAW_AUDIO,
                     "editing_script_unsupported_source")
            identifier = attrs.get("data-hf-id") or ("clip-0" if single else None)
            _require(isinstance(identifier, str) and bool(identifier),
                     "editing_script_missing_clip_id")
            lane.append((identifier,) + _timing(attrs, single))
        _require(len({row[0] for row in lane}) == len(lane), "editing_script_duplicate_clip_id")
        lanes[tag] = lane
    _require(len(lanes["video"]) == len(lanes["audio"]), "editing_script_av_lane_mismatch")
    for video, audio in zip(lanes["video"], lanes["audio"]):
        _require(video[0] == audio[0] and all(abs(a - b) <= TIMING_TOLERANCE_MS
                                            for a, b in zip(video[1:], audio[1:])),
                 "editing_script_av_lane_mismatch")
    cursor, raw_cursor, previous_source_end = 0, Decimal(0), Decimal(0)
    clips = []
    for identifier, start, source_start, duration in lanes["video"]:
        _require(abs(start - raw_cursor) <= TIMING_TOLERANCE_MS, "editing_script_noncontiguous_output")
        _require(source_start + TIMING_TOLERANCE_MS >= previous_source_end,
                 "editing_script_unsupported_source_order")
        if source["duration"] is not None:
            _require(source_start + duration <= source["duration"] + TIMING_TOLERANCE_MS,
                     "editing_script_source_out_of_bounds")
        source_ms, duration_ms = _round_milliseconds(source_start), _round_milliseconds(duration)
        _require(duration_ms > 0, "editing_script_invalid_timing")
        # Validate raw boundaries before rounding. The service rounds each clip's
        # duration, then tiles those integer durations; fractional-frame cuts can
        # otherwise accumulate a false gap when comparing rounded DOM starts.
        clips.append({"id": identifier, "srcStart": source_ms, "srcEnd": source_ms + duration_ms,
                      "timelineIn": cursor, "timelineOut": cursor + duration_ms})
        cursor += duration_ms
        raw_cursor += duration
        previous_source_end = source_start + duration
    _require(abs(raw_cursor - total) <= TIMING_TOLERANCE_MS and total > 0,
             "editing_script_duration_mismatch")
    return clips, elements


def _source_clock(doc):
    if "source" not in doc:
        # Legacy caption-only wrappers omit the optional source header. The
        # canonical raw proxy still identifies the clock, but the full source
        # duration is unknown; never infer it from a trimmed output timeline.
        return {"path": "public/source.mp4", "duration": None}
    source = doc["source"]
    _require(isinstance(source, dict) and _integer(source.get("duration"))
             and source["duration"] > 0, "editing_script_unsupported_source")
    _local_path(source.get("path"))
    return source


def _validate_document(doc):
    _require(isinstance(doc, dict) and _integer(doc.get("schemaVersion")) and doc["schemaVersion"] == 1
             and _integer(doc.get("rev")) and doc["rev"] >= 0,
             "editing_script_invalid_document")
    source = _source_clock(doc)
    tracks = doc.get("tracks")
    _require(isinstance(tracks, list) and all(isinstance(track, dict) for track in tracks),
             "editing_script_invalid_document")
    _require(all(isinstance(track.get("items"), list) and isinstance(track.get("type"), str)
                 and isinstance(track.get("id"), str) for track in tracks),
             "editing_script_invalid_document")
    _require(sum(track.get("type") == "captions" for track in tracks) == 1
             and sum(track.get("type") == "av" for track in tracks) <= 1,
             "editing_script_ambiguous_tracks")
    _require(len({track["id"] for track in tracks}) == len(tracks), "editing_script_ambiguous_tracks")
    for track in tracks:
        if track.get("type") == "av":
            _require(isinstance(track.get("speakerVolume"), (int, float))
                     and not isinstance(track["speakerVolume"], bool)
                     and math.isfinite(track["speakerVolume"]) and track["speakerVolume"] >= 0,
                     "editing_script_invalid_document")
            _require(all(isinstance(item, dict) for item in track["items"]), "editing_script_invalid_document")
            identifiers = [item.get("id") for item in track["items"]]
            _require(all(isinstance(identifier, str) for identifier in identifiers)
                     and len(set(identifiers)) == len(identifiers), "editing_script_duplicate_clip_id")
            for item in track["items"]:
                _validate_timed(item, nullable=False)
                _require(item["srcEnd"] > item["srcStart"], "editing_script_invalid_document")
                if item.get("sourceUri"):
                    _require(_local_path(item["sourceUri"]) == _local_path(source["path"]),
                             "editing_script_unsupported_source")
        if track.get("type") == "captions":
            seen = set()
            for section in track["items"]:
                _require(isinstance(section, dict) and isinstance(section.get("id"), str)
                         and isinstance(section.get("segments"), list),
                         "editing_script_invalid_document")
                for segment in section["segments"]:
                    _require(isinstance(segment, dict) and isinstance(segment.get("id"), str)
                             and isinstance(segment.get("words"), list)
                             and _integer(segment.get("timelineIn"))
                             and _integer(segment.get("timelineOut")), "editing_script_invalid_document")
                    for word in segment["words"]:
                        _validate_timed(word, nullable=True)
                        _require(isinstance(word.get("text"), str), "editing_script_invalid_document")
                        if word.get("sourceUri"):
                            _require(_local_path(word["sourceUri"]) in RAW_AUDIO | {_local_path(source["path"])},
                                     "editing_script_unsupported_source")
                        _require(word["id"] not in seen, "editing_script_duplicate_word_id")
                        seen.add(word["id"])


def _validate_timed(item, nullable):
    _require(isinstance(item, dict) and isinstance(item.get("id"), str) and bool(item["id"]),
             "editing_script_invalid_document")
    for key in TIMES:
        valid = _integer(item.get(key))
        if nullable and key in ("srcStart", "srcEnd") and key in item:
            valid = valid or item[key] is None
        _require(valid, "editing_script_invalid_document")
    _require((item["srcStart"] is None) == (item["srcEnd"] is None),
             "editing_script_invalid_document")
    if item["srcStart"] is not None:
        _require(0 <= item["srcStart"] <= item["srcEnd"], "editing_script_invalid_document")
    _require(item["timelineIn"] <= item["timelineOut"] and item.get("state") in (None, "hidden", "deleted"),
             "editing_script_invalid_document")


def _playing(track):
    return sorted((item for item in track["items"] if item.get("state") is None),
                  key=lambda item: item["timelineIn"])


def _geometry(items):
    return [{key: item[key] for key in ("id",) + TIMES} for item in items]


def _subtract(ranges, covered):
    remaining = []
    for start, end in ranges:
        cursor = start
        for low, high in covered:
            if high <= cursor or low >= end:
                continue
            if low > cursor:
                remaining.append((cursor, min(low, end)))
            cursor = max(cursor, high)
        if cursor < end:
            remaining.append((cursor, end))
    return remaining


def _restore_window(item, clips):
    next_clip = next((clip for clip in clips if clip["srcStart"] >= item["srcStart"]), None)
    start = next_clip["timelineIn"] if next_clip else clips[-1]["timelineOut"]
    return {"timelineIn": start, "timelineOut": start + item["srcEnd"] - item["srcStart"]}


def _sync_av(track, clips):
    if track is None:
        track = {"id": AV_TRACK_ID, "type": "av", "speakerVolume": 1, "items": []}
    old = _playing(track)
    if _geometry(old) == clips and not track.get("ledgerAhead"):
        return deepcopy(track)
    updated = deepcopy(track)
    updated.pop("ledgerAhead", None)
    playable = []
    for clip in clips:
        prior = next((item for item in old if item["id"] == clip["id"]
                      and item["srcStart"] == clip["srcStart"] and item["srcEnd"] == clip["srcEnd"]), None)
        value = deepcopy(prior) if prior else {}
        value.update(clip)
        if prior is None and len(clips) > 1:
            value["origin"] = {"kind": "split", "from": "av-source"}
        playable.append(value)
    carried = []
    for item in track["items"]:
        if item.get("state") is not None and not any(
                item["srcStart"] < clip["srcEnd"] and clip["srcStart"] < item["srcEnd"] for clip in clips):
            value = deepcopy(item)
            value.update(_restore_window(item, clips))
            carried.append(value)
    removed = []
    occupied = {item["id"] for item in playable + carried}
    ranges = _subtract([(clip["srcStart"], clip["srcEnd"]) for clip in old],
                       [(clip["srcStart"], clip["srcEnd"]) for clip in clips])
    for start, end in ranges:
        identifier = "cut-{}".format(start)
        suffix = 1
        while identifier in occupied:
            identifier = "cut-{}-{}".format(start, suffix)
            suffix += 1
        occupied.add(identifier)
        item = {"id": identifier, "srcStart": start, "srcEnd": end,
                "state": "deleted", "stateReason": dict(REMOVAL_REASON),
                "origin": {"kind": "split", "from": "av-source"}}
        item.update(_restore_window(item, clips))
        removed.append(item)
    updated["items"] = playable + carried + removed
    return updated


def _covering(clips, source_time):
    return next((clip for clip in clips if clip["srcStart"] <= source_time < clip["srcEnd"]), None)


def _collapsed(clips, source_time):
    return max((clip["timelineOut"] for clip in clips if clip["srcStart"] < source_time), default=0)


def _project_segment(segment, clips):
    words = segment["words"]
    anchor = next((word for word in words if word["srcStart"] is not None
                   and _covering(clips, word["srcStart"]) is not None), None)
    anchor_output = None
    if anchor:
        clip = _covering(clips, anchor["srcStart"])
        anchor_output = clip["timelineIn"] + anchor["srcStart"] - clip["srcStart"]
    projected = []
    for word in words:
        updated = deepcopy(word)
        if word["srcStart"] is None:
            if anchor is None:
                start = end = word["timelineIn"]
            else:
                start = anchor_output + word["timelineIn"] - anchor["timelineIn"]
                end = start + word["timelineOut"] - word["timelineIn"]
        else:
            clip = _covering(clips, word["srcStart"])
            if clip is None:
                start = end = _collapsed(clips, word["srcStart"])
            else:
                intersections = sum(word["srcStart"] < item["srcEnd"]
                                    and item["srcStart"] < word["srcEnd"] for item in clips)
                _require(intersections <= 1, "editing_script_word_spans_cut")
                start = clip["timelineIn"] + word["srcStart"] - clip["srcStart"]
                end = min(clip["timelineOut"], clip["timelineIn"] + word["srcEnd"] - clip["srcStart"])
        updated.update(timelineIn=start, timelineOut=max(start, end))
        projected.append(updated)
    live = [word for word in projected if word["timelineOut"] > word["timelineIn"]]
    spanning = live or projected
    result = deepcopy(segment)
    result["words"] = projected
    result["timelineIn"] = min((word["timelineIn"] for word in spanning), default=0)
    result["timelineOut"] = max((word["timelineOut"] for word in spanning), default=0)
    return result


def _caption_spans(clips):
    # A speaker split alone does not cut speech. Adjacent source/output spans
    # share one caption clock, including the service's millisecond rounding.
    spans = []
    for clip in clips:
        if spans and abs(clip["srcStart"] - spans[-1]["srcEnd"]) <= TIMING_TOLERANCE_MS:
            spans[-1]["srcEnd"] = clip["srcEnd"]
            spans[-1]["timelineOut"] = clip["timelineOut"]
        else:
            spans.append(dict(clip))
    return spans


def _sync_captions(track, clips):
    clips = _caption_spans(clips)
    updated = deepcopy(track)
    for section in updated["items"]:
        section["segments"] = sorted((_project_segment(segment, clips) for segment in section["segments"]),
                                     key=lambda segment: segment["timelineIn"])
    updated["items"].sort(key=lambda section: section["segments"][0]["timelineIn"]
                          if section["segments"] else 0)
    segments = [segment for section in updated["items"] for segment in section["segments"]]
    for index, segment in enumerate(segments):
        segment["timelineIn"] = segments[index - 1]["timelineOut"] if index else 0
        if index + 1 < len(segments):
            segment["timelineOut"] = segments[index + 1]["timelineIn"]
    if segments and clips[-1]["timelineOut"] >= segments[-1]["timelineOut"]:
        segments[-1]["timelineOut"] = clips[-1]["timelineOut"]
    return updated


def _mounted_captions(elements):
    for _, attrs in elements:
        identifier = attrs.get("data-composition-id", "")
        path = attrs.get("data-composition-src", "")
        if (identifier == "narrator-captions" or "narrator_captions" in path
                or "caption-word" in attrs.get("class", "").split()):
            return True
        if re.search(r"(?:^|[-_/])captions?(?:[-_/.]|$)", identifier + "/" + path, re.I):
            return True
    return False


def synchronize(html, existing_doc):
    """Return a synced copy; input ownership and every unrelated track survive.

    Words use their immutable source anchors. A cut through a phrase does not
    make later words inherit the first word's clip. Leading boundary words whose
    source start was removed collapse; a retained word ends at its clip boundary.
    A word spanning two kept intervals is ambiguous and is refused.
    """
    _validate_document(existing_doc)
    clips, elements = _speaker_cut(html, _source_clock(existing_doc))
    av = next((track for track in existing_doc["tracks"] if track["type"] == "av"), None)
    captions = next(track for track in existing_doc["tracks"] if track["type"] == "captions")
    new_av = _sync_av(av, clips)
    new_captions = _sync_captions(captions, clips)
    old_words = [word for section in captions["items"] for segment in section["segments"]
                 for word in segment["words"]]
    new_words = [word for section in new_captions["items"] for segment in section["segments"]
                 for word in segment["words"]]
    if old_words == new_words:
        # Legacy display windows and adjacent speaker splits do not require a
        # caption rebake when every rendered word keeps its existing placement.
        # Leave that presentation intact instead of normalizing phrase windows.
        new_captions = deepcopy(captions)
    if new_captions != captions:
        _require(not _mounted_captions(elements), "editing_script_mounted_captions_require_rebake")
    result = deepcopy(existing_doc)
    result["tracks"] = [new_av if track["type"] == "av" else new_captions
                        if track["type"] == "captions" else deepcopy(track)
                        for track in existing_doc["tracks"]]
    if av is None:
        result["tracks"].append(new_av)
    if result != existing_doc:
        result["rev"] += 1
    return result


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "editing_script_duplicate_json_key")
        result[key] = value
    return result


def _read_workspace(root):
    root = Path(root).resolve()
    path = root / EDITING_SCRIPT
    _require(path.is_file(), "editing_script_missing_document")
    _require(path.resolve().is_relative_to(root), "editing_script_path_outside_workspace")
    index = root / "index.html"
    _require(index.resolve().is_relative_to(root), "editing_script_path_outside_workspace")
    try:
        _require(path.stat().st_size <= MAX_WORKSPACE_TEXT_BYTES
                 and index.stat().st_size <= MAX_WORKSPACE_TEXT_BYTES, "editing_script_workspace_too_large")
        html = index.read_text(encoding="utf-8")
        document = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError("invalid JSON number")))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        raise ValueError("editing_script_unreadable_workspace") from None
    return path, html, document


def _report(document, changed):
    av = next(track for track in document["tracks"] if track["type"] == "av")
    captions = next(track for track in document["tracks"] if track["type"] == "captions")
    return {"changed": changed, "files": [EDITING_SCRIPT] if changed else [],
            "av_clips": len(_playing(av)),
            "caption_words": sum(len(segment["words"]) for section in captions["items"]
                                 for segment in section["segments"])}


def validate_workspace(root):
    """Refuse an unsupported or stale workspace; never write while validating."""
    _, html, document = _read_workspace(root)
    result = synchronize(html, document)
    _require(result == document, "editing_script_out_of_sync")
    return _report(document, False)


def sync_workspace(root):
    """Atomically update only the EditingScript and return a count-only report."""
    path, html, document = _read_workspace(root)
    result = synchronize(html, document)
    changed = result != document
    if changed:
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                             prefix=".editing-script-", suffix=".tmp", delete=False) as output:
                temporary = Path(output.name)
                json.dump(result, output, ensure_ascii=False, indent=2, allow_nan=False)
                output.write("\n")
                output.flush()
                os.fsync(output.fileno())
            os.replace(str(temporary), str(path))
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
    return _report(result, changed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        report = validate_workspace(args.workspace) if args.check else sync_workspace(args.workspace)
    except ValueError as exc:
        print(json.dumps({"ok": False, "code": str(exc)}))
        return 1
    print(json.dumps({"ok": True, **report}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
