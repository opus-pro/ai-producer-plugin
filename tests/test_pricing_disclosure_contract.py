"""Pin when the entry skill speaks about the cost of preparing a project."""
from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/aip/skills/aip/SKILL.md"


class PreparationPriceDisclosureTest(unittest.TestCase):
    def setUp(self) -> None:
        self.skill = SKILL.read_text(encoding="utf-8")

    def test_price_is_announced_only_when_preparation_can_charge(self) -> None:
        self.assertIn("When it can charge, whatever you say when you start preparation carries the price", self.skill)
        self.assertIn("When it is free, that message says nothing about money, not even that it is free", self.skill)
        self.assertIn("no zero amount, no credits, no note about free usage or a limited time", self.skill)

    def test_quota_first_preparation_counts_as_charging(self) -> None:
        self.assertIn("Preparation is free only when its row is in the `free` band", self.skill)
        self.assertIn("a row with a `per_unit` price can charge, including one a daily quota may cover first", self.skill)

    def test_user_initiated_cost_talk_is_always_answered(self) -> None:
        self.assertIn("asks to talk the edit through before anything is spent, is answered from `get_pricing` either way, free included", self.skill)
        self.assertIn("tell them what preparing costs", self.skill)
        self.assertIn("A free usage status or refusal the service reports later is passed on as it reads", self.skill)

    def test_no_unconditional_preparation_price_rule(self) -> None:
        self.assertNotIn("Preparation spends, so whatever you say when you start it carries its price", self.skill)


if __name__ == "__main__":
    unittest.main()
