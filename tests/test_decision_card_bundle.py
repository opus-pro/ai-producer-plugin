from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CARD_DIR = REPO / "plugins" / "aip" / "assets" / "decision-card"
BUNDLE = CARD_DIR / "decision-card.js"
TILES = CARD_DIR / "caption-tiles" / "v1"
CAPTION_PATTERNS = {
    "blur-ladder",
    "editorial-stack",
    "inverted-stack",
    "lead-in-flare",
    "pace-adaptive",
    "scribble-subtitle",
    "solo-word-punch",
    "tilt-slam",
}
MAX_BUNDLE_BYTES = 256 * 1024
MAX_TILE_BYTES = 128 * 1024
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
FINE_CUT_COMPONENTS = {"editing_preference_example", "editing_preference", "reference_image", "visual_preference_prompt"}


class DecisionCardBundleTest(unittest.TestCase):
    """The widget bundle is generated, public-safe, and ships every preview it rewrites to."""

    def setUp(self) -> None:
        self.source = BUNDLE.read_text(encoding="utf-8")

    def test_bundle_is_generated_from_the_service_card(self) -> None:
        self.assertRegex(self.source, r"Generated from the AI Producer service's decision card resource ui://aip/decision-card/v\d+\.")
        self.assertIn("Do not edit by hand", self.source)
        self.assertIn("window.AIPDecisionCard = {", self.source)
        self.assertLessEqual(BUNDLE.stat().st_size, MAX_BUNDLE_BYTES)

    def test_card_rules_outweigh_the_widget_host(self) -> None:
        # A widget host styles buttons with an id-weight selector; every card rule below the
        # document level is scoped under the shell twice so the card keeps its own look.
        self.assertIn("#card-shell#card-shell .seg", self.source)
        self.assertIn("#card-shell#card-shell button", self.source)
        self.assertNotRegex(self.source, r'(?:\\n|[}]) *\.seg[ {\[:]', "an unscoped card rule loses to the host")

    def test_a_sent_card_says_where_its_answer_went_and_reopens(self) -> None:
        # sendPrompt only fills the message box, and the host never tells the widget it was sent.
        self.assertIn('"Added to your message. Press Enter to send it."', self.source)
        self.assertNotIn("recorded in the chat", self.source)
        self.assertIn('el("button", "change", "Change")', self.source)
        self.assertIn("view.submission = null; save(); render();", self.source)

    def test_a_refused_card_asks_for_another_press(self) -> None:
        # The host refuses a message that does not follow a recent click; a new press is one.
        self.assertIn('"Not added to your message. Press Send again, or type your choices in the chat."', self.source)
        self.assertNotIn("The chat rejected this selection", self.source)

    def test_bundle_names_no_network_origin(self) -> None:
        urls = set(re.findall(r"https?://[^\s\"')]+", self.source))
        self.assertLessEqual(urls, {SVG_NAMESPACE}, "the bundle must not reach any origin beyond its own directory")
        self.assertNotIn("opus.pro", self.source)

    def test_fine_cut_components_never_reach_the_card(self) -> None:
        match = re.search(r"var FINE_CUT = \[([^\]]*)\];", self.source)
        self.assertIsNotNone(match, "the bundle must name the fine-cut components it drops")
        assert match is not None
        self.assertEqual(set(re.findall(r'"([a-z_]+)"', match.group(1))), FINE_CUT_COMPONENTS)
        self.assertIn("FINE_CUT.indexOf(component.id) >= 0", self.source)

    def test_caption_previews_ship_beside_the_bundle(self) -> None:
        self.assertIn('BASE + "caption-tiles/v1/"', self.source)
        shipped = {path.stem for path in TILES.glob("*.mp4")}
        self.assertEqual(shipped, CAPTION_PATTERNS)
        self.assertEqual({path.suffix for path in TILES.iterdir()}, {".mp4"})
        for tile in TILES.glob("*.mp4"):
            data = tile.read_bytes()
            self.assertLessEqual(len(data), MAX_TILE_BYTES, tile.name)
            self.assertEqual(data[4:8], b"ftyp", f"{tile.name} is not an MP4 file")


if __name__ == "__main__":
    unittest.main()
