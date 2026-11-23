#!/usr/bin/env python3
"""Synchronize a fetched EditingScript with the speaker cut in index.html, offline.

Only the AV and caption projections change. Unsupported media clocks or a mounted
caption renderer that would need rebaking are refused before any file is written.

A project cut from several videos (a valid `sources` list of two or more) is synced
file by file: each speaker clip's file is the video its `src` names, every bound and
order rule holds within that file, each AV clip records its file as `sourceId`, and a
caption word is placed only on its own file's clips. Seconds of two files never compare.
A single-video document is synced exactly as before.
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
# A source video's proxy is `<stem>.mp4` and its full-res file of record `<stem>_full.mp4`;
# its recorded voice is `<stem>.mp3` (the service's `source_media_stem` and `span_media_paths`).
SOURCE_VIDEO_EXTENSION = ".mp4"
FULL_RES_SUFFIX = "_full"
VOICE_EXTENSION = ".mp3"


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


def _source_path(value):
    """A media path as a whole, without a query, fragment, or leading `./` or `/`."""
    if not isinstance(value, str):
        return ""
    path = re.split(r"[?#]", value.strip(), maxsplit=1)[0]
    while path.startswith("./"):
        path = path[2:]
    return path.lstrip("/")


def _source_stem(value):
    """The stem a source video path shares with its other variant, or "" for a non-video."""
    path = _source_path(value)
    if not path.endswith(SOURCE_VIDEO_EXTENSION):
        return ""
    stem = path[:-len(SOURCE_VIDEO_EXTENSION)]
    return stem[:-len(FULL_RES_SUFFIX)] if stem.endswith(FULL_RES_SUFFIX) else stem


def _integral_ms(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value == int(value))


def _sources(doc):
    """The `sources` list of a project cut from several videos, or None.

    None for a document with no list, an invalid one, or one naming a single video: the
    service reads an invalid list as no list, and such a document syncs as one video,
    exactly as before.
    """
    value = doc.get("sources") if isinstance(doc, dict) else None
    if not isinstance(value, list) or len(value) < 2:
        return None
    ids = set()
    for entry in value:
        if not (isinstance(entry, dict) and set(entry) == {"id", "path", "duration"}
                and isinstance(entry["id"], str) and entry["id"] and isinstance(entry["path"], str)
                and _integral_ms(entry["duration"]) and entry["id"] not in ids):
            return None
        ids.add(entry["id"])
    return value


def _video_file(path, sources):
    """The id of the video a speaker video clip's `src` is a file of, matched by stem."""
    stem = _source_stem(path)
    matches = [entry["id"] for entry in sources if stem and _source_stem(entry["path"]) == stem]
    _require(len(matches) == 1, "editing_script_clip_file_unplaced")
    return matches[0]


def _voice_file(path, sources):
    """The id of the video whose recorded voice a speaker audio clip plays: the project's
    first video's `public/source.mp3` (or its isolated swap), else `<stem>.mp3` beside a
    later video's file."""
    if path in RAW_AUDIO:
        return sources[0]["id"]
    _require(path.endswith(VOICE_EXTENSION), "editing_script_clip_file_unplaced")
    return _video_file(path[:-len(VOICE_EXTENSION)] + SOURCE_VIDEO_EXTENSION, sources)


def _own_video_uri(uri, file, sources):
    """Whether an AV clip's `sourceUri` is a file of its own video: that video's listed path or
    the full-res file beside it, by the same stem rule. Another video's file, or any voice, is
    not: readers take an AV clip's `sourceUri` as the picture it plays."""
    stem = _source_stem(_local_path(uri))
    own = next(entry for entry in sources if entry["id"] == file)
    return bool(stem) and stem == _source_stem(own["path"])


def _source_duration(file, sources):
    return Decimal(int(next(entry["duration"] for entry in sources if entry["id"] == file)))


