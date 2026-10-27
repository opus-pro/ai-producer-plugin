#!/usr/bin/env python3
"""Download the video of a reference post (YouTube, TikTok, Instagram or any site yt-dlp reads).

usage: fetch_reference.py <post url> <output directory> [--browser auto|firefox|chrome]

Without --browser it never touches the browser: it fetches the post signed out, with the yt-dlp
release this plugin pins and its JavaScript challenge solver, and writes <output directory>/reference.<ext>,
the video only, at no more than 1080p (the smallest video when nothing at 1080p or below exists),
and never more than its first ten minutes. When the platform answers with a sign-in or bot wall it
stops with status sign_in_required, the browsers it could borrow a sign-in from, and the gated ones
among them: a browser whose cookie key the operating system guards behind its own prompt, which is
Chrome on macOS and its Keychain window. The user's answer to that window is their consent.

With --browser it borrows that browser's sign-in for this one site: auto uses only gated browsers;
any other browser is named, and only after the user agreed to it. Only YouTube, TikTok and
Instagram links borrow a sign-in, because only for them is the site's cookie domain known exactly.
The browser's cookies are read once, offline, by a pinned yt-dlp release that is given no URL and so
makes no request, into a private temporary directory; they are cut down to the post's own domain
before any downloader touches the network, reused for every request of the run, and deleted when
the run ends, whatever its outcome. They are never printed, logged or written anywhere else.

Prints one JSON object:
  {"status": "ok", "path": ..., "duration": seconds or null, "cookies": "none" | "firefox" | "chrome"}
  {"status": "sign_in_required", "browsers": [...], "gated": [...]}   rerun with --browser
  {"status": "unavailable", "detail": ...}                    private, removed or blocked where you are
  {"status": "no_downloader"}                                 install uv, then rerun
  {"status": "failed", "detail": ...}

DEBT: this local download, and the browser sign-in it borrows, stays until the import service fetches
reference links server-side; the plugin then drops this script.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

# Every yt-dlp run uses this reviewed release, so the plugin never fetches and runs code nobody pinned.
# The platforms change often: raise it, with the solver pin its `default` extra names, every plugin release.
YT_DLP_RELEASE = "2026.10.26"
YT_DLP_EJS_RELEASE = "0.8.0"
# The only process that sees the whole browser jar, run with no URL, so it reads the browser and writes
# the jar on exit without a request.
COOKIE_READER = ["uvx", "--from", f"yt-dlp=={YT_DLP_RELEASE}", "yt-dlp", "--ignore-config"]
FORMAT = "bv*[height<=1080]/b[height<=1080]/wv*/w"
MAX_SECONDS = 600
PROBE_TIMEOUT_SECONDS = 240
DOWNLOAD_TIMEOUT_SECONDS = 1200
DETAIL_CHARS = 600

# Lower-cased stderr fragments. Unavailable is read before sign-in: "Private video. Sign in if
# you've been granted access" is a private post, not a wall a borrowed sign-in opens.
UNAVAILABLE = (
    "private video", "this video is private", "video unavailable", "has been removed",
    "may have been removed", "not available in your country", "geo restrict", "geo-restrict",
    "http error 404", "does not exist", "account is private", "ip address is blocked",
)
SIGN_IN = (
    "sign in to confirm", "not a bot", "login required", "log in to", "use --cookies",
    "--cookies-from-browser", "cookies for the authentication", "age-restricted", "confirm your age",
    "inappropriate for some users", "isn't available to everyone", "requires authentication",
)

# The platforms a borrowed sign-in may be used for, with the cookie domain each keeps. Any other site
# downloads signed out only: a domain guessed from a hostname can be a public suffix (co.uk) and
# would carry other sites' cookies along.
SITE_DOMAINS = {
    "youtube.com": ("youtube.com",), "youtu.be": ("youtube.com",),
    "tiktok.com": ("tiktok.com",),
    "instagram.com": ("instagram.com",), "instagr.am": ("instagram.com",),
}


def run(cmd, timeout):
    """One command, its exit code and text output; a timeout reads as a failure, never an exception."""
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        return done.returncode, done.stdout, done.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {timeout} s"


def downloader():
    """The yt-dlp command to run: the pinned release through uvx with the challenge solver beside it."""
    # Without the solver YouTube offers only storyboard images, so no other launcher stands in for uvx.
    if shutil.which("uvx"):
        return ["uvx", "--with", f"yt-dlp-ejs=={YT_DLP_EJS_RELEASE}", "--from", f"yt-dlp=={YT_DLP_RELEASE}", "yt-dlp"]
    return None


def js_runtime_args():
    # yt-dlp enables only deno by default; YouTube's challenge needs some runtime.
    if shutil.which("deno"):
        return []
    for name in ("node", "bun"):
        if shutil.which(name):
            return ["--js-runtimes", name]
    return []


def classify(stderr):
    text = stderr.lower()
    if any(fragment in text for fragment in UNAVAILABLE):
        return "unavailable"
    if any(fragment in text for fragment in SIGN_IN):
        return "sign_in_required"
    return "failed"


def site_domains(url):
    host = (urlparse(url).hostname or "").lower()
    for suffix, domains in SITE_DOMAINS.items():
        if host == suffix or host.endswith("." + suffix):
            return domains
    return None


def filter_jar(text, domains):
    """Keep the Netscape jar's header and only the cookies of these domains and their subdomains."""
    kept = []
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.startswith("#") and not line.startswith("#HttpOnly_"):
            kept.append(line)
            continue
        domain = line.split("\t", 1)[0]
        if domain.startswith("#HttpOnly_"):
            domain = domain[len("#HttpOnly_"):]
        domain = domain.lstrip(".").lower()
        if any(domain == d or domain.endswith("." + d) for d in domains):
            kept.append(line)
    return "\n".join(kept) + "\n"


