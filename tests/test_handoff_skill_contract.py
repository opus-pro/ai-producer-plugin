"""Pin the handoff skill's call order for a pasted Motion library reference."""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/aip/skills/aip-handoff/SKILL.md"
ENTRY_SKILL = ROOT / "plugins/aip/skills/aip/SKILL.md"

MOTION_ASSET_LINE = "@aip p=C1EXAMPLE0000 t=6.72 motion-asset id=text-subscribe version=4.0.0"
CUTOUT_PACKAGE_LINE = "@aip p=C1EXAMPLE0000 t=6.72 motion-asset id=frame-green-screen version=1.0.0"


def numbered_step(skill: str, number: int) -> str:
    """The body of one numbered step, including its sub-bullets."""
    match = re.search(rf"^{number}\. (.*?)(?=^\d+\. |^## )", skill, re.MULTILINE | re.DOTALL)
    assert match, f"step {number} is missing"
    return match.group(1)


class HandoffSkillContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill = SKILL.read_text(encoding="utf-8")

    def test_description_matches_a_pasted_reference_line(self) -> None:
        description = re.search(r"^description:\s*(.+)$", self.skill, re.MULTILINE).group(1)
        self.assertIn("@aip", description)
        for kind in ("motion-asset", "omni-preset"):
            self.assertIn(kind, description)
        # The entry skill routes a pasted line here, so the host loads it without a catalogue.
        self.assertIn("(../aip-handoff/SKILL.md)", ENTRY_SKILL.read_text(encoding="utf-8"))

    def test_motion_asset_reference_resolves_lists_then_places_without_a_question(self) -> None:
        kind = re.search(r"(\w[\w-]*) id=", MOTION_ASSET_LINE).group(1)
        self.assertEqual(kind, "motion-asset")
        resolve = numbered_step(self.skill, 1)
        place = numbered_step(self.skill, 2)
        self.assertIn("`resolve_selection`", resolve)
        self.assertIn("before any other call", resolve)
        # Within the placement step the listing precedes the write, and the write is the
        # one `next` names for `add`: no measurement, no choice card, no authoring.
        add_clause = place.split("- `chooseInput`")[0]
        self.assertLess(add_clause.index("`list_motion_assets`"), add_clause.index("`materialize_motion_asset`"))
        self.assertIn("`expected_project_revision` equal to the listed `project_revision`", add_clause)
        self.assertIn("Ask nothing", add_clause)
        for tool in ("`present_choices`", "`frame_speaker`", "`get_motion_asset`", "`sign_workspace_upload`"):
            self.assertNotIn(tool, add_clause)
        # A choice card is offered only where the listing says inputs are missing.
        self.assertIn("`chooseInput`: `next` names the input keys", place)

    def test_cutout_package_windows_come_from_next_and_never_cross_a_cut(self) -> None:
        self.assertIn("motion-asset", CUTOUT_PACKAGE_LINE)
        place = numbered_step(self.skill, 2)
        self.assertIn("`next` carries `frame_speaker` arguments", place)
        rules = self.skill.split("## What a cutout placement keeps", 1)[1].split("## ", 1)[0]
        self.assertIn("one matte window per kept span", rules)
        self.assertIn("Run it as supplied", rules)
        self.assertIn("never open one window across the whole effect", rules)
        self.assertIn("a window that crosses a cut is refused", rules)
        # Each window binds as its own segment with its own file, cut times, and geometry.
        self.assertIn("one segment per accepted window", rules)
        for field in ("`start_ms`", "`end_ms`", "`sink_px`", "`card_clip_top_px`", "`head_top_px`", "`head_bottom_px`"):
            self.assertIn(field, rules)
        # A stale revision re-cuts only the spans that moved and keeps the rest.
        self.assertIn("re-run `frame_speaker` only for the spans that moved", rules)


if __name__ == "__main__":
    unittest.main()
