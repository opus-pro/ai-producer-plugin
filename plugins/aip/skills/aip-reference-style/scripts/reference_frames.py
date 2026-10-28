#!/usr/bin/env python3
"""Turn a reference video, or a directory of reference images, into the stills a model reads its style from.

usage: reference_frames.py <reference video or image directory> <output directory>
       reference_frames.py <reference video> <output directory> --caption-kit <caption>:<clean>[,...]
                           --band <top>:<bottom> [--entry <seconds>]
       reference_frames.py <image directory> <output directory> --caption-kit <still>[:<still>][,...]
                           --band <top>:<bottom>
       reference_frames.py <reference video> <output directory> --visuals <seconds>[,...]

Needs ffmpeg and ffprobe on PATH. Writes contact sheets of the analyzed span, then per
beat a keyframe and a frame strip, transition pages that straddle every hard cut between
beats with each cut's kind (cut, flash or blur), and reference-index.json naming every file
with its times. A beat is the stretch
between two hard cuts; the cut threshold adapts to each video so a beat averages about
three seconds. A reference longer than MAX_ANALYZED_SECONDS is analyzed in windows: its
opening, then windows spread evenly over the rest, up to that budget.

--caption-kit writes caption-kit/ instead, the caption sample's whole input: for each pair of
contact-sheet times, a moment whose caption reads clearly and a moment of the same shot without
one, both at full resolution (caption-<seconds>.jpg, clean-<seconds>.jpg), and kit.jpg, which
sets their caption bands side by side, above the band frame by frame from --entry, the moment
just before a caption arrives. --band is the share of the frame height the captions sit in.

A directory of images (.jpg, .jpeg, .png, .webp, in name order) is a reference of stills: it
writes each image as stills/still-NN.jpg and reference-index.json naming them, with no beats,
cuts or transitions, which stills cannot show. Its --caption-kit names stills by number, a
still showing a caption and optionally a still of the same shot without one, each copied at
the image's own resolution, and kit.jpg sets their caption bands side by side with no entry row.

--visuals writes visuals/visual-<seconds>.jpg instead: the frame at each contact-sheet time at the
reference's own resolution, for reading one graphic's type, colour and layout in detail.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

MAX_ANALYZED_SECONDS = 90.0
OPENING_SECONDS = 15.0
WINDOW_SECONDS = 15.0

CANDIDATE_CUT_SCORE = 6.0
CUT_SCORE_LADDER = (30.0, 25.0, 20.0, 15.0, 12.0, 10.0, 8.0, 6.0)
TARGET_MEAN_BEAT_SECONDS = 3.0
MIN_BEAT_SECONDS = 0.4
MAX_BEAT_SECONDS = 6.0
CUT_DETECT_WIDTH = 360

SHEET_FPS = 2
SHEET_COLUMNS = 9
SHEET_ROWS = 6
SHEET_FRAME_WIDTH = 200
KEYFRAME_POSITION = 0.6
KEYFRAME_WIDTH = 540
STRIP_FPS = 4.0
STRIP_MAX_FRAMES = 20
STRIP_COLUMNS = 10
STRIP_FRAME_WIDTH = 180
TRANSITION_HALF_SECONDS = 0.33
TRANSITION_FPS = 12
TRANSITION_FRAMES = 8
TRANSITION_FRAME_WIDTH = 120
TRANSITION_ROWS_PER_PAGE = 6
# A boundary's kind is read from small gray frames across it: the frames nearest each edge
# are the two shots, the ones between them are the transition.
KIND_FRAME_SIZE = 64
KIND_EDGE_FRAMES = 2
# A flash: a frame between the shots brighter than both of them by this share of full white.
FLASH_RISE = 0.2
# A blur or whip: a frame between the shots keeping less than this share of their detail.
BLUR_KEEP = 0.5
KINDS = ("cut", "flash", "blur")
LABEL = "drawtext=text='%{{pts\\:hms}}':x=4:y=4:fontsize={size}:fontcolor=yellow:box=1:boxcolor=black@0.6"
NAME_LABEL = "drawtext=text='{text}':x=6:y=6:fontsize={size}:fontcolor=yellow:box=1:boxcolor=black@0.6"
# How a caption arrives: the band from --entry, at this rate, for this long, in one row.
KIT_ENTRY_FPS = 12
KIT_ENTRY_FRAMES = 6
KIT_GAP = 6
KIT_MAX_SIDE = 1568
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp")
# Images may differ in size, so each caption band in an image kit is set to one height.
KIT_IMAGE_BAND_HEIGHT = 360

SCDET_LINE = re.compile(r"lavfi\.scd\.score:\s*([0-9.]+),\s*lavfi\.scd\.time:\s*([0-9.]+)")


def run(args):
    return subprocess.run(args, capture_output=True, text=True, check=False)


def require_tools():
    missing = [tool for tool in ("ffmpeg", "ffprobe") if shutil.which(tool) is None]
    if missing:
        sys.exit(f"reference_frames: {' and '.join(missing)} not found on PATH; install ffmpeg and run again")


def probe_duration(video):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)])
    try:
        return float(out.stdout.strip())
    except ValueError:
        sys.exit(f"reference_frames: could not read the duration of {video}: {out.stderr.strip()[:300]}")


def detect_cuts(video):
    """Every scene change scdet scores at CANDIDATE_CUT_SCORE or above, as (seconds, score)."""
    filters = f"scale={CUT_DETECT_WIDTH}:-2,scdet=threshold={CANDIDATE_CUT_SCORE}:sc_pass=1"
    out = run(["ffmpeg", "-hide_banner", "-v", "info", "-i", str(video), "-an", "-sn", "-vf", filters, "-f", "null", "-"])
    return sorted((float(m.group(2)), float(m.group(1))) for m in SCDET_LINE.finditer(out.stderr))


def merge_spans(spans):
    merged = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def choose_windows(duration, budget=MAX_ANALYZED_SECONDS):
    """The spans to analyze: the whole video when it fits the budget, otherwise its opening and
    windows spread evenly over the rest. Even spacing keeps the sample's mix of quiet and busy
    stretches the reference's own, which the proportion of each treatment is read from; windows
    picked for their cutting would read a busy stretch as the whole."""
    if duration <= budget:
        return [(0.0, duration)]
    opening = min(OPENING_SECONDS, duration)
    count = int((budget - opening) // WINDOW_SECONDS)
    rest = duration - opening
    stride = rest / count
    windows = [(0.0, opening)]
    for i in range(count):
        middle = opening + stride * (i + 0.5)
        windows.append((max(opening, middle - WINDOW_SECONDS / 2), min(duration, middle + WINDOW_SECONDS / 2)))
    return merge_spans(windows)


def cut_rate(cuts, spans, min_score):
    """Cuts per minute at min_score or above inside the spans."""
    seconds = sum(e - b for b, e in spans)
    hits = sum(1 for t, score in cuts if score >= min_score and any(b <= t < e for b, e in spans))
    return round(60.0 * hits / seconds, 1) if seconds else 0.0


def boundaries(cuts, windows, min_score):
    """Cut times at or above min_score inside the windows, at least MIN_BEAT_SECONDS apart
    and from every window edge."""
    picked = []
    for start, end in windows:
        last = start
        for t, score in cuts:
            if score >= min_score and start + MIN_BEAT_SECONDS <= t <= end - MIN_BEAT_SECONDS and t - last >= MIN_BEAT_SECONDS:
                picked.append(t)
                last = t
    return picked


def pick_cut_score(cuts, windows):
    """The highest rung of the ladder whose cuts give beats averaging TARGET_MEAN_BEAT_SECONDS."""
    analyzed = sum(e - b for b, e in windows)
    for rung in CUT_SCORE_LADDER:
        beats = len(boundaries(cuts, windows, rung)) + len(windows)
        if analyzed / beats <= TARGET_MEAN_BEAT_SECONDS:
            return rung
    return CUT_SCORE_LADDER[-1]


def split_long(start, end):
    pieces = max(1, math.ceil((end - start) / MAX_BEAT_SECONDS))
    step = (end - start) / pieces
    return [(start + i * step, start + (i + 1) * step) for i in range(pieces)]


def make_beats(cuts, windows, min_score):
    cut_times = boundaries(cuts, windows, min_score)
    beats = []
    for start, end in windows:
        edges = [start, *[t for t in cut_times if start < t < end], end]
        for a, b in zip(edges, edges[1:]):
            for i, (x, y) in enumerate(split_long(a, b)):
                # `cut`: the beat opens on a hard cut, not on a window edge or a split of a long shot.
                beats.append({"n": len(beats) + 1, "t": [round(x, 2), round(y, 2)], "cut": i == 0 and a != start})
    return beats


def has_drawtext():
    return " drawtext " in run(["ffmpeg", "-hide_banner", "-filters"]).stdout


def frame_chain(fps, width, offset, label, size):
    chain = [f"fps={fps}", f"scale={width}:-2", f"setpts=PTS-STARTPTS+{offset}/TB"]
    if label:
        chain.append(LABEL.format(size=size))
    return chain


def render(video, start, duration, chain, out_pattern, frames=None):
    args = ["ffmpeg", "-hide_banner", "-v", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{duration:.3f}", "-i", str(video),
            "-vf", ",".join(chain), "-fps_mode", "vfr", "-q:v", "3"]
    if frames:
        args += ["-frames:v", str(frames)]
    out = run([*args, str(out_pattern)])
    if out.returncode != 0:
        raise RuntimeError(f"ffmpeg failed for {out_pattern}: {out.stderr.strip()[:300]}")


def contact_sheets(video, windows, out, label):
    names = []
    with tempfile.TemporaryDirectory() as tmp:
        for w, (start, end) in enumerate(windows):
            chain = frame_chain(SHEET_FPS, SHEET_FRAME_WIDTH, start, label, 14)
            chain.append(f"tile={SHEET_COLUMNS}x{SHEET_ROWS}:padding=4:color=white")
            render(video, start, end - start, chain, Path(tmp) / f"w{w:02d}-%03d.jpg")
        for i, page in enumerate(sorted(Path(tmp).glob("w*.jpg")), 1):
            name = f"contact-sheet-{i:02d}.jpg"
            shutil.move(str(page), out / name)
            names.append(name)
    return names


def beat_jobs(video, beat, out, label):
    start, end = beat["t"]
    span = end - start
    n = beat["n"]
    keyframe = out / "keyframes" / f"beat-{n:02d}.jpg"
    strip = out / "strips" / f"beat-{n:02d}.jpg"
    fps = min(STRIP_FPS, STRIP_MAX_FRAMES / max(span, 0.01))
    frames = max(1, math.ceil(span * fps))
    strip_chain = frame_chain(f"{fps:.4f}", STRIP_FRAME_WIDTH, start, label, 13)
    strip_chain.append(f"tile={min(frames, STRIP_COLUMNS)}x{math.ceil(frames / STRIP_COLUMNS)}:padding=3:color=white")
    key_at = start + span * KEYFRAME_POSITION
    beat.update({"keyframe": f"keyframes/{keyframe.name}", "strip": f"strips/{strip.name}"})
    return [
        (video, key_at, 0.2, [f"scale={KEYFRAME_WIDTH}:-2"], keyframe, 1),
        (video, start, span, strip_chain, strip, 1),
    ]


def transition_rows(video, beats, windows, rows_dir, label):
    """One row job per hard cut inside a window, straddling it. A boundary that only splits a long
    shot is no transition, so it gets no row."""
    jobs, times = [], []
    for prev, beat in zip(beats, beats[1:]):
        t = beat["t"][0]
        if not beat.get("cut") or prev["t"][1] != t or not any(b < t < e for b, e in windows):
            continue
        start = max(0.0, t - TRANSITION_HALF_SECONDS)
        chain = frame_chain(TRANSITION_FPS, TRANSITION_FRAME_WIDTH, start, label, 11)
        chain.append(f"tile={TRANSITION_FRAMES}x1:padding=3:color=white")
        jobs.append((video, start, 2 * TRANSITION_HALF_SECONDS, chain, rows_dir / f"row-{len(times):03d}.jpg", 1))
        times.append(round(t, 2))
    return jobs, times


def frame_stats(gray, size=KIND_FRAME_SIZE):
    """(brightness, detail) of one square gray frame, each 0 to 1: its mean level and its mean
    step between horizontal neighbours."""
    brightness = sum(gray) / (255 * len(gray))
    steps = sum(abs(a - b) for row in range(size) for a, b in zip(gray[row * size:(row + 1) * size - 1],
                                                                   gray[row * size + 1:(row + 1) * size]))
    return brightness, steps / (255 * size * (size - 1))


def classify(stats):
    """`flash`, `blur` or `cut` for the (brightness, detail) of the frames straddling a boundary."""
    if len(stats) < 2 * KIND_EDGE_FRAMES + 1:
        return "cut"
    half = len(stats) // 2
    sides = (stats[:KIND_EDGE_FRAMES], stats[-KIND_EDGE_FRAMES:])
    middles = (stats[KIND_EDGE_FRAMES:half], stats[half:-KIND_EDGE_FRAMES])
    side_brightness = max(sum(b for b, _ in side) / len(side) for side in sides)
    if max(b for middle in middles for b, _ in middle) - side_brightness >= FLASH_RISE:
        return "flash"
    # A whip or blur smears both shots where they meet. Content fading in on one side alone
    # also loses detail there, and is no blur transition.
    if all(middle and min(d for _, d in middle) < BLUR_KEEP * sum(d for _, d in side) / len(side)
           for middle, side in zip(middles, sides)):
        return "blur"
    return "cut"


def boundary_kind(video, t):
    start = max(0.0, t - TRANSITION_HALF_SECONDS)
    size = KIND_FRAME_SIZE
    out = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{2 * TRANSITION_HALF_SECONDS:.3f}",
                          "-i", str(video), "-vf", f"fps={TRANSITION_FPS},scale={size}:{size},format=gray",
                          "-frames:v", str(TRANSITION_FRAMES), "-f", "rawvideo", "-"], capture_output=True, check=False)
    frames = [out.stdout[i:i + size * size] for i in range(0, len(out.stdout) - size * size + 1, size * size)]
    return classify([frame_stats(frame) for frame in frames])


def boundary_kinds(video, times):
    with concurrent.futures.ThreadPoolExecutor(max(2, min(8, os.cpu_count() or 2))) as pool:
        return list(pool.map(lambda t: boundary_kind(video, t), times))


def stack_transition_pages(rows_dir, times, kinds, out):
    pages = []
    if not times:
        return pages
    pattern = rows_dir / "row-%03d.jpg"
    result = run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", str(pattern), "-vf",
                  f"tile=1x{TRANSITION_ROWS_PER_PAGE}:padding=4:color=white", "-fps_mode", "vfr", "-q:v", "3",
                  str(out / "transitions-%02d.jpg")])
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed stacking transition rows: {result.stderr.strip()[:300]}")
    for i in range(math.ceil(len(times) / TRANSITION_ROWS_PER_PAGE)):
        rows = slice(i * TRANSITION_ROWS_PER_PAGE, (i + 1) * TRANSITION_ROWS_PER_PAGE)
        pages.append({"file": f"transitions-{i + 1:02d}.jpg",
                      "boundaries": [{"t": t, "kind": kind} for t, kind in zip(times[rows], kinds[rows])]})
    return pages


def run_jobs(jobs):
    workers = max(2, min(8, os.cpu_count() or 2))
    with concurrent.futures.ThreadPoolExecutor(workers) as pool:
        for future in [pool.submit(render, *job) for job in jobs]:
            future.result()


def build(video, out):
    require_tools()
    out.mkdir(parents=True, exist_ok=True)
    for sub in ("keyframes", "strips"):
        (out / sub).mkdir(exist_ok=True)
    duration = probe_duration(video)
    cuts = detect_cuts(video)
    windows = choose_windows(duration)
    score = pick_cut_score(cuts, windows)
    beats = make_beats(cuts, windows, score)
    label = has_drawtext()
    sheets = contact_sheets(video, windows, out, label)
    jobs = [job for beat in beats for job in beat_jobs(video, beat, out, label)]
    with tempfile.TemporaryDirectory() as tmp:
        rows, times = transition_rows(video, beats, windows, Path(tmp), label)
        run_jobs(jobs + rows)
        kinds = boundary_kinds(video, times)
        pages = stack_transition_pages(Path(tmp), times, kinds, out)
    index = {
        "source": Path(video).name,
        "duration": round(duration, 2),
        "analyzed": [[round(a, 2), round(b, 2)] for a, b in windows],
        "partial": duration > MAX_ANALYZED_SECONDS,
        # Hard cuts a minute, over the whole reference and over the analyzed windows.
        "cuts_per_minute": {"whole": cut_rate(cuts, [(0.0, duration)], score), "analyzed": cut_rate(cuts, windows, score)},
        "labels": "time" if label else "none",
        "contact_sheets": sheets,
        "transition_pages": pages,
        "transition_kinds": {kind: kinds.count(kind) for kind in KINDS},
        "beats": beats,
    }
    (out / "reference-index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return index


def frame_size(path):
    out = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0",
               str(path)])
    width, height = out.stdout.strip().split(",")[:2]
    return int(width), int(height)


def ffmpeg(args, what):
    out = run(["ffmpeg", "-hide_banner", "-v", "error", "-y", *args])
    if out.returncode != 0:
        raise RuntimeError(f"ffmpeg failed for {what}: {out.stderr.strip()[:300]}")


def caption_kit(video, out, pairs, band, entry=None):
    """The caption sample's input: each pair's frames at full resolution, and kit.jpg showing their caption bands."""
    require_tools()
    kit = out / "caption-kit"
    kit.mkdir(parents=True, exist_ok=True)
    top, bottom = band
    crop = f"crop=iw:trunc(ih*{bottom - top:.4f}/2)*2:0:trunc(ih*{top:.4f}/2)*2"
    label = has_drawtext()
    files = []
    with tempfile.TemporaryDirectory() as tmp:
        rows = []
        for i, (caption, clean) in enumerate(pairs):
            pair = []
            for kind, t in (("caption", caption), ("clean", clean)):
                path = kit / f"{kind}-{t:.2f}.jpg"
                ffmpeg(["-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1", "-q:v", "2", str(path)], path.name)
                pair.append(path)
                files.append(path.name)
            names = [NAME_LABEL.format(text=f"{p.stem}", size=22) if label else "null" for p in pair]
            graph = f"[0]{crop},{names[0]}[a];[1]{crop},{names[1]}[b];[a][b]hstack=inputs=2:shortest=1"
            rows.append(Path(tmp) / f"row-{i}.png")
            ffmpeg(["-i", str(pair[0]), "-i", str(pair[1]), "-filter_complex", graph, "-frames:v", "1", str(rows[-1])], "a kit row")
        width, _ = frame_size(rows[0])
        if entry is not None:
            chain = [f"fps={KIT_ENTRY_FPS}", crop, f"scale={width // KIT_ENTRY_FRAMES // 2 * 2}:-2",
                     f"setpts=PTS-STARTPTS+{entry}/TB"]
            if label:
                chain.append(LABEL.format(size=13))
            chain.append(f"tile={KIT_ENTRY_FRAMES}x1")
            rows.append(Path(tmp) / "entry.png")
            render(video, entry, KIT_ENTRY_FRAMES / KIT_ENTRY_FPS, chain, rows[-1], 1)
        stack_kit(rows, Path(tmp), kit)
    return {"kit": "caption-kit/kit.jpg", "frames": [f"caption-kit/{name}" for name in files],
            "size": list(frame_size(kit / files[0]))}


def stack_kit(rows, tmp, kit):
    """kit.jpg: the kit's rows one under another, padded to the widest."""
    width = max(frame_size(row)[0] for row in rows)
    pads = "".join(f"[{i}]pad={width}:ih+{KIT_GAP}:0:0:white[p{i}];" for i in range(len(rows)))
    stack = "".join(f"[p{i}]" for i in range(len(rows))) + f"vstack=inputs={len(rows)}"
    stacked = tmp / "stacked.png"
    ffmpeg([*[arg for row in rows for arg in ("-i", str(row))], "-filter_complex", pads + stack, "-frames:v", "1", str(stacked)],
           "kit.jpg")
    # One read shows the whole kit: a reader shrinks a larger image anyway, and the frames hold the full resolution.
    scale = min(1.0, KIT_MAX_SIDE / max(frame_size(stacked)))
    ffmpeg(["-i", str(stacked), "-vf", f"scale=trunc(iw*{scale:.4f}/2)*2:-2", "-q:v", "2", str(kit / "kit.jpg")], "kit.jpg")


