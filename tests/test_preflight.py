"""Synthetic workspace tests for the offline preview preflight."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "plugins/aip/skills/aip/scripts/preflight.py"
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


if __name__ == "__main__":
    unittest.main()