def browser_profiles():
    """The browsers on this machine that hold a profile, Firefox first: it opens without a prompt."""
    home = Path.home()
    appdata = Path(os.environ.get("APPDATA", home / "AppData/Roaming"))
    local = Path(os.environ.get("LOCALAPPDATA", home / "AppData/Local"))
    places = {
        "firefox": (home / "Library/Application Support/Firefox/Profiles", home / ".mozilla/firefox",
                    home / "snap/firefox/common/.mozilla/firefox", appdata / "Mozilla/Firefox/Profiles"),
        "chrome": (home / "Library/Application Support/Google/Chrome", home / ".config/google-chrome",
                   local / "Google/Chrome/User Data"),
    }
    return [name for name, paths in places.items() if any(p.is_dir() for p in paths)]


def gated(browsers):
    """The browsers whose cookie key sits behind the operating system's own consent prompt."""
    return [name for name in browsers if name == "chrome" and sys.platform == "darwin"]


def detail(stderr):
    lines = [line for line in stderr.splitlines() if "ERROR" in line] or stderr.splitlines()[-3:]
    return "\n".join(lines)[-DETAIL_CHARS:]


def probe(base, url, cookie_args):
    """Resolve the post and its 1080p format without downloading; returns (code, duration, stderr)."""
    code, out, err = run(base + cookie_args + ["--simulate", "-f", FORMAT, "--print", "duration", url],
                         PROBE_TIMEOUT_SECONDS)
    duration = None
    if code == 0:
        try:
            duration = float(out.strip().splitlines()[-1])
        except (ValueError, IndexError):
            duration = None
    return code, duration, err


def download(base, url, out_dir, cookie_args, duration):
    cmd = base + cookie_args + ["-f", FORMAT, "-o", str(out_dir / "reference.%(ext)s"),
                                "--print", "after_move:filepath", "--no-simulate"]
    # A post whose length is unknown is bounded too; a known short one downloads whole and fast.
    if duration is None or duration > MAX_SECONDS:
        cmd += ["--download-sections", f"*0-{MAX_SECONDS}"]
    code, out, err = run(cmd + [url], DOWNLOAD_TIMEOUT_SECONDS)
    path = out.strip().splitlines()[-1] if code == 0 and out.strip() else ""
    return (path if path and Path(path).is_file() else None), err


def with_browser(base, url, out_dir, browser):
    """Borrow one browser's sign-in for this site: read its cookies once, keep the site's, then delete them."""
    domains = site_domains(url)
    with tempfile.TemporaryDirectory(prefix="aip-reference-") as private:
        os.chmod(private, 0o700)
        whole = Path(private) / "browser.txt"
        site = Path(private) / "site.txt"
        # With no URL yt-dlp exits with a usage error, after writing the browser's jar to --cookies.
        _, _, err = run(COOKIE_READER + ["--cookies-from-browser", browser, "--cookies", str(whole)],
                        PROBE_TIMEOUT_SECONDS)
        if not whole.exists():
            return None, None, f"the {browser} sign-in could not be read: {detail(err)}"
        site.write_text(filter_jar(whole.read_text(encoding="utf-8", errors="replace"), domains), encoding="utf-8")
        os.chmod(site, 0o600)
        whole.unlink()
        code, duration, err = probe(base, url, ["--cookies", str(site)])
        if code != 0:
            return None, None, err
        path, err = download(base, url, out_dir, ["--cookies", str(site)], duration)
        return path, duration, err


def fetch(url, out_dir, browser=None):
    base = downloader()
    if base is None:
        return {"status": "no_downloader"}
    base = base + ["--ignore-config", "--no-playlist"] + js_runtime_args()
    out_dir.mkdir(parents=True, exist_ok=True)
    if browser is None:
        code, duration, err = probe(base, url, [])
        if code == 0:
            path, err = download(base, url, out_dir, [], duration)
            if path:
                return {"status": "ok", "path": path, "duration": duration, "cookies": "none"}
        kind = classify(err)
        if kind == "sign_in_required":
            browsers = browser_profiles() if site_domains(url) else []
            return {"status": kind, "browsers": browsers, "gated": gated(browsers)}
        return {"status": kind, "detail": detail(err)}
    if site_domains(url) is None:
        return {"status": "sign_in_required", "browsers": [], "gated": [],
                "detail": "a sign-in is borrowed only for YouTube, TikTok and Instagram links"}
    browsers = gated(browser_profiles()) if browser == "auto" else [browser]
    if not browsers:
        return {"status": "sign_in_required", "browsers": browser_profiles(), "gated": [],
                "detail": "no browser here asks for consent before its cookies are read; name one the user agreed to"}
    err = ""
    for name in browsers:
        path, duration, err = with_browser(base, url, out_dir, name)
        if path:
            return {"status": "ok", "path": path, "duration": duration, "cookies": name}
        if classify(err) == "unavailable":
            break
    kind = classify(err)
    return {"status": "unavailable" if kind == "unavailable" else "failed", "detail": detail(err)}


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("url")
    parser.add_argument("out", type=Path)
    parser.add_argument("--browser", choices=("auto", "firefox", "chrome"))
    args = parser.parse_args(argv)
    result = fetch(args.url, args.out, args.browser)
    print(json.dumps(result))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
