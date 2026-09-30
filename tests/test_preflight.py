"""Synthetic workspace tests for the offline preview preflight."""

import importlib.util
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "plugins/aip/skills/aip/scripts/preflight.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("preflight", SCRIPT)
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)

ROOT = '<div id="stage" data-composition-id="finecut-root" data-start="0" data-duration="8">{}</div>'
HOST = '<div class="visual-host clip" data-composition-id="beat" data-composition-src="compositions/beat.html" data-start="1" data-duration="3"></div>'
CHILD = '<template><div data-composition-id="beat">{}</div></template>'


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write("index.html", ROOT.format(HOST))
        self.write("compositions/beat.html", CHILD.format(""))

    def write(self, name, content=""):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def codes(self, result):
        return {item["code"] for item in result["errors"]}

    def test_valid_independent_composition(self):
        self.assertTrue(preflight.check(self.root)["ok"])

    def test_child_references_resolve_from_the_root(self):
        self.write("compositions/beat.html", CHILD.format('<img src="public/photo.png">'))
        self.assertIn("missing_local_reference", self.codes(preflight.check(self.root)))
        self.write("public/photo.png")
        self.assertTrue(preflight.check(self.root)["ok"])

    def test_css_file_and_inline_urls(self):
        self.write("index.html", ROOT.format(HOST + '<link href="styles/main.css">'))
        self.write("styles/main.css", '.card { background: url("../public/photo.png"); }')
        self.write("compositions/beat.html", CHILD.format('<div style="background:url(public/photo.png)"></div>'))
        self.assertIn("missing_local_reference", self.codes(preflight.check(self.root)))
        self.write("public/photo.png")
        self.assertTrue(preflight.check(self.root)["ok"])

    def test_only_explicit_service_assets_are_allowed(self):
        self.write("index.html", ROOT.format(HOST + '<audio id="speaker-audio" src="public/source.mp3"></audio>'))
        self.assertFalse(preflight.check(self.root)["ok"])
        self.assertTrue(preflight.check(self.root, ["public/source.mp3"])["ok"])

    def test_service_paths_declare_existing_remote_assets(self):
        self.write("index.html", ROOT.format('<audio src="public/source.mp3"></audio>'))
        self.assertTrue(preflight.check(self.root, ["render-engine/public/source.mp3"])["ok"])
        report = preflight.check(self.root, ["render-engine/../outside"])
        self.assertIn("invalid_service_file", self.codes(report))

    def test_a_type_no_commit_accepts_is_reported_before_upload(self):
        self.write("compositions/beat.html", CHILD.format('<img src="public/images/logo.svg">'))
        self.write("public/images/logo.svg", "<svg xmlns='http://www.w3.org/2000/svg'/>")
        self.write("public/notes", "source: example")
        report = preflight.check(self.root)
        self.assertIn({"code": "unpromotable_type", "file": "public/images/logo.svg"}, report["errors"])
        self.assertIn({"code": "unpromotable_type", "file": "public/notes"}, report["errors"])

    def test_service_scripts_and_hidden_entries_are_not_publication_files(self):
        self.write("public/vendor/gsap.min.js", "// provided by the service")
        self.write(".DS_Store")
        self.write("compositions/.cache/build.js")
        self.assertIn("unpromotable_type", self.codes(preflight.check(self.root)))
        self.assertTrue(preflight.check(self.root, ["public/vendor/gsap.min.js"])["ok"])

    def test_declared_service_caption_layer_is_reported_as_a_warning(self):
        captions = ('<div class="visual-host clip" data-composition-id="narrator-captions" '
                    'data-composition-src="compositions/narrator_captions.html" data-start="0" data-duration="8"></div>')
        self.write("index.html", ROOT.format(HOST + captions))
        undeclared = preflight.check(self.root)
        self.assertIn("composition_not_locally_inspectable", self.codes(undeclared))
        declared = preflight.check(self.root, ["render-engine/compositions/narrator_captions.html"])
        self.assertNotIn("composition_not_locally_inspectable", self.codes(declared))
        self.assertIn({"code": "composition_not_locally_inspectable", "file": "index.html"}, declared["warnings"])
        self.assertTrue(declared["ok"])

    def test_declared_missing_composition_other_than_the_caption_layer_stays_an_error(self):
        (self.root / "compositions/beat.html").unlink()
        report = preflight.check(self.root, ["render-engine/compositions/beat.html"])
        self.assertIn("composition_not_locally_inspectable", self.codes(report))
        self.assertFalse(report["ok"])

    def test_composition_id_and_timing_are_checked(self):
        self.write("compositions/beat.html", '<template><div data-composition-id="wrong" data-start="nan" data-duration="0"></div></template>')
        codes = self.codes(preflight.check(self.root))
        self.assertIn("composition_id_mismatch", codes)
        self.assertIn("invalid_timing", codes)

    def test_remote_urls_are_not_printed(self):
        self.write("index.html", ROOT.format('<img src="https://example.invalid/a?secret=value">'))
        report = preflight.check(self.root)
        self.assertIn("remote_reference_unsupported", self.codes(report))
        self.assertNotIn("secret", str(report))
        self.assertNotIn("example.invalid", str(report))

    def test_nested_video_is_warning(self):
        self.write("compositions/beat.html", CHILD.format('<video data-pip-src="public/source.mp4" muted data-volume="0"></video>'))
        report = preflight.check(self.root, ["public/source.mp4"])
        self.assertTrue(report["ok"])
        self.assertEqual(report["warnings"][0]["code"], "nested_video_requires_player_validation")

    def test_composition_references_resolve_from_the_root(self):
        # The editor mounts a composition into index.html, so its paths read from the
        # root; the documented nested footage tag passes as written.
        self.write("public/videos/clip.mp4", "mp4")
        self.write("public/images/card.png", "png")
        self.write("compositions/beat.html", CHILD.format(
            '<video id="footage" class="clip" src="public/videos/clip.mp4" data-start="1" data-duration="3" '
            'data-media-start="0" muted playsinline data-volume="0"></video>'
            '<img src="public/images/card.png"><style>.bed{background:url("public/images/card.png")}</style>'))
        report = preflight.check(self.root)
        self.assertTrue(report["ok"], report)

    def test_composition_reference_climbing_to_public_is_outside_the_workspace(self):
        self.write("public/images/card.png", "png")
        self.write("compositions/beat.html", CHILD.format('<img src="../public/images/card.png">'))
        self.assertEqual(self.codes(preflight.check(self.root)), {"reference_outside_workspace"})

    def test_composition_script_resolves_from_the_composition_file(self):
        # The export loads a composition as its own page, so its vendor script is
        # written `../public/vendor/...`; the editor re-points it by file name.
        self.write("compositions/beat.html", CHILD.format('<script src="../public/vendor/gsap.min.js"></script>'))
        self.assertTrue(preflight.check(self.root, ["public/vendor/gsap.min.js"])["ok"])
        self.write("compositions/beat.html", CHILD.format('<script src="public/vendor/gsap.min.js"></script>'))
        self.assertIn("missing_local_reference", self.codes(preflight.check(self.root, ["public/vendor/gsap.min.js"])))

    def test_composition_stylesheet_resolves_from_the_root(self):
        self.write("styles/theme.css", "body{}")
        self.write("compositions/beat.html", CHILD.format('<link rel="stylesheet" href="styles/theme.css">'))
        self.assertTrue(preflight.check(self.root)["ok"])
        self.write("compositions/beat.html", CHILD.format('<link rel="stylesheet" href="../styles/theme.css">'))
        self.assertEqual(self.codes(preflight.check(self.root)), {"reference_outside_workspace"})

    def test_stylesheet_url_resolves_from_the_css_file(self):
        self.write("public/fonts/a.woff2", "font")
        self.write("styles/theme.css", "@font-face{src:url(../public/fonts/a.woff2)}")
        self.assertTrue(preflight.check(self.root)["ok"])

    def test_fragment_data_and_external_path(self):
        self.write("index.html", ROOT.format('<a href="#stage"></a><img src="data:image/png;base64,abc"><img src="../outside.png">'))
        self.assertEqual(self.codes(preflight.check(self.root)), {"reference_outside_workspace"})

    def test_root_inside_template_is_rejected(self):
        self.write("index.html", '<template>' + ROOT.format("") + '</template>')
        self.assertIn("missing_or_invalid_root", self.codes(preflight.check(self.root)))


