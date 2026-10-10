"""Keep the two settle-before-cutting rounds aligned with the cards the service draws."""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/aip/skills/aip/SKILL.md"
CAPTION_SKILL = ROOT / "plugins/aip/skills/aip-dynamic-caption/SKILL.md"

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


if __name__ == "__main__":
    unittest.main()
