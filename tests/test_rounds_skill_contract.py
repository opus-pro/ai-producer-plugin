"""Keep the two settle-before-cutting rounds aligned with the cards the service draws."""
from pathlib import Path
import base64
import hashlib
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/aip/skills/aip/SKILL.md"
CAPTION_SKILL = ROOT / "plugins/aip/skills/aip-dynamic-caption/SKILL.md"
CARD_BUNDLE = ROOT / "plugins/aip/assets/decision-card/decision-card.js"

# The service's card options, in the order its cards list them.
ROUGH_CUT_BOLDNESS = ["off", "conservative", "balanced", "aggressive"]
CAPTION_PATTERNS = [
    "blur-ladder",
    "editorial-stack",
    "inverted-stack",
    "lead-in-flare",
    "pace-adaptive",
    "scribble-subtitle",
    "solo-word-punch",
    "tilt-slam",
]
FINE_CUT_COMPONENTS = [
    "editing_preference_example",
    "editing_preference",
    "reference_image",
    "visual_preference_prompt",
]


def section(text: str, start: str) -> str:
    return text[text.index(start):].split("\n\n", 1)[0]


class RoundsSkillContractTests(unittest.TestCase):
    def setUp(self):
        self.skill = SKILL.read_text(encoding="utf-8")

    def test_only_rough_cut_and_finishes_are_carded(self):
        rows = re.findall(r"^\| (Rough cut|Finishes|Fine cut) \| `(\w+)` \| (.+?) \|", self.skill, re.MULTILINE)
        self.assertEqual(
            [(name, card, re.findall(r"`(\w+)`", components)) for name, card, components in rows],
            [
                ("Rough cut", "roughcut", ["rough_cut_boldness"]),
                ("Finishes", "finishing", ["caption_style", "bgm_enabled", "sfx_enabled"]),
            ],
        )
        self.assertIn("`bgm_enabled=on`, `sfx_enabled=off`", self.skill)

    def test_rough_cut_names_the_four_boldness_values_in_card_order(self):
        rough_cut = section(self.skill, "**Rough cut.**")
        positions = [rough_cut.index(f"`{value}`") for value in ROUGH_CUT_BOLDNESS]
        self.assertEqual(positions, sorted(positions))

    def test_finishes_offers_no_caption_and_the_service_patterns(self):
        self.assertIn("`no-caption` (\"No captions\") and eight caption patterns", self.skill)
        rows = re.findall(r"^\|[^|]+\| `([a-z-]+)`\s+\|", CAPTION_SKILL.read_text(encoding="utf-8"), re.MULTILINE)
        self.assertEqual(rows, CAPTION_PATTERNS)

    def test_fine_cut_components_are_refused_even_when_offered(self):
        fine_cut = section(self.skill, "**Fine cut.**")
        self.assertIn("The fine cut is not a round.", fine_cut)
        self.assertIn("even when `present_choices` offers components for them", fine_cut)
        for component in FINE_CUT_COMPONENTS:
            self.assertIn(f"`{component}`", fine_cut)
        self.assertIn("styling reference for palette and type; use it without asking for one or recording it", fine_cut)

    def test_hosts_that_draw_the_card_keep_the_card_flow(self):
        self.assertIn("Each round is one card: call `present_choices` with that round's components, end your turn, and wait.", self.skill)
        hosts = section(self.skill, "**Hosts that show the card as data.**")
        self.assertIn("Hosts with neither of the two tools named below draw the card: run the rounds as above.", hosts)

    def test_widget_hosts_draw_the_pinned_bundle_as_written(self):
        hosts = section(self.skill, "**Hosts that show the card as data.**")
        self.assertIn("When a tool named exactly `show_widget` is among your tools", hosts)
        script = re.search(
            r'<script src="https://cdn\.jsdelivr\.net/gh/opus-pro/ai-producer-plugin@([0-9a-f]{40})/plugins/aip/assets/decision-card/decision-card\.js" integrity="(sha384-[A-Za-z0-9+/=]+)" crossorigin="anonymous"></script>',
            self.skill,
        )
        self.assertIsNotNone(script, "the widget must load the bundle pinned to a commit, with its integrity")
        assert script is not None
        expected = "sha384-" + base64.b64encode(hashlib.sha384(CARD_BUNDLE.read_bytes()).digest()).decode()
        self.assertEqual(script.group(2), expected, "the pinned integrity must match the bundle this package ships")
        self.assertIn('<script>AIPDecisionCard.render(RESULT, { mount: "aip-card", key: "roughcut-1" })</script>', self.skill)
        self.assertIn("A tool with a similar name or purpose does not stand in for `show_widget`", self.skill)

    def test_terminal_hosts_ask_each_round_without_the_card(self):
        terminal = section(self.skill, "Without `show_widget`, a host whose tools include one named exactly `AskUserQuestion`")
        self.assertIn("so do not call `present_choices` there", terminal)
        self.assertIn("at most four options each", terminal)
        self.assertIn("letting the run choose, which records no `caption_style`", terminal)
        self.assertIn("Write down the token each chosen option stands for, never the label the user saw.", terminal)


if __name__ == "__main__":
    unittest.main()