# The skeletons of the code-drawn reference, reduced to what each rule reads.
TICK = "const st = { t: 0 }; tl.to(st, { t: 4, duration: 4, ease: 'none', onUpdate: function () { draw(st.t); } }, 0);"
CANVAS_2D = ('<canvas class="cv"></canvas><script>const tl = gsap.timeline({ paused: true });'
    "const ctx = root.querySelector('.cv').getContext('2d'); function draw(t) { ctx.fillRect(t * 50, 0, 9, 9); }"
    + TICK + "</script>")
WEBGL2 = ('<canvas class="cv"></canvas><script>const tl = gsap.timeline({ paused: true }); let gl = null;'
    "function draw(t) { if (t <= 0 || t >= 4) { if (gl) gl.getExtension('WEBGL_lose_context').loseContext(); return; }"
    " if (!gl) gl = cv.getContext('webgl2', { preserveDrawingBuffer: true }); }" + TICK + "</script>")
THREE = ('<canvas class="cv"></canvas><script src="../public/vendor/three.min.js"></script>'
    "<script>const tl = gsap.timeline({ paused: true }); let R = null;"
    "function draw(t) { if (t <= 0 || t >= 4) { if (R) { R.forceContextLoss(); R.dispose(); R = null; } return; }"
    " if (!R) { if (!window.THREE) return; R = new THREE.WebGLRenderer({ canvas: cv }); } }" + TICK + "</script>")


class CodeDrawnTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "compositions").mkdir()
        (self.root / "index.html").write_text(ROOT.format(HOST))

    def result(self, body):
        (self.root / "compositions/beat.html").write_text(CHILD.format(body))
        result = preflight.check(self.root)
        return ({item["code"] for item in result["errors"]}, {item["code"] for item in result["warnings"]})

    def test_the_reference_skeletons_pass(self):
        for body in (CANVAS_2D, WEBGL2, THREE):
            self.assertEqual(self.result(body), (set(), set()))

    def test_three_needs_no_declaration(self):
        # The service writes it in the commit that first names it, so nothing declares it.
        self.result(THREE)
        self.assertFalse((self.root / "public/vendor/three.min.js").exists())
        self.assertTrue(preflight.check(self.root)["ok"])

    def test_a_canvas_on_its_own_clock_is_an_error(self):
        errors, _ = self.result(CANVAS_2D.replace(TICK, "function loop() { draw(1); requestAnimationFrame(loop); } loop();"))
        self.assertEqual(errors, {"code_drawn_clock"})

    def test_a_dom_moment_with_a_timer_is_not_judged(self):
        self.assertEqual(self.result("<script>setTimeout(function () {}, 10);</script>"), (set(), set()))

    def test_a_clock_in_a_comment_or_string_does_not_count(self):
        body = CANVAS_2D.replace(TICK, "// requestAnimationFrame\nconst why = 'setTimeout';" + TICK)
        self.assertEqual(self.result(body), (set(), set()))

    def test_an_unreleased_context_is_an_error(self):
        errors, _ = self.result(WEBGL2.replace(".loseContext()", ".isContextLost()"))
        self.assertEqual(errors, {"webgl_context_not_released"})
        errors, _ = self.result(THREE.replace("R.forceContextLoss(); ", ""))
        self.assertEqual(errors, {"webgl_context_not_released"})

    def test_three_read_before_it_loads_is_a_warning(self):
        errors, warnings = self.result(THREE.replace("if (!window.THREE) return; ", ""))
        self.assertEqual((errors, warnings), (set(), {"three_used_before_load"}))

    def test_every_script_type_a_browser_runs_is_judged(self):
        body = CANVAS_2D.replace(TICK, "requestAnimationFrame(draw);").replace(
            "<script>", '<script type="text/javascript; charset=utf-8">', 1)
        self.assertEqual(self.result(body)[0], {"code_drawn_clock"})

    def test_an_unguarded_alias_of_window_three_is_a_warning(self):
        body = THREE.replace("if (!window.THREE) return; R = new THREE", "R = new T").replace(
            "let R = null;", "let R = null; const T = window.THREE;")
        self.assertEqual(self.result(body), (set(), {"three_used_before_load"}))

    def test_randomness_in_a_canvas_is_a_warning(self):
        errors, warnings = self.result(CANVAS_2D.replace("t * 50", "Math.random() * 50"))
        self.assertEqual((errors, warnings), (set(), {"code_drawn_nondeterministic"}))


