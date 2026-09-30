"""Offline checks for speaker zoom, filter and motion effect hosts in index.html.

A speaker zoom, filter or motion is an empty visual host the editor lists and edits and
the service's engine replays; the aip-composition skill owns the contract. These checks
mirror what the service accepts, so a host that passes here is one the editor shows. A
motion host also names a definition, an inline <script data-aip-motion> whose frame
function the engine calls every frame; when Node is available, `sample` runs each one
the way the service's commit check does and reports what the engine would not draw.
"""

import json
import math
import re
import shutil
import subprocess

ENGINE = "public/vendor/speaker-effects.js"
TRACKS = {"zoom": "20", "filter": "21"}
MAX_SCALE = 3.0
MAX_RAMP = 10.0
ANCHOR_TOLERANCE = 0.02

MOTION_NAME = re.compile(r"^[a-z0-9-]{1,40}$")
PARAM_NAME = re.compile(r"^[a-z][a-zA-Z0-9]{0,15}$")
MOTION_TRACK = re.compile(r"^\s*\d{1,4}\s*$")
MIN_MOTION_TRACK, MAX_MOTION_TRACK = 900, 907
MAX_PARAMS, MAX_PARAMS_CHARS, MAX_PARAM_MAGNITUDE = 8, 400, 1_000_000
# The sources a definition could read once and keep; read on code with strings and
# comments blanked, as the service reads it.
MOTION_NONDETERMINISTIC = re.compile(
    r"\bMath\s*\.\s*random\b|\bDate\b|\bperformance\b|\bcrypto\b|\bsetTimeout\b|\bsetInterval\b"
    r"|\brequestAnimationFrame\b")
