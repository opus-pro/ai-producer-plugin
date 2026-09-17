from html.parser import HTMLParser
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/pip-transition/index.html"
REFERENCE = ROOT / "plugins/aip/skills/aip-composition/references/pip-transition.md"


class Tags(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.items: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.items.append((tag, dict(attrs)))

    def one(self, tag: str, element_id: str) -> dict[str, str | None]:
        matches = [attrs for name, attrs in self.items if name == tag and attrs.get("id") == element_id]
        if len(matches) != 1:
            raise AssertionError(f"expected one {tag}#{element_id}, got {len(matches)}")
        return matches[0]


class PipEditabilityContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = FIXTURE.read_text(encoding="utf-8")
        self.tags = Tags()
        self.tags.feed(self.html)

    def test_effect_owns_muted_pip_view_with_host_timing(self) -> None:
        host = self.tags.one("div", "pip-host")
        speaker = self.tags.one("video", "speaker")
        effect_speaker = self.tags.one("video", "effect-speaker")
        self.assertIn("src", speaker)
        self.assertNotIn("data-pip-src", speaker)
        self.assertNotIn("src", effect_speaker)
        self.assertEqual(effect_speaker["data-pip-src"], "public/synthetic.webm")
        self.assertEqual(effect_speaker["data-start"], host["data-start"])
        self.assertEqual(effect_speaker["data-duration"], host["data-duration"])
        self.assertIn("muted", effect_speaker)
        self.assertEqual(effect_speaker["data-volume"], "0")

    def test_editable_frame_uses_child_timeline_not_root_geometry(self) -> None:
        frames = [attrs for tag, attrs in self.tags.items
                  if tag == "div" and "speaker-pip-frame" in (attrs.get("class") or "").split()]
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0]["data-aip-editable"], "speaker-pip-frame")
        self.assertIn("pipTl.to(frame", self.html)
        self.assertIsNone(re.search(r"rootTl\.(?:fromTo|to|set)\s*\(", self.html))
        self.assertIn("window.moveHost", self.html)
        self.assertIn("window.deleteHost", self.html)

    def test_published_recipe_keeps_the_same_ownership_boundary(self) -> None:
        reference = REFERENCE.read_text(encoding="utf-8")
        self.assertIn('class="speaker-pip-frame" data-aip-editable="speaker-pip-frame"', reference)
        self.assertIn('data-pip-src="public/source.mp4"', reference)
        self.assertIn("tl.to(frame", reference)
        self.assertNotIn("rootTl.", reference)


if __name__ == "__main__":
    unittest.main()