SPEAKER = ('<video id="speaker" class="clip speaker-clip" src="public/source.mp4" data-start="0" data-duration="4" '
           'data-media-start="10" data-track-index="0"></video>'
           '<video id="speaker-2" class="clip speaker-clip" src="public/source.mp4" data-start="4" data-duration="4" '
           'data-media-start="20" data-track-index="0"></video>')
ENGINE = '<script src="public/vendor/speaker-effects.js"></script>'


def zoom_host(**overrides):
    attrs = {"class": "visual-host clip", "data-composition-id": "zoom-1", "data-aip-effect": "zoom",
             "data-no-timeline": "", "data-start": "5", "data-duration": "2", "data-src-anchor": "21",
             "data-track-index": "20", "data-hide-captions": "false", "data-effect-scale": "1.2",
             "data-effect-origin": "50% 40%", "data-effect-in": "0.3", "data-effect-out": "0.4"}
    attrs.update(overrides)
    text = " ".join(f'{name}="{value}"' for name, value in attrs.items() if value is not None)
    return f"<div {text}></div>"


def filter_host(**overrides):
    attrs = {"class": "visual-host clip", "data-composition-id": "filter-1", "data-aip-effect": "filter",
             "data-no-timeline": "", "data-start": "1", "data-duration": "2", "data-src-anchor": "11",
             "data-track-index": "21", "data-hide-captions": "false", "data-effect-filter": "grayscale(1)"}
    attrs.update(overrides)
    text = " ".join(f'{name}="{value}"' for name, value in attrs.items() if value is not None)
    return f"<div {text}></div>"


class SpeakerEffectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("public/source.mp4",):
            (self.root / name).parent.mkdir(parents=True, exist_ok=True)
            (self.root / name).write_text("")

    def codes(self, *hosts, engine=ENGINE):
        (self.root / "index.html").write_text(ROOT.format(SPEAKER + "".join(hosts)) + engine)
        return {item["code"] for item in preflight.check(self.root)["errors"]}

    def test_valid_zoom_and_filter_hosts_need_no_uploaded_engine(self):
        self.assertEqual(self.codes(zoom_host(), filter_host()), set())

    def test_the_engine_must_be_loaded(self):
        self.assertEqual(self.codes(zoom_host(), engine=""), {"speaker_effect_engine_missing"})

    def test_host_contract(self):
        self.assertEqual(self.codes(zoom_host(**{"data-composition-src": "compositions/zoom.html"})) - {
            "missing_local_reference", "composition_not_locally_inspectable"}, {"speaker_effect_has_composition"})
        self.assertEqual(self.codes(zoom_host(**{"data-hide-captions": None})), {"speaker_effect_hides_captions"})
        self.assertEqual(self.codes(zoom_host(**{"data-no-timeline": None})), {"speaker_effect_waits_for_timeline"})
        self.assertEqual(self.codes(zoom_host(**{"data-track-index": "3"})), {"speaker_effect_track"})
        self.assertEqual(self.codes(zoom_host(**{"data-aip-effect": "blur"})), {"invalid_speaker_effect"})

    def test_values(self):
        self.assertEqual(self.codes(zoom_host(**{"data-effect-scale": "1"})), {"invalid_speaker_effect_scale"})
        self.assertEqual(self.codes(zoom_host(**{"data-effect-origin": "center"})), {"invalid_speaker_effect_origin"})
        self.assertEqual(self.codes(zoom_host(**{"data-effect-in": "-1"})), {"invalid_speaker_effect_ramp"})
        self.assertEqual(self.codes(zoom_host(**{"data-effect-in": "1.8"})), {"speaker_effect_ramps_exceed_window"})
        self.assertEqual(self.codes(filter_host(**{"data-effect-filter": "url(#x)"})), {"invalid_speaker_effect_filter"})

    def test_the_anchor_is_the_source_second_at_the_start(self):
        self.assertEqual(self.codes(zoom_host(**{"data-src-anchor": None})), {"speaker_effect_anchor_missing"})
        # Output 5 s plays source 21 s (second clip: 20 + (5 - 4)); 15 s is the uncut position.
        self.assertEqual(self.codes(zoom_host(**{"data-src-anchor": "15"})), {"speaker_effect_anchor_mismatch"})

    def test_one_kind_does_not_overlap_itself(self):
        second = zoom_host(**{"data-composition-id": "zoom-2", "data-start": "6", "data-src-anchor": "22"})
        self.assertEqual(self.codes(zoom_host(), second), {"speaker_effect_overlap"})
        overlapping_filter = filter_host(**{"data-start": "5", "data-src-anchor": "21"})
        self.assertEqual(self.codes(zoom_host(), overlapping_filter), set())


