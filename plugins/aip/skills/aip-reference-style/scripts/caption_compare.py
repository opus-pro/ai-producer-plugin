#!/usr/bin/env python3
"""The caption match's plumbing: installed fonts, a face specimen, and like-for-like comparison images.

usage:
  caption_compare.py fonts [<query>]
      Installed font files whose family or file name contains <query> (all of them without one): one line per
      face, "<file> #<index> <family> / <style>". Needs fontTools (run through `uv run --with fonttools python`).
  caption_compare.py specimen <out.png> <frame> --text "<words>" [--crop X,Y,W,H] [--size PX] <query> [<query> ...]
      The frame (cropped to the caption) above the words set in every installed face whose family or file name
      contains a query, one labeled row per face, so one image settles the faces and weights. Prints the rows'
      faces in order as "<n> <file> #<index> <family> / <style>". Needs fontTools, like `fonts`.
  caption_compare.py extract <font file> <index> <out.ttf>
      One face of a collection (.ttc / .otc) as its own file.
  caption_compare.py compare <out.png> <frame>=<page> [<frame>=<page> ...] [--crop X,Y,W,H] [--t SECONDS]
      Renders each page in headless Chrome at its frame's pixel size and sets it beside that frame, frame on the
      left; pairs stack top to bottom in one image. --crop keeps one region of both (fractions of the frame), at
      full resolution; --t is passed to every page as ?t=<seconds>. Pages load over HTTP from their own
      directory, so their relative fonts and images resolve.

It measures and draws nothing on its own: what to compare, and whether the two match, is the caller's call.
"""
import functools
import html
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

CHROME_PATHS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome", "chromium", "chromium-browser",
)
FONT_DIRS = ("/System/Library/Fonts", "/Library/Fonts", "~/Library/Fonts", "/usr/share/fonts", "~/.fonts",
             "~/.local/share/fonts", "C:/Windows/Fonts")
FONT_SUFFIXES = (".ttf", ".otf", ".ttc", ".otc")
SPECIMEN_MAX_FACES = 24
SPECIMEN_MIN_WIDTH = 900


def fail(message):
    print(f"caption_compare: {message}", file=sys.stderr)
    sys.exit(1)


def size_of(image):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "json", image], capture_output=True, text=True, check=True).stdout
    stream = json.loads(out)["streams"][0]
    return int(stream["width"]), int(stream["height"])


def faces(path):
    from fontTools.ttLib import TTCollection, TTFont
    if path.suffix.lower() in (".ttc", ".otc"):
        fonts = TTCollection(str(path), lazy=True).fonts
    else:
        fonts = [TTFont(str(path), lazy=True)]
    for index, font in enumerate(fonts):
        names = font["name"]
        family = names.getDebugName(16) or names.getDebugName(1) or "?"
        style = names.getDebugName(17) or names.getDebugName(2) or "?"
        yield index, family, style


def installed(queries):
    """(file, index, family, style) of every installed face whose family or file name contains one of the queries."""
    try:
        import fontTools  # noqa: F401
    except ImportError:
        fail("needs fontTools: run it through `uv run --with fonttools python caption_compare.py ...`")
    queries = [q.lower() for q in queries] or [""]
    for root in FONT_DIRS:
        base = Path(os.path.expanduser(root))
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.suffix.lower() not in FONT_SUFFIXES:
                continue
            try:
                for index, family, style in faces(path):
                    if any(q in family.lower() or q in path.name.lower() for q in queries):
                        yield path, index, family, style
            except Exception:  # noqa: BLE001 - an unreadable font file is skipped, not fatal
                continue


def fonts(args):
    for path, index, family, style in installed(args[:1]):
        print(f"{path} #{index} {family} / {style}")


def save_face(path, index, out):
    from fontTools.ttLib import TTCollection, TTFont
    font = TTCollection(str(path)).fonts[index] if path.suffix.lower() in (".ttc", ".otc") else TTFont(str(path))
    font.save(out)


def extract(args):
    if len(args) != 3:
        fail("extract <font file> <index> <out.ttf>")
    save_face(Path(args[0]), int(args[1]), args[2])
    print(args[2])


def chrome():
    for path in (os.environ.get("CHROME"),) + CHROME_PATHS:
        if path and (os.path.exists(path) or shutil.which(path)):
            return path
    fail("no Chrome or Chromium found; set CHROME to its path")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(directory):
    handler = functools.partial(QuietHandler, directory=directory)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def render(browser, page, width, height, out, t):
    server = serve(str(page.parent))
    try:
        url = f"http://127.0.0.1:{server.server_port}/{page.name}" + (f"?t={t}" if t is not None else "")
        base = [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                f"--window-size={width},{height}", "--virtual-time-budget=8000", f"--screenshot={out}"]
        for extra in ([], ["--single-process", "--no-zygote"]):
            subprocess.run(base + extra + [url], capture_output=True, timeout=120)
            if os.path.exists(out):
                return
        fail(f"Chrome rendered nothing for {page}; a sandbox that stops it may need CHROME set to another browser")
    finally:
        server.shutdown()


def split_options(args, names):
    """The --name values among args, and the other args in order."""
    options, rest = {}, []
    i = 0
    while i < len(args):
        if args[i] in names and i + 1 < len(args):
            options[args[i][2:]] = args[i + 1]
            i += 2
        else:
            rest.append(args[i])
            i += 1
    return options, rest


