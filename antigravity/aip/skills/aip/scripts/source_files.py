"""The service's commit checks of a project cut from several videos, run offline.

A project whose editing script lists two or more videos in `sources` lands only when every
element holding a source second names its video and every speaker clip plays inside its own
video. The commit round refuses the rest element by element; preflight reports the same
refusals before upload, under the same rule names, codes and sentences:

- `multi_source_sources_header`: the tree plays or names more than one video, but the editing
  script has no valid `sources` list of two or more videos;
- `multi_source_clip_file`: a speaker clip whose `src` the list cannot place, or a speaker
  audio clip playing one video's voice under another video's picture;
- `multi_source_anchor_file`: an element with `data-src-anchor` and no `data-source-id`, or one
  naming a video the list does not hold;
- `source_range`: a speaker clip that plays outside its own video, by that video's length.

A path names a video by the shared rule (`source_id_of_media_path`, the cases in the
service's `source-media-paths.json`): its stem without `.mp4` and one `_full` equals that
video's listed path's stem, compared as whole paths. A tree cut from one video is never judged
here, so it is checked exactly as before. What only the service can read, such as the
project's own record of its videos, is still judged at commit.
"""

import json
import re

from editing_script_sync import EDITING_SCRIPT, RAW_AUDIO, _source_path, _source_stem, _sources


INDEX = "index.html"
SOURCES_HEADER_RULE = "multi_source_sources_header"
CLIP_FILE_RULE = "multi_source_clip_file"
ANCHOR_FILE_RULE = "multi_source_anchor_file"
SOURCE_RANGE_RULE = "source_range"
# A clip may end this far past its video's recorded length: the length is integer ms and a
# clip's in-point and length are written in seconds, so the two round apart by under one.
SOURCE_RANGE_TOLERANCE_S = 0.001
SPEAKER_CLIP = "speaker-clip"
# A later video's recorded voice, beside its proxy: `public/sources/<id>.mp3`.
LATER_VOICE = re.compile(r"^public/sources/([^/]+)\.mp3$")

HEADER_HINT = (
    "Keep the editing script's sources list as the project wrote it: one {id, path, duration} entry per "
    "video, the project's own upload first. Commit it with the index if the round changes either.")
CLIP_HINT = (
    "Point each speaker clip's src at one video's path from the editing script's sources list (the first "
    "video is public/source.mp4, a later one public/sources/<id>.mp4), and its audio twin at the same "
    "video's .mp3.")
ANCHOR_HINT = (
    'Give the element data-source-id="<id>" naming the video its data-src-anchor second is in, one of '
    "the ids in the editing script's sources list.")
RANGE_HINT = (
    "Keep each speaker clip inside its own video: data-media-start at 0 or later, and data-media-start "
    "plus data-duration at most that video's length (the editing script's sources list gives each "
    "video's duration in ms). To play another video, point src at its path and pick a range inside it.")


def source_id_of_media_path(src, sources):
    """The id of the `sources` entry whose path has `src`'s stem, or None when no entry has it,
    when two entries share it, or when `src` is not a source video."""
    stem = _source_stem(src)
    if not stem or not isinstance(sources, list):
        return None
    matches = [entry["id"] for entry in sources
               if isinstance(entry, dict) and isinstance(entry.get("id"), str) and entry["id"]
               and _source_stem(entry.get("path")) == stem]
    return matches[0] if len(matches) == 1 else None