SLIDE = ('<script data-aip-motion="slide">(window.__aipMotions = window.__aipMotions || {})["slide"] = {'
         ' params: { dx: { min: -150, max: 150, default: 0 } },'
         ' frame: function (t, d, p) { return { x: p.dx }; } };</script>')


def motion_host(**overrides):
    attrs = {"class": "visual-host clip", "data-composition-id": "hit-1", "data-aip-effect": "motion",
             "data-no-timeline": "", "data-start": "5", "data-duration": "0.4", "data-src-anchor": "21",
             "data-track-index": "900", "data-hide-captions": "false", "data-effect-motion": "slide",
             "data-effect-params": '{"dx":12}'}
    attrs.update(overrides)
    text = " ".join((f"{name}='{value}'" if '"' in value else f'{name}="{value}"')
                    for name, value in attrs.items() if value is not None)
    return f"<div {text}></div>"


def definition(name, body):
    return (f'<script data-aip-motion="{name}">(window.__aipMotions = window.__aipMotions || {{}})["{name}"] = '
            f"{body};</script>")


class MotionTests(SpeakerEffectTests):
    def test_a_motion_with_its_definition_rides_over_a_zoom_and_another_track(self):
        other = motion_host(**{"data-composition-id": "hit-2", "data-track-index": "901"})
        self.assertEqual(self.codes(zoom_host(), motion_host(), other, SLIDE), set())

    def test_two_motions_on_one_track_do_not_overlap(self):
        second = motion_host(**{"data-composition-id": "hit-2", "data-start": "5.2", "data-src-anchor": "21.2"})
        self.assertEqual(self.codes(motion_host(), second, SLIDE), {"motion_track_overlap"})

    def test_a_host_needs_its_definition(self):
        self.assertEqual(self.codes(motion_host()), {"motion_definition_missing"})

    def test_host_values(self):
        for overrides in ({"data-track-index": "22"}, {"data-track-index": "0x384"},
                          {"data-effect-params": "[1]"}, {"data-effect-params": '{"Dx":1}'},
                          {"data-effect-motion": "Slide"}):
            self.assertEqual(self.codes(motion_host(**overrides), SLIDE), {"motion_host_invalid"}, overrides)

    def test_a_definition_reading_randomness_or_time_is_an_error(self):
        for read in ("var r = Math.random();", "var n = Date.now();", "var n = performance.now();",
                     "setTimeout(function () {}, 0);"):
            captured = SLIDE.replace("(window.__aipMotions", read + " (window.__aipMotions", 1)
            self.assertEqual(self.codes(motion_host(), captured), {"motion_nondeterministic"}, read)
        quoted = SLIDE.replace("return {", 'var label = "Date"; return {')
        self.assertEqual(self.codes(motion_host(), quoted), set())

    def test_one_name_one_definition(self):
        self.assertEqual(self.codes(motion_host(), SLIDE, SLIDE), {"motion_definition_invalid"})

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_node_samples_what_the_engine_would_not_draw(self):
        wild = definition("slide", "{ frame: function () { return { x: 500 }; } }")
        self.assertEqual(self.codes(motion_host(), wild), {"motion_output_invalid"})
        counter = definition("slide", "(function () { var n = 0; return { frame: function () { n += 1; "
                             "return { x: n % 3 }; } }; })()")
        self.assertEqual(self.codes(motion_host(), counter), {"motion_nondeterministic"})


RECIPES = Path(__file__).resolve().parents[1] / "plugins/aip/skills/aip-composition/references/motion-recipes.md"


class MotionRecipeTests(SpeakerEffectTests):
    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_every_recipe_is_a_definition_the_service_accepts(self):
        blocks = re.findall(r"```js\n(.*?)```", RECIPES.read_text(), re.S)
        self.assertGreaterEqual(len(blocks), 7)
        for code in blocks:
            name = re.search(r'\)\["([a-z0-9-]+)"\]\s*=', code).group(1)
            host = motion_host(**{"data-effect-motion": name, "data-effect-params": None, "data-duration": "2"})
            script = f'<script data-aip-motion="{name}">{code}</script>'
            self.assertEqual(self.codes(host, script), set(), name)


if __name__ == "__main__":
    unittest.main()