def crop_filter(crop, width, height):
    x, y, w, h = crop
    return f"crop={int(w * width)}:{int(h * height)}:{int(x * width)}:{int(y * height)}"


def specimen(args):
    options, rest = split_options(args, ("--text", "--crop", "--size"))
    if len(rest) < 3 or "text" not in options:
        fail('specimen <out.png> <frame> --text "<words>" [--crop X,Y,W,H] [--size PX] <query> [<query> ...]')
    out, frame, queries = rest[0], Path(rest[1]).resolve(), rest[2:]
    size = float(options.get("size", 72))
    found = list(installed(queries))
    if not found:
        fail(f"no installed face matches {', '.join(queries)}; `fonts` lists them all")
    if len(found) > SPECIMEN_MAX_FACES:
        print(f"{len(found)} faces match; showing the first {SPECIMEN_MAX_FACES}, narrow the query for the rest")
        found = found[:SPECIMEN_MAX_FACES]
    width, height = size_of(str(frame))
    crop = [float(x) for x in options["crop"].split(",")] if "crop" in options else [0, 0, 1, 1]
    crop_w = int(crop[2] * width)
    page_w = max(crop_w, SPECIMEN_MIN_WIDTH)
    row_h = int(size * 1.35) + 34
    work = tempfile.mkdtemp(prefix="caption-specimen-")
    try:
        rules, rows = [], []
        for n, (path, index, family, style) in enumerate(found):
            save_face(path, index, os.path.join(work, f"f{n}.ttf"))
            rules.append(f"@font-face{{font-family:f{n};src:url(f{n}.ttf)}}")
            rows.append(f'<div class="row"><div class="label">{n} {html.escape(path.name)} #{index} '
                        f'{html.escape(family)} / {html.escape(style)}</div>'
                        f'<div class="text" style="font-family:f{n}">{html.escape(options["text"])}</div></div>')
        page = Path(work) / "specimen.html"
        page.write_text(
            "<!doctype html><meta charset=utf-8><style>" + "".join(rules)
            + f"body{{margin:0;background:#3a3a3a;color:#fff}}.row{{height:{row_h}px;padding:0 12px;overflow:hidden}}"
            + ".label{font:24px/32px monospace;color:#ffd84d}"
            + f".text{{font-size:{size}px;line-height:{int(size * 1.3)}px;white-space:nowrap}}</style>" + "".join(rows),
            encoding="utf-8")
        shot = os.path.join(work, "specimen.png")
        render(chrome(), page, page_w, row_h * len(rows), shot, None)
        graph = (f"[0]{crop_filter(crop, width, height)},pad={page_w}:ih:0:0:black[a];[1]scale={page_w}:-2[b];"
                 "[a][b]vstack")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(frame), "-i", shot, "-filter_complex", graph,
                        "-frames:v", "1", out], check=True)
        for n, (path, index, family, style) in enumerate(found):
            print(f"{n} {path} #{index} {family} / {style}")
        w, h = size_of(out)
        print(f"{out} {w}x{h} (the frame on top, then one row per face)")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def compare(args):
    options, rest = split_options(args, ("--crop", "--t"))
    if len(rest) < 2:
        fail("compare <out.png> <frame>=<page> [...] [--crop X,Y,W,H] [--t SECONDS]")
    out = rest[0]
    crop = [float(x) for x in options["crop"].split(",")] if "crop" in options else None
    t = float(options["t"]) if "t" in options else None
    pairs = []
    for arg in rest[1:]:
        frame, _, page = arg.partition("=")
        if not page:
            fail(f"expected <frame>=<page>, got {arg}")
        pairs.append((Path(frame).resolve(), Path(page).resolve()))
    browser = chrome()
    work = tempfile.mkdtemp(prefix="caption-compare-")
    rows = []
    try:
        for n, (frame, page) in enumerate(pairs):
            width, height = size_of(str(frame))
            shot = os.path.join(work, f"page{n}.png")
            render(browser, page, width, height, shot, t)
            row = os.path.join(work, f"row{n}.png")
            if crop:
                region = crop_filter(crop, width, height)
                graph = f"[0]{region}[a];[1]scale={width}:{height},{region}[b];[a][b]hstack"
            else:
                graph = f"[1]scale={width}:{height}[b];[0][b]hstack"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(frame), "-i", shot, "-filter_complex", graph,
                            "-frames:v", "1", row], check=True)
            rows.append(row)
        if len(rows) == 1:
            shutil.copy(rows[0], out)
        else:
            widths = [size_of(r)[0] for r in rows]
            pads = [f"[{i}]pad={max(widths)}:ih[p{i}]" for i in range(len(rows))]
            graph = ";".join(pads) + ";" + "".join(f"[p{i}]" for i in range(len(rows))) + f"vstack=inputs={len(rows)}"
            subprocess.run(["ffmpeg", "-v", "error", "-y", *[arg for r in rows for arg in ("-i", r)], "-filter_complex",
                            graph, "-frames:v", "1", out], check=True)
        w, h = size_of(out)
        print(f"{out} {w}x{h} ({len(rows)} pair{'s' if len(rows) != 1 else ''}, frame left, page right)")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    commands = {"fonts": fonts, "specimen": specimen, "extract": extract, "compare": compare}
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print(__doc__.strip())
        sys.exit(len(sys.argv) >= 2 and sys.argv[1] not in ("-h", "--help"))
    commands[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
