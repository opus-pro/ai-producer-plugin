"""Synthetic workspace tests for the offline preview preflight."""

import importlib.util
from pathlib import Path
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

    def test_randomness_in_a_canvas_is_a_warning(self):
        errors, warnings = self.result(CANVAS_2D.replace("t * 50", "Math.random() * 50"))
        self.assertEqual((errors, warnings), (set(), {"code_drawn_nondeterministic"}))


if __name__ == "__main__":
    unittest.main()
