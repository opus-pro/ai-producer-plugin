"""Keep host-authored frame_speaker windows on the source clock.

A host's cut lives in its own tree until it commits, so a window on the cut is
mapped through whatever cut the service last saw. The framing skill therefore
names each window's footage in the original upload, and the cutout's source
layer starts at the footage that window named.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/aip/skills/aip-framing/SKILL.md"
CUTOUT = ROOT / "plugins/aip/skills/aip-framing/references/cutout.md"


class FramingSkillContractTests(unittest.TestCase):
    def test_measurement_names_windows_in_source_milliseconds(self) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        measurement = skill.split("4. **The measurement, before you place.**", 1)[1].split("\n5. ", 1)[0]
        self.assertIn("`source_start_ms` and `source_end_ms`", measurement)
        self.assertIn("whole milliseconds into the original upload", measurement)
        self.assertIn("`data-media-start` plus the beat's offset into that clip, times 1000", measurement)
        self.assertIn("two windows, one per clip", measurement)
        self.assertNotIn("`start` and `end` on the cut", measurement)

    def test_caption_windows_stay_on_the_cut(self) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        self.assertIn("pass each moment's window on the cut to the caption call", skill)

    def test_cutout_window_and_source_layer_share_the_named_footage(self) -> None:
        cutout = CUTOUT.read_text(encoding="utf-8")
        self.assertIn("Name exactly that footage as `source_start_ms` and `source_end_ms`", cutout)
        self.assertIn("split at the cut: one cutout beat per clip, each with its own window", cutout)
        self.assertIn("`data-media-start` at the window's `source_start_ms` / 1000", cutout)
        self.assertNotIn("the beat's `start` and `end`", cutout)
        self.assertNotIn("the source seconds of the beat's start", cutout)


if __name__ == "__main__":
    unittest.main()
