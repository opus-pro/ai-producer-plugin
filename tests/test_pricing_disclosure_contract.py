"""Pin when the entry skill speaks about the cost of preparing a project."""
from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/aip/skills/aip/SKILL.md"


class PreparationPriceDisclosureTest(unittest.TestCase):
    def test_price_is_announced_only_when_preparation_charges(self) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        self.assertIn("When it charges, whatever you say when you start preparation carries the price", skill)
        self.assertIn("When it is free, say nothing about money, not even that it is free", skill)
        self.assertIn("no zero amount, no credits, no note about free usage or a limited time", skill)
        self.assertIn("A user who asks what something costs is answered from `get_pricing` either way", skill)

    def test_no_unconditional_preparation_price_rule(self) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        self.assertNotIn("Preparation spends, so whatever you say when you start it carries its price", skill)


if __name__ == "__main__":
    unittest.main()