_JS_STRING_OR_COMMENT = re.compile(
    r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`|/\*.*?\*/|//[^\n]*", re.S)

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


def motion_params(raw):
    """A motion host's parameter values, or None when the service would reject them."""
    if raw is None or str(raw).strip() == "":
        return {}
    if len(raw) > MAX_PARAMS_CHARS:
        return None
    try:
        value = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(value, dict) or len(value) > MAX_PARAMS:
        return None
    for name, number in value.items():
        is_number = isinstance(number, (int, float)) and not isinstance(number, bool)
        if not PARAM_NAME.fullmatch(name) or not is_number or not math.isfinite(number) or abs(number) > MAX_PARAM_MAGNITUDE:
            return None
    return value


def _motion_host_ok(attrs):
    track = attrs.get("data-track-index")
    return (MOTION_NAME.fullmatch((attrs.get("data-effect-motion") or "").strip()) is not None
            and motion_params(attrs.get("data-effect-params")) is not None
            and track is not None and MOTION_TRACK.match(track) is not None
            and MIN_MOTION_TRACK <= int(track) <= MAX_MOTION_TRACK)


def _value_codes(kind, attrs, duration):
    if kind == "motion":
        return [] if _motion_host_ok(attrs) else ["motion_host_invalid"]
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
    scale = _number(attrs.get("data-effect-scale"))
    if scale is None or not 1 < scale <= MAX_SCALE:
        codes.append("invalid_speaker_effect_scale")
    origin = attrs.get("data-effect-origin")
    if origin is not None and not ORIGIN.match(origin.strip()):
        codes.append("invalid_speaker_effect_origin")
    return codes


def _lane(kind, attrs):
    """The lane two effects may not overlap in: a zoom or filter's kind, a motion's track."""
    return f"motion:{(attrs.get('data-track-index') or '').strip()}" if kind == "motion" else kind


def _host_codes(attrs, clips):
    kind = attrs.get("data-aip-effect")
    if kind not in (*TRACKS, "motion") or "visual-host" not in (attrs.get("class") or "").split() or not attrs.get(
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
    if kind in TRACKS and attrs.get("data-track-index") != TRACKS[kind]:
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
    return codes, (_lane(kind, attrs), start, start + duration)


def _definition_codes(scripts):
    """Codes for the index's motion definitions, and the names they define."""
    codes, names, seen = [], set(), set()
    for name, text in scripts:
        name = (name or "").strip()
        if not MOTION_NAME.match(name) or name in seen:
            codes.append("motion_definition_invalid")
            continue
        seen.add(name)
        if MOTION_NONDETERMINISTIC.search(_JS_STRING_OR_COMMENT.sub(" ", text)):
            codes.append("motion_nondeterministic")
            continue
        names.add(name)
    return codes, names, seen


def check(elements, motion_scripts=()):
    """Error codes for the effect hosts among ``index.html``'s ``(tag, attrs, depth)``
    elements and its ``(name, text)`` motion definitions, in the order found; empty when
    there are none or all are valid."""
    top = [(tag, attrs) for tag, attrs, depth in elements if depth == 0]
    clips = [attrs for tag, attrs in top if tag == "video" and attrs.get("data-track-index") == "0"]
    codes, windows = [], {}
    hosts = [attrs for _, attrs in top if attrs.get("data-aip-effect") is not None]
    for attrs in hosts:
        host_codes, window = _host_codes(attrs, clips)
        codes.extend(host_codes)
        if window is not None:
            windows.setdefault(window[0], []).append(window[1:])
    for lane, spans in windows.items():
        spans.sort()
        if any(later[0] < earlier[1] for earlier, later in zip(spans, spans[1:])):
            codes.append("motion_track_overlap" if lane.startswith("motion:") else "speaker_effect_overlap")
    definition_codes, defined, named = _definition_codes(motion_scripts)
    codes.extend(definition_codes)
    for attrs in hosts:
        name = (attrs.get("data-effect-motion") or "").strip()
        if attrs.get("data-aip-effect") == "motion" and _motion_host_ok(attrs) and name not in named:
            codes.append("motion_definition_missing")
    engine_loaded = any(tag == "script" and (attrs.get("src") or "").strip() == ENGINE for tag, attrs in top)
    if hosts and not engine_loaded:
        codes.append("speaker_effect_engine_missing")
    return list(dict.fromkeys(codes))


# Runs each motion host's definition in a Node vm context where randomness and time throw,
# at 34 instants across its window, twice, and reports what the service's commit check
# would refuse. The service repeats this in its own contained boot.
_SAMPLER = r"""
const vm = require("vm");
const input = JSON.parse(require("fs").readFileSync(0, "utf8"));
const LIMITS = { x: 160, y: 160, rotate: 8 };
const COLOR = /^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/;
const MAG = 1000000;
// A realm of its own per definition: built-ins only, randomness and time throwing, Math
// and JSON frozen, no code from strings. Only primitives cross into it.
const SETUP = `
  var thrower = function () { throw new Error("randomness or time is not available to a motion definition"); };
  Math.random = thrower;
  globalThis.Date = function () { thrower(); };
  globalThis.Date.now = thrower;
  globalThis.performance = { now: thrower };
  globalThis.crypto = { getRandomValues: thrower, randomUUID: thrower };
  globalThis.setTimeout = thrower; globalThis.setInterval = thrower;
  globalThis.requestAnimationFrame = thrower; globalThis.queueMicrotask = thrower;
  globalThis.window = globalThis; globalThis.self = globalThis;
  globalThis.__aipMotions = {};
  (function () {
    var rand = function (id) {
      var h = 2166136261;
      for (var k = 0; k < id.length; k++) h = Math.imul(h ^ id.charCodeAt(k), 16777619) >>> 0;
      return function (i) {
        var x = Math.imul(h ^ (((i | 0) + 0x9e3779b9) >>> 0), 2246822519) >>> 0;
        x = Math.imul(x ^ (x >>> 13), 3266489917) >>> 0;
        return (((x ^ (x >>> 16)) >>> 0) / 4294967296) * 2 * Math.PI;
      };
    };
    var ok = function (spec) {
      return !!spec && typeof spec === "object" && isFinite(spec.min) && isFinite(spec.max) && spec.min < spec.max &&
        Math.abs(spec.min) <= ${MAG} && Math.abs(spec.max) <= ${MAG} && isFinite(spec.default) &&
        spec.default >= spec.min && spec.default <= spec.max;
    };
    globalThis.__decl = function (name) {
      var def = Object.prototype.hasOwnProperty.call(globalThis.__aipMotions, name) ? globalThis.__aipMotions[name] : null;
      if (!def || typeof def.frame !== "function") return "missing";
      var decl = def.params === undefined ? {} : def.params;
      if (!decl || typeof decl !== "object" || Object.keys(decl).length > 8) return "invalid";
      for (var key in decl) if (Object.prototype.hasOwnProperty.call(decl, key) && !ok(decl[key])) return "invalid";
      return JSON.stringify(decl);
    };
    globalThis.__frame = function (name, paramsJson, id, t, d) {
      var def = globalThis.__aipMotions[name];
      var values = JSON.parse(paramsJson);
      var decl = def.params || {};
      var p = {};
      for (var key in decl) {
        if (!Object.prototype.hasOwnProperty.call(decl, key)) continue;
        var v = Object.prototype.hasOwnProperty.call(values, key) ? values[key] : decl[key].default;
        p[key] = Math.min(decl[key].max, Math.max(decl[key].min, v));
      }
      var out = def.frame(t, d, p, rand(id));
      return JSON.stringify(out === undefined ? null : out);
    };
  })();
  Object.freeze(Math);
  Object.freeze(JSON);
`;
function realm(source) {
  const ctx = vm.createContext({}, { codeGeneration: { strings: false, wasm: false }, microtaskMode: "afterEvaluate" });
  vm.runInContext(SETUP, ctx);
  vm.runInContext(source, ctx, { timeout: 1000 });
  return ctx;
}
function bad(out) {
  if (!out || typeof out !== "object") return true;
  for (const key of Object.keys(out)) {
    if (key === "overlay") {
      const o = out.overlay;
      if (!o || !Number.isFinite(o.opacity) || o.opacity < 0 || o.opacity > 1) return true;
      if (o.color !== undefined && !COLOR.test(String(o.color))) return true;
    } else if (key === "scale") {
      if (!Number.isFinite(out.scale) || out.scale < 1 || out.scale > 3) return true;
    } else if (key in LIMITS) {
      if (!Number.isFinite(out[key]) || Math.abs(out[key]) > LIMITS[key]) return true;
    } else return true;
  }
  return false;
}
function pass(ctx, host) {
  const outs = [];
  for (let k = 0; k < 34; k++) {
    const t = Math.min(host.duration * k / 33, host.duration - 1e-6);
    const code = `__frame(${JSON.stringify(host.name)}, ${JSON.stringify(JSON.stringify(host.params))}, ${JSON.stringify(host.id)}, ${t}, ${host.duration})`;
    const out = JSON.parse(String(vm.runInContext(code, ctx, { timeout: 250 })));
    if (bad(out)) throw new Error("output");
    outs.push(JSON.stringify(out));
  }
  return outs.join("|");
}
const codes = [];
for (const host of input.hosts) {
  let a;
  let b;
  try {
    a = realm(input.sources[host.name] || "");
    b = realm(input.sources[host.name] || "");
  } catch (e) {
    codes.push("motion_definition_invalid");
    continue;
  }
  const decl = String(vm.runInContext(`__decl(${JSON.stringify(host.name)})`, a, { timeout: 250 }));
  if (decl === "missing") { codes.push("motion_definition_missing"); continue; }
  if (decl === "invalid") { codes.push("motion_definition_invalid"); continue; }
  const declared = JSON.parse(decl);
  if (Object.keys(host.params).some((name) => !Object.prototype.hasOwnProperty.call(declared, name) ||
      host.params[name] < declared[name].min || host.params[name] > declared[name].max)) {
    codes.push("motion_params_invalid");
    continue;
  }
  try {
    const first = pass(a, host);
    if (pass(a, host) !== first || pass(b, host) !== first) codes.push("motion_nondeterministic");
  } catch (e) {
    const text = String(e && e.message);
    codes.push(text === "output" ? "motion_output_invalid" : /timed out/.test(text) ? "motion_too_slow" : "motion_nondeterministic");
  }
}
process.stdout.write(JSON.stringify(codes));
"""


def sample(elements, motion_scripts=()):
    """Error codes from running each valid motion host's definition, or [] when there are
    none, when Node is absent, or when the static checks already refuse the index."""
    node = shutil.which("node")
    sources = {(name or "").strip(): text for name, text in motion_scripts}
    hosts = []
    for tag, attrs, depth in elements:
        if depth or attrs.get("data-aip-effect") != "motion" or not _motion_host_ok(attrs):
            continue
        duration = _number(attrs.get("data-duration"))
        name = attrs["data-effect-motion"].strip()
        if duration and duration > 0 and name in sources:
            hosts.append({"id": attrs.get("data-composition-id") or "", "name": name, "duration": duration,
                          "params": motion_params(attrs.get("data-effect-params"))})
    if node is None or not hosts:
        return []
    try:
        done = subprocess.run([node, "-e", _SAMPLER], input=json.dumps({"hosts": hosts, "sources": sources}),
                              capture_output=True, text=True, timeout=30, check=False)
        found = json.loads(done.stdout) if done.returncode == 0 else []
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return []
    return list(dict.fromkeys(str(code) for code in found))
