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


class StylesheetSyntaxTests(unittest.TestCase):
    """The export compiles every stylesheet with a strict parser; a browser previews the same
    malformed CSS without complaint. Each case is a shape that previews and fails to export."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "compositions").mkdir()
        (self.root / "index.html").write_text(ROOT.format(HOST))

    def css_errors(self, css):
        style = '<template><div data-composition-id="beat"><style>\n{}\n</style></div></template>'
        (self.root / "compositions/beat.html").write_text(style.format(css))
        report = preflight.check(self.root)
        return [item["detail"] for item in report["errors"] if item["code"] == "css_syntax_error"]

    def test_a_stray_closing_brace_is_located_in_the_file(self):
        self.assertEqual(self.css_errors(".beat{color:red}}"), ["line 2, column 17: Unexpected }"])

    def test_a_missing_semicolon_points_at_the_next_property(self):
        errors = self.css_errors(".card{max-width:50%padding:24px}")
        self.assertEqual(errors, ["line 2, column 20: Missed semicolon"])

    def test_a_rule_cut_off_after_its_selector_is_refused(self):
        self.assertEqual(self.css_errors(".a{color:red}.page "), ["line 2, column 14: Unknown word"])

    def test_unclosed_structures_are_refused(self):
        for css, reason in (
            (".a{color:red", "Unclosed block"),
            ('.a::after{content:"x}', "Unclosed string"),
            (".a{color:red}/* note", "Unclosed comment"),
            (".a{width:calc(1px + 2px}", "Unclosed bracket"),
            (".a{color red:blue}", "Unknown word"),
        ):
            with self.subTest(css=css):
                errors = self.css_errors(css)
                self.assertEqual(len(errors), 1)
                self.assertTrue(errors[0].endswith(reason), errors)

    def test_css_the_parser_accepts_is_not_reported(self):
        accepted = "\n".join((
            "@import url(theme.css);",
            ":root{--gap:a:b;--block:{inner:value}}",
            ".a{background:url(data:image/png;base64,AA:BB);filter:progid:DX.Gradient(x=1)}",
            '.b::after{content:"a:b;}{";}',
            ".md\\:flex{display:flex}",
            "@media (min-width:600px){.c{margin:0}}",
            ".d{&:hover{color:red}}",
            ".e{/* } */color:red;;}",
            "@keyframes rise{0%{opacity:0}100%{opacity:1}}",
            ".f{: color:red}",
        ))
        self.assertEqual(self.css_errors(accepted), [])

    def test_a_stylesheet_file_is_checked_too(self):
        (self.root / "compositions/beat.html").write_text(CHILD.format(""))
        (self.root / "styles").mkdir()
        (self.root / "styles/theme.css").write_text(".a{color:red}\n.b{color:blue}}\n")
        report = preflight.check(self.root)
        self.assertIn({"code": "css_syntax_error", "file": "styles/theme.css",
                       "detail": "line 2, column 15: Unexpected }"}, report["errors"])

    def test_an_inline_style_attribute_is_not_a_stylesheet(self):
        (self.root / "compositions/beat.html").write_text(CHILD.format('<div style="color:red; }"></div>'))
        self.assertTrue(preflight.check(self.root)["ok"])


if __name__ == "__main__":
    unittest.main()