def visual_frames(video, out, times):
    """Each time's frame at the reference's own resolution, for the detail a graphic's keyframe and strip are too small for."""
    require_tools()
    (out / "visuals").mkdir(parents=True, exist_ok=True)
    names = []
    for t in times:
        name = f"visuals/visual-{t:.2f}.jpg"
        ffmpeg(["-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1", "-q:v", "2", str(out / name)], name)
        names.append(name)
    return {"visuals": names}


def reference_images(reference):
    """The images a reference directory holds, in name order; None when the reference is a video."""
    if not reference.is_dir():
        return None
    images = sorted(path for path in reference.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES)
    if not images:
        sys.exit(f"reference_frames: {reference} holds no {', '.join(IMAGE_SUFFIXES)} image")
    return images


def build_images(images, out):
    """A reference of stills: each image at the keyframes' width, numbered in order, and the index naming them."""
    require_tools()
    (out / "stills").mkdir(parents=True, exist_ok=True)
    stills = []
    for number, image in enumerate(images, 1):
        name = f"stills/still-{number:02d}.jpg"
        ffmpeg(["-i", str(image), "-vf", f"scale='min({KEYFRAME_WIDTH},iw)':-2", "-frames:v", "1", "-q:v", "2", str(out / name)],
               name)
        stills.append({"still": number, "file": name, "image": image.name, "size": list(frame_size(image))})
    index = {"source": images[0].parent.name, "kind": "images", "stills": stills}
    (out / "reference-index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return index


def image_caption_kit(images, out, pairs, band):
    """The caption kit of a reference of stills: each pair's stills at their own resolution, and kit.jpg showing their
    caption bands. A still shows no caption arriving, so the kit has no entry row."""
    require_tools()
    kit = out / "caption-kit"
    kit.mkdir(parents=True, exist_ok=True)
    top, bottom = band
    crop = f"crop=iw:trunc(ih*{bottom - top:.4f}/2)*2:0:trunc(ih*{top:.4f}/2)*2,scale=-2:{KIT_IMAGE_BAND_HEIGHT}"
    label = has_drawtext()
    files = []
    with tempfile.TemporaryDirectory() as tmp:
        rows = []
        for i, (caption, clean) in enumerate(pairs):
            pair = []
            for kind, number in (("caption", caption), ("clean", clean)):
                if number is None:
                    continue
                if not 1 <= number <= len(images):
                    sys.exit(f"reference_frames: there is no still {number}; the reference has {len(images)}")
                path = kit / f"{kind}-{number:02d}.jpg"
                ffmpeg(["-i", str(images[number - 1]), "-frames:v", "1", "-q:v", "2", str(path)], path.name)
                pair.append(path)
                files.append(path.name)
            bands = [f"[{j}]{crop}" + (f",{NAME_LABEL.format(text=path.stem, size=22)}" if label else "") for j, path in enumerate(pair)]
            graph = bands[0] if len(pair) == 1 else f"{bands[0]}[a];{bands[1]}[b];[a][b]hstack=inputs=2"
            rows.append(Path(tmp) / f"row-{i}.png")
            ffmpeg([*[arg for path in pair for arg in ("-i", str(path))], "-filter_complex", graph, "-frames:v", "1", str(rows[-1])],
                   "a kit row")
        stack_kit(rows, Path(tmp), kit)
    return {"kit": "caption-kit/kit.jpg", "frames": [f"caption-kit/{name}" for name in files]}


def still_pair(text):
    caption, _, clean = text.partition(":")
    return int(caption), None if clean in ("", "-") else int(clean)


def seconds_pair(text):
    caption, _, clean = text.partition(":")
    return float(caption), float(clean)


def main(argv):
    parser = argparse.ArgumentParser(usage=__doc__.split("\n\n")[1].removeprefix("usage: "))
    parser.add_argument("reference", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--caption-kit", type=lambda s: [p for p in s.split(",") if p])
    parser.add_argument("--band", type=seconds_pair)
    parser.add_argument("--entry", type=float)
    parser.add_argument("--visuals", type=lambda s: [float(t) for t in s.split(",") if t])
    args = parser.parse_args(argv[1:])
    images = reference_images(args.reference)
    if args.visuals:
        if images is not None:
            parser.error("--visuals needs a video: a reference of stills is read at its own resolution already")
        print(json.dumps(visual_frames(args.reference, args.out, args.visuals)))
        return
    if args.caption_kit and not args.band:
        parser.error("--caption-kit needs --band <top>:<bottom>")
    if images is not None:
        if args.entry is not None:
            parser.error("--entry needs a video: stills show no caption arriving")
        if args.caption_kit:
            try:
                pairs = [still_pair(p) for p in args.caption_kit]
            except ValueError:
                parser.error("--caption-kit names stills by number: <still>[:<still>],...")
            print(json.dumps(image_caption_kit(images, args.out, pairs, args.band)))
            return
        index = build_images(images, args.out)
        print(json.dumps({"stills": len(index["stills"])}))
        return
    if args.caption_kit:
        pairs = [seconds_pair(p) for p in args.caption_kit]
        print(json.dumps(caption_kit(args.reference, args.out, pairs, args.band, args.entry)))
        return
    index = build(args.reference, args.out)
    print(json.dumps({"beats": len(index["beats"]), "analyzed": index["analyzed"], "partial": index["partial"],
                      "contact_sheets": len(index["contact_sheets"]), "transition_pages": len(index["transition_pages"])}))


if __name__ == "__main__":
    main(sys.argv)