def _media_paths(sources):
    """Every media path a multi-source document may name: each video and its voice."""
    paths = set(RAW_AUDIO)
    for entry in sources:
        path = _source_path(entry["path"])
        paths.add(path)
        if path.endswith(SOURCE_VIDEO_EXTENSION):
            paths.add(path[:-len(SOURCE_VIDEO_EXTENSION)] + VOICE_EXTENSION)
    return paths


# Elements HTML never closes, so they never enclose a later element.
VOID_TAGS = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
                       "source", "track", "wbr"})
# The editor's soft delete: the element stays in the page, hidden, and plays nothing.
DELETED_ATTR = "data-aip-deleted"


class _Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []
        self.templates = 0
        # Open elements as (tag, is_stage, is_host), so a video knows whether it sits under
        # #stage and whether a visual host or a composition owns it, or a deleted element holds it.
        self.open = []
        self.root_videos = []

    def handle_starttag(self, tag, attrs):
        keys = [key for key, _ in attrs]
        _require(len(set(keys)) == len(keys), "editing_script_duplicate_attribute")
        if tag == "template":
            self.templates += 1
        if not self.templates:
            attrs = dict(attrs)
            self.elements.append((tag, attrs))
            if tag == "video" and self._in_stage_outside_hosts():
                self.root_videos.append(attrs)
        if tag not in VOID_TAGS:
            attrs = dict(attrs)
            self.open.append((tag, attrs.get("id") == "stage",
                              "visual-host" in (attrs.get("class") or "").split()
                              or "data-composition-src" in attrs or DELETED_ATTR in attrs))

    def _in_stage_outside_hosts(self):
        for _, is_stage, is_host in reversed(self.open):
            if is_stage:
                return True
            if is_host:
                return False
        return False

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "template":
            self.templates = max(0, self.templates - 1)
        for position in range(len(self.open) - 1, -1, -1):
            if self.open[position][0] == tag:
                del self.open[position:]
                break


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


