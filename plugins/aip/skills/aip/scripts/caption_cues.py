#!/usr/bin/env python3
"""Print the caption moments of the current cut, timed from the EditingScript.

Run on the render-engine workspace once the speaker cut is final and before any
caption moment is mounted. It first synchronizes compositions/editing-script.json
with index.html exactly as preflight --sync-editing-script does, then groups the
words the cut keeps into moments and cues:

- A moment never spans a speaker cut, a sentence end, a long pause or
  MAX_MOMENT_SECONDS, so a later cut between moments moves each one whole with
  its source anchor.
- A cue holds at most --max-words words and ends at a clause mark or a pause.

Times are seconds: a moment's start on the cut and its source anchor, and each
cue's and word's in and out from the moment's start.
"""

import argparse
import json
from pathlib import Path
import sys

from editing_script_sync import EDITING_SCRIPT, sync_workspace


DEFAULT_MAX_WORDS = 4
MAX_WORDS_LIMIT = 16
MAX_MOMENT_SECONDS = 8
# A pause longer than this ends the moment, so the caption is off while nobody speaks.
MOMENT_PAUSE_MS = 1000
# A cue stays up until the next one across a pause shorter than this, so the
# caption does not flicker between phrases; across a longer one it holds briefly.
CUE_JOIN_MS = 500
CUE_HOLD_MS = 200
SPAN_TOLERANCE_MS = 1
SENTENCE_END = tuple(".!?。！？…")
CLAUSE_END = tuple(",;:、，；：")
CLOSERS = "\"')]}”’」』）"


def _spans(document):
    av = next((track for track in document["tracks"] if track["type"] == "av"), None)
    clips = sorted((item for item in (av or {}).get("items", []) if item.get("state") is None),
                   key=lambda item: item["timelineIn"])
    spans = []
    for clip in clips:
        # A speaker split alone does not cut speech; adjacent spans share one clock.
        if spans and abs(clip["srcStart"] - spans[-1]["srcEnd"]) <= SPAN_TOLERANCE_MS:
            spans[-1]["srcEnd"], spans[-1]["timelineOut"] = clip["srcEnd"], clip["timelineOut"]
        else:
            spans.append({key: clip[key] for key in ("srcStart", "srcEnd", "timelineIn", "timelineOut")})
    return spans


def _words(document, spans):
    captions = next(track for track in document["tracks"] if track["type"] == "captions")
    kept = []
    for number, section in enumerate(captions["items"]):
        for segment in section["segments"]:
            for word in segment["words"]:
                if word.get("state") is not None or word["timelineOut"] <= word["timelineIn"]:
                    continue
                span = next((index for index, item in enumerate(spans)
                             if item["timelineIn"] <= word["timelineIn"] < item["timelineOut"]), None)
                if span is None:
                    continue
                kept.append({"text": word["text"], "in": word["timelineIn"], "out": word["timelineOut"],
                             "src": word["srcStart"], "span": span, "section": number})
    return sorted(kept, key=lambda word: word["in"])


def _ends(text, marks):
    return text.rstrip().rstrip(CLOSERS).endswith(marks)


def _group(words, max_words):
    moments = []
    for word in words:
        current = moments[-1] if moments else None
        previous = current[-1][-1] if current else None
        if (previous is None or word["span"] != previous["span"] or word["section"] != previous["section"]
                or _ends(previous["text"], SENTENCE_END) or word["in"] - previous["out"] > MOMENT_PAUSE_MS
                or word["out"] - current[0][0]["in"] > MAX_MOMENT_SECONDS * 1000):
            moments.append([[word]])
        elif (len(current[-1]) >= max_words or _ends(previous["text"], CLAUSE_END)
              or word["in"] - previous["out"] > CUE_JOIN_MS):
            current.append([word])
        else:
            current[-1].append(word)
    return moments


def _seconds(milliseconds):
    return round(milliseconds / 1000, 3)


def cue_moments(document, max_words=DEFAULT_MAX_WORDS):
    """Return the caption moments of a synchronized EditingScript."""
    spans = _spans(document)
    groups = _group(_words(document, spans), max_words)
    width = max(2, len(str(len(groups))))
    moments = []
    for number, cues in enumerate(groups):
        first = cues[0][0]
        span = spans[first["span"]]
        following = groups[number + 1][0][0]["in"] if number + 1 < len(groups) else span["timelineOut"]
        ceiling = min(following, span["timelineOut"])
        source = first["src"] if first["src"] is not None else span["srcStart"] + first["in"] - span["timelineIn"]
        timed = []
        for index, cue in enumerate(cues):
            last = cue[-1]["out"]
            upcoming = cues[index + 1][0]["in"] if index + 1 < len(cues) else None
            if upcoming is not None and upcoming - last <= CUE_JOIN_MS:
                out = upcoming
            else:
                # Never into the next moment, which shares the track.
                out = max(min(last + CUE_HOLD_MS, ceiling), cue[0]["in"] + 1)
            timed.append({"in": _seconds(cue[0]["in"] - first["in"]), "out": _seconds(out - first["in"]),
                          "words": [[word["text"], _seconds(word["in"] - first["in"]),
                                     _seconds(word["out"] - first["in"])] for word in cue]})
        identifier = "captions-{:0{}d}".format(number + 1, width)
        moments.append({"id": identifier, "src": "compositions/{}.html".format(identifier),
                        "start": _seconds(first["in"]), "duration": timed[-1]["out"],
                        "src_anchor": _seconds(source), "cues": timed})
    return moments


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("workspace", type=Path, help="the render-engine directory")
    parser.add_argument("--max-words", type=int, default=DEFAULT_MAX_WORDS,
                        help="most words a cue shows at once (default %(default)s)")
    args = parser.parse_args()
    if not 1 <= args.max_words <= MAX_WORDS_LIMIT:
        print(json.dumps({"ok": False, "code": "caption_cues_invalid_max_words"}))
        return 1
    try:
        report = sync_workspace(args.workspace)
        document = json.loads((args.workspace / EDITING_SCRIPT).read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        code = str(exc) if isinstance(exc, ValueError) and str(exc).startswith("editing_script_") else "editing_script_unreadable_workspace"
        print(json.dumps({"ok": False, "code": code}))
        return 1
    moments = cue_moments(document, args.max_words)
    print(json.dumps({"ok": True, "synced": report["changed"], "moments": moments},
                     ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