def read_script(root):
    """The editing script as stored, or None when it is absent, unreadable or not an object."""
    try:
        loaded = json.loads((root / EDITING_SCRIPT).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    return loaded if isinstance(loaded, dict) else None


def _value(attrs, name, default=None):
    """An attribute's text as the service reads it: "" for one written without a value."""
    if name not in attrs:
        return default
    return "" if attrs[name] is None else attrs[name]


def _classes(attrs):
    return (_value(attrs, "class") or "").split()


def _number(attrs, name, default=None):
    raw = _value(attrs, name, default)
    try:
        return None if raw is None else float(raw)
    except ValueError:
        return None


def _speaker_clips(elements, tag):
    return [attrs for name, attrs, _ in elements
            if name == tag and SPEAKER_CLIP in _classes(attrs) and "data-hf-id" in attrs]


def _element_id(attrs):
    return _value(attrs, "id") or _value(attrs, "data-composition-id") or _value(attrs, "data-hf-id")


def _named(tag, attrs):
    ident = _element_id(attrs)
    return '<{} id="{}">'.format(tag, ident) if ident else "<{}>".format(tag)


def _occurrences(script):
    """The source records of the script's av track: its cut ledger's occurrences, or for a
    track that predates the ledger its playable items, either of which may name a video."""
    tracks = script.get("tracks") if script is not None else None
    for track in tracks if isinstance(tracks, list) else []:
        if not isinstance(track, dict) or track.get("type") != "av":
            continue
        if "canonicalCut" in track:
            cut = track["canonicalCut"]
            rows = cut.get("occurrences") if isinstance(cut, dict) else None
        else:
            items = track.get("items")
            rows = ([row for row in items if isinstance(row, dict) and "state" not in row]
                    if isinstance(items, list) else None)
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def is_multi_source(elements, script):
    """Whether the tree is cut from more than one video, as the service decides it: its speaker
    clips play two files, its editing script lists two videos, or its cut names a video."""
    played = set()
    for attrs in _speaker_clips(elements, "video"):
        start, duration = _number(attrs, "data-media-start", "0"), _number(attrs, "data-duration", "0")
        path = _source_path(_value(attrs, "src") or "")
        if start is not None and duration is not None and duration > 0 and path:
            played.add(path)
    listed = script.get("sources") if script is not None else None
    return (len(played) >= 2 or (isinstance(listed, list) and len(listed) >= 2)
            or any(row.get("sourceId") is not None for row in _occurrences(script)))


def _issue(path, rule, code, message, hint, **where):
    item = {"code": code, "rule": rule, "file": path}
    item.update((key, value) for key, value in where.items() if value is not None)
    item.update(message=message, repair_hint=hint)
    return item


def _voice_source_id(src, header):
    """The video whose recorded voice a speaker audio clip plays, or None for a voice that is
    not a video's own recording."""
    path = _source_path(src)
    if path in RAW_AUDIO:
        return str(header[0]["id"])
    match = LATER_VOICE.match(path)
    return None if match is None else source_id_of_media_path(
        "public/sources/{}.mp4".format(match.group(1)), header)


def _clip_issues(elements, header):
    issues, files = [], {}
    for attrs in _speaker_clips(elements, "video"):
        src = _value(attrs, "src") or ""
        source_id = source_id_of_media_path(src, header)
        if source_id is None:
            issues.append(_issue(
                INDEX, CLIP_FILE_RULE, "clip_file_unplaced",
                "Speaker clip {} plays {!r}, which is not the path of a video in the editing script's sources "
                "list, so the project cannot tell which video it plays.".format(_named("video", attrs), src),
                CLIP_HINT, element="video", element_id=_element_id(attrs), attribute="src", actual=src))
            continue
        files[_value(attrs, "data-hf-id")] = source_id
    for attrs in _speaker_clips(elements, "audio"):
        voice = _voice_source_id(_value(attrs, "src") or "", header)
        picture = files.get(_value(attrs, "data-hf-id"))
        if voice is None or picture is None or voice == picture:
            continue
        issues.append(_issue(
            INDEX, CLIP_FILE_RULE, "audio_twin_other_file",
            "Speaker audio clip {} plays the voice of video {!r} under the picture of video {!r}, so the "
            "sound would not match the speaker.".format(_named("audio", attrs), voice, picture),
            CLIP_HINT, element="audio", element_id=_element_id(attrs), attribute="src",
            expected=picture, actual=voice))
    return issues


def _anchor_issues(elements, ids):
    issues = []
    for tag, attrs, _ in elements:
        if "data-src-anchor" not in attrs or SPEAKER_CLIP in _classes(attrs):
            continue
        named = _value(attrs, "data-source-id")
        if named in ids:
            continue
        missing = not named
        message = ("{} holds a source second (data-src-anchor) but does not name the video it is in."
                   if missing else
                   "{} names video {!r}, which is not in the editing script's sources list.")
        issues.append(_issue(
            INDEX, ANCHOR_FILE_RULE, "anchor_file_missing" if missing else "anchor_file_unknown",
            message.format(_named(tag, attrs), named), ANCHOR_HINT, element=tag,
            element_id=_element_id(attrs), attribute="data-source-id", actual=named))
    return issues


def _range_issues(elements, header):
    lengths = {str(entry["id"]): float(str(entry["duration"])) / 1000.0 for entry in header}
    issues = []
    for attrs in _speaker_clips(elements, "video"):
        source_id = source_id_of_media_path(_value(attrs, "src") or "", header)
        start, duration = _number(attrs, "data-media-start"), _number(attrs, "data-duration")
        if source_id is None or start is None or duration is None:
            continue
        length, end = lengths[source_id], start + duration
        if start >= -SOURCE_RANGE_TOLERANCE_S and end <= length + SOURCE_RANGE_TOLERANCE_S:
            continue
        before = start < -SOURCE_RANGE_TOLERANCE_S
        tail = ("but a video starts at 0s." if before else
                "but that video is only {:.3f}s long, so the export has nothing to play past it.".format(length))
        issues.append(_issue(
            INDEX, SOURCE_RANGE_RULE, "clip_before_source_start" if before else "clip_past_source_end",
            "Speaker clip {} plays video {!r} from {:.3f}s to {:.3f}s, {}".format(
                _named("video", attrs), source_id, start, end, tail),
            RANGE_HINT, element="video", element_id=_element_id(attrs),
            attribute="data-media-start" if before else "data-duration",
            expected="0.000" if before else "{:.3f}".format(length),
            actual="{:.3f}".format(start) if before else "{:.3f}".format(end)))
    return issues


def issues(elements, script):
    """Every refusal the commit would give this tree's index and editing script for its several
    videos, in the commit's order, or none for a tree cut from one video. `elements` is the
    index's parsed tags as (tag, attributes, template depth), `script` the editing script."""
    if not is_multi_source(elements, script):
        return []
    header = _sources(script)
    if header is None:
        return [_issue(
            EDITING_SCRIPT if script is not None else INDEX, SOURCES_HEADER_RULE, "sources_header_missing",
            "This project is cut from more than one video, but the editing script has no sources list "
            "naming each video, so nothing says which video a clip or an anchor plays.",
            HEADER_HINT, expected="sources: two or more {id, path, duration} entries")]
    clips = _clip_issues(elements, header)
    anchors = _anchor_issues(elements, {str(entry["id"]) for entry in header})
    # A clip whose video is unknown has no length to measure; ranges wait until each clip names one.
    return clips + anchors + ([] if clips else _range_issues(elements, header))