def _speaker_cut(html, source, sources=None):
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
    lanes, files = {}, {}
    for tag in ("video", "audio"):
        key = "speaker" if tag == "video" else "speaker-audio"
        candidates = [attrs for item_tag, attrs in elements if item_tag == tag
                      and (attrs.get("id") == key
                           or "speaker-clip" in (attrs.get("class") or "").split())]
        _require(bool(candidates), "editing_script_missing_speaker_lane")
        _require(candidates[0].get("id") == key, "editing_script_speaker_order")
        ids = [attrs.get("id") for attrs in candidates]
        _require(all(ids) and len(set(ids)) == len(ids), "editing_script_duplicate_speaker_id")
        single = len(candidates) == 1 and "speaker-clip" not in candidates[0].get("class", "").split()
        lane, lane_files = [], []
        for attrs in candidates:
            _require(single or "speaker-clip" in (attrs.get("class") or "").split(),
                     "editing_script_ambiguous_speaker_lane")
            path = _local_path(attrs.get("src"))
            if sources is None:
                _require(path == video_path if tag == "video" else path in RAW_AUDIO,
                         "editing_script_unsupported_source")
            else:
                lane_files.append(_video_file(path, sources) if tag == "video" else _voice_file(path, sources))
            identifier = attrs.get("data-hf-id") or ("clip-0" if single else None)
            _require(isinstance(identifier, str) and bool(identifier),
                     "editing_script_missing_clip_id")
            lane.append((identifier,) + _timing(attrs, single))
        _require(len({row[0] for row in lane}) == len(lane), "editing_script_duplicate_clip_id")
        lanes[tag] = lane
        files[tag] = lane_files
    _require(len(lanes["video"]) == len(lanes["audio"]), "editing_script_av_lane_mismatch")
    for video, audio in zip(lanes["video"], lanes["audio"]):
        _require(video[0] == audio[0] and all(abs(a - b) <= TIMING_TOLERANCE_MS
                                            for a, b in zip(video[1:], audio[1:])),
                 "editing_script_av_lane_mismatch")
    if sources is not None:
        # A clip's voice is its picture's file: one video's sound under another's picture
        # would be cut on the wrong clock.
        _require(files["video"] == files["audio"], "editing_script_audio_other_file")
    cursor, raw_cursor = 0, Decimal(0)
    # Order and bounds hold within each file; on one video there is one file, `None`.
    previous_source_end = {}
    clips = []
    for position, (identifier, start, source_start, duration) in enumerate(lanes["video"]):
        file = None if sources is None else files["video"][position]
        limit = source["duration"] if sources is None else _source_duration(file, sources)
        _require(abs(start - raw_cursor) <= TIMING_TOLERANCE_MS, "editing_script_noncontiguous_output")
        _require(source_start + TIMING_TOLERANCE_MS >= previous_source_end.get(file, Decimal(0)),
                 "editing_script_unsupported_source_order")
        if limit is not None:
            _require(source_start + duration <= limit + TIMING_TOLERANCE_MS,
                     "editing_script_source_out_of_bounds")
        source_ms, duration_ms = _round_milliseconds(source_start), _round_milliseconds(duration)
        _require(duration_ms > 0, "editing_script_invalid_timing")
        # Validate raw boundaries before rounding. The service rounds each clip's
        # duration, then tiles those integer durations; fractional-frame cuts can
        # otherwise accumulate a false gap when comparing rounded DOM starts.
        clip = {"id": identifier}
        if file is not None:
            clip["sourceId"] = file
        clip.update({"srcStart": source_ms, "srcEnd": source_ms + duration_ms,
                     "timelineIn": cursor, "timelineOut": cursor + duration_ms})
        clips.append(clip)
        cursor += duration_ms
        raw_cursor += duration
        previous_source_end[file] = source_start + duration
    speaker_sources = {attrs.get("src") for tag, attrs in elements if tag == "video"
                       and (attrs.get("id") == "speaker" or "speaker-clip" in (attrs.get("class") or "").split())}
    # A stage longer than the voice is the length only when footage appended after the voice
    # runs to it, which is when the export plays that far.
    extended = (total > raw_cursor + TIMING_TOLERANCE_MS
                and _appended_footage_end(document.root_videos, speaker_sources) + TIMING_TOLERANCE_MS >= total)
    _require((abs(raw_cursor - total) <= TIMING_TOLERANCE_MS or extended) and total > 0,
             "editing_script_duration_mismatch")
    return clips, elements


def _is_recording_file(src):
    """Source #1's files sit directly in public/ (source.mp4, source_full.mp4, source_speaker1.mp4,
    ...). A later video's sit in public/sources/ and are footage like any other clip's file."""
    return src.startswith("public/source") and not src.startswith("public/sources/")


def _appended_footage_end(root_videos, speaker_sources):
    """The end of the last root footage clip, or 0: the service's appended-footage rule
    (a timed `<video class="clip">` under #stage, in no visual host or composition, that is
    neither the speaker nor source #1's recording, carries no `data-hf-id`, and was not deleted
    in the editor)."""
    end = Decimal(0)
    for attrs in root_videos:
        src = (attrs.get("src") or "").strip()
        if ("clip" not in (attrs.get("class") or "").split() or "data-hf-id" in attrs
                or DELETED_ATTR in attrs or not src or src in speaker_sources or _is_recording_file(src)):
            continue
        try:
            start = _decimal_milliseconds(attrs.get("data-start"))
            duration = _decimal_milliseconds(attrs.get("data-duration"))
        except ValueError:
            continue
        if start >= 0 and duration > 0:
            end = max(end, start + duration)
    return end


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
    sources = _sources(doc)
    # The media a caption word may name: the one source's clock, or on a project cut from
    # several videos each video and its voice. An AV clip's `sourceUri` is its picture, so on
    # several videos it must be its own video's file (`_own_video_uri`).
    av_media = {_local_path(source["path"])}
    word_media = RAW_AUDIO | (av_media if sources is None else _media_paths(sources))
    files = None if sources is None else {entry["id"] for entry in sources}
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
                if files is not None:
                    _require(item.get("sourceId") in files, "editing_script_record_file_unplaced")
                if item.get("sourceUri") and sources is None:
                    _require(_local_path(item["sourceUri"]) in av_media, "editing_script_unsupported_source")
                elif item.get("sourceUri"):
                    _require(_own_video_uri(item["sourceUri"], item["sourceId"], sources),
                             "editing_script_source_uri_other_file")
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
                            _require(_local_path(word["sourceUri"]) in word_media,
                                     "editing_script_unsupported_source")
                        if files is not None:
                            _require(word.get("sourceId") in files, "editing_script_record_file_unplaced")
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


def _geometry(items, multi):
    keys = ("id", "sourceId") + TIMES if multi else ("id",) + TIMES
    return [{key: item[key] for key in keys} for item in items]


def _file(item, multi):
    """A record's file on a project cut from several videos; `None` on one video, whatever
    the record carries, so a single-video document compares seconds alone, as before."""
    return item.get("sourceId") if multi else None


def _same_file(item, clip, multi):
    return _file(item, multi) == _file(clip, multi)


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


def _seam(file, source_time, clips, multi):
    """Where a cut-away instant of `file` lands on the output timeline: the start of the first
    kept clip of that file playing source at or after it, else the end of that file's last
    kept clip, else the end of the timeline. On one video every clip is the same file, so
    this is the first clip after the instant, else the timeline's end."""
    own = [clip for clip in clips if _file(clip, multi) == file]
    next_clip = next((clip for clip in own if clip["srcStart"] >= source_time), None)
    if next_clip is not None:
        return next_clip["timelineIn"]
    return own[-1]["timelineOut"] if own else clips[-1]["timelineOut"]


def _restore_window(item, clips, multi):
    start = _seam(_file(item, multi), item["srcStart"], clips, multi)
    return {"timelineIn": start, "timelineOut": start + item["srcEnd"] - item["srcStart"]}


def _sync_av(track, clips, multi=False):
    if track is None:
        track = {"id": AV_TRACK_ID, "type": "av", "speakerVolume": 1, "items": []}
    old = _playing(track)
    if _geometry(old, multi) == clips and not track.get("ledgerAhead"):
        return deepcopy(track)
    updated = deepcopy(track)
    updated.pop("ledgerAhead", None)
    playable = []
    for clip in clips:
        prior = next((item for item in old if item["id"] == clip["id"] and _same_file(item, clip, multi)
                      and item["srcStart"] == clip["srcStart"] and item["srcEnd"] == clip["srcEnd"]), None)
        value = deepcopy(prior) if prior else {}
        value.update(clip)
        if prior is None and len(clips) > 1:
            value["origin"] = {"kind": "split", "from": "av-source"}
        playable.append(value)
    carried = []
    for item in track["items"]:
        if item.get("state") is not None and not any(
                _same_file(item, clip, multi)
                and item["srcStart"] < clip["srcEnd"] and clip["srcStart"] < item["srcEnd"]
                for clip in clips):
            value = deepcopy(item)
            value.update(_restore_window(item, clips, multi))
            carried.append(value)
    removed = []
    occupied = {item["id"] for item in playable + carried}
    # Source that played before and does not now, within each file: seconds of two files
    # never subtract from each other.
    ranges = []
    for file in dict.fromkeys(_file(clip, multi) for clip in old):
        ranges.extend((file, start, end) for start, end in _subtract(
            [(clip["srcStart"], clip["srcEnd"]) for clip in old if _file(clip, multi) == file],
            [(clip["srcStart"], clip["srcEnd"]) for clip in clips if _file(clip, multi) == file]))
    for file, start, end in ranges:
        identifier = "cut-{}".format(start)
        suffix = 1
        while identifier in occupied:
            identifier = "cut-{}-{}".format(start, suffix)
            suffix += 1
        occupied.add(identifier)
        item = {"id": identifier}
        if file is not None:
            item["sourceId"] = file
        item.update({"srcStart": start, "srcEnd": end,
                     "state": "deleted", "stateReason": dict(REMOVAL_REASON),
                     "origin": {"kind": "split", "from": "av-source"}})
        item.update(_restore_window(item, clips, multi))
        removed.append(item)
    updated["items"] = playable + carried + removed
    return updated


def _covering(clips, source_time):
    return next((clip for clip in clips if clip["srcStart"] <= source_time < clip["srcEnd"]), None)


def _collapsed(clips, source_time):
    return max((clip["timelineOut"] for clip in clips if clip["srcStart"] < source_time), default=0)


def _segment_file(segment):
    """The one file a caption segment's words name on a project cut from several videos. A
    segment is phrased within one file, so one that names two cannot be placed."""
    files = {_file(word, True) for word in segment["words"]}
    _require(len(files) <= 1, "editing_script_segment_spans_files")
    return next(iter(files), None)


def _project_segment(segment, clips, multi=False):
    words = segment["words"]
    file = _segment_file(segment) if multi else None
    timeline = clips
    if multi:
        # A word is placed, and collapses, only on its own file's clips.
        clips = [clip for clip in clips if _file(clip, True) == file]
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
                start = end = (_seam(file, word["srcStart"], timeline, True) if multi
                               else _collapsed(clips, word["srcStart"]))
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


def _caption_spans(clips, multi):
    # A speaker split alone does not cut speech. Adjacent source/output spans
    # share one caption clock, including the service's millisecond rounding,
    # within one file.
    spans = []
    for clip in clips:
        if (spans and _same_file(clip, spans[-1], multi)
                and abs(clip["srcStart"] - spans[-1]["srcEnd"]) <= TIMING_TOLERANCE_MS):
            spans[-1]["srcEnd"] = clip["srcEnd"]
            spans[-1]["timelineOut"] = clip["timelineOut"]
        else:
            spans.append(dict(clip))
    return spans


def _in_output_order(sections):
    """Sections whose segments run in output order across the whole track, for a cut of
    several videos. Clips of one video can play around another's (A, then B, then A again), so
    a section's projected segments may sit on either side of another section's. Each section
    keeps one file and its own order; one interrupted by another section's segment is split
    there, the later part under a new id, so the document order is the output order and every
    neighbouring window is well formed."""
    taken = {section["id"] for section in sections}
    placed = sorted(((segment["timelineIn"], order, number, section, segment)
                     for order, section in enumerate(sections)
                     for number, segment in enumerate(section["segments"])),
                    key=lambda row: row[:3])
    result, current, parts = [], None, {}
    for _, order, _, section, segment in placed:
        if current is None or current[0] != order:
            part = parts.get(order, 0)
            parts[order] = part + 1
            identifier = section["id"]
            if part:
                identifier = "{}-{}".format(section["id"], part)
                while identifier in taken:
                    identifier += "-part"
                taken.add(identifier)
            fresh = dict(section, id=identifier, segments=[])
            result.append(fresh)
            current = (order, fresh)
        current[1]["segments"].append(segment)
    return result + [section for section in sections if not section["segments"]]


def _sync_captions(track, clips, multi=False):
    clips = _caption_spans(clips, multi)
    updated = deepcopy(track)
    for section in updated["items"]:
        section["segments"] = sorted((_project_segment(segment, clips, multi) for segment in section["segments"]),
                                     key=lambda segment: segment["timelineIn"])
    if multi:
        updated["items"] = _in_output_order(updated["items"])
    else:
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
                or "caption-word" in (attrs.get("class") or "").split()):
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
    sources = _sources(existing_doc)
    multi = sources is not None
    clips, elements = _speaker_cut(html, _source_clock(existing_doc), sources)
    av = next((track for track in existing_doc["tracks"] if track["type"] == "av"), None)
    captions = next(track for track in existing_doc["tracks"] if track["type"] == "captions")
    new_av = _sync_av(av, clips, multi)
    new_captions = _sync_captions(captions, clips, multi)
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
