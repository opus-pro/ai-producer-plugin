"""Unit tests for the offline progressive-publication guard."""

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "plugins/aip/skills/aip/scripts/publication_guard.py"
SPEC = importlib.util.spec_from_file_location("publication_guard", SCRIPT)
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


def speaker(start, duration, media_start, suffix=""):
    return (
        f'<video id="speaker{suffix}" class="clip speaker-clip" src="public/source.mp4" data-hf-id="cut{suffix}" '
        f'data-start="{start}" data-duration="{duration}" data-media-start="{media_start}" data-track-index="0" data-volume="0"></video>'
        f'<audio id="speaker-audio{suffix}" class="clip speaker-clip" src="public/source.mp3" data-hf-id="cut{suffix}" '
        f'data-start="{start}" data-duration="{duration}" data-media-start="{media_start}" data-track-index="0" data-volume="1"></audio>'
    )


def effect(number):
    return (f'<div class="visual-host clip" data-composition-id="effect-{number}" '
            f'data-composition-src="compositions/effect-{number}.html" data-start="{number}" '
            f'data-duration="1" data-track-index="{number + 1}"></div>')


def index(duration=59.85, effects=(), clips=None, caption=""):
    clips = speaker(0, duration, 0) if clips is None else clips
    return f'<div id="stage" data-composition-id="finecut-root" data-start="0" data-duration="{duration}">{clips}{"".join(effects)}{caption}</div>'


class PublicationGuardTests(unittest.TestCase):
    def assert_code(self, code, *args):
        with self.assertRaisesRegex(ValueError, f"^{code}$"):
            guard.validate_progress(*args)

    def test_rejects_candidate_duration_that_changes_planned_cut(self):
        baseline = index(duration=59.85)
        self.assert_code("planned_duration_mismatch", baseline, baseline, index(duration=20.2, effects=[effect(1)]), 59.85)

    def test_adds_one_effect_at_each_of_six_publications(self):
        baseline = index()
        previous = baseline
        for number in range(1, 7):
            candidate = index(effects=[effect(n) for n in range(1, number + 1)])
            snapshot = guard.validate_progress(baseline, previous, candidate, 59.85)
            self.assertEqual(snapshot["duration"], 59.85)
            self.assertEqual(len(snapshot["effects"]), number)
            previous = candidate

    def test_rejects_three_effect_batch(self):
        baseline = index()
        self.assert_code("invalid_effect_transition", baseline, baseline, index(effects=[effect(1), effect(2), effect(3)]), 59.85)

    def test_rejects_changed_speaker_media_offset(self):
        baseline = index()
        changed = index(clips=speaker(0, 59.85, 0.5), effects=[effect(1)])
        self.assert_code("speaker_timeline_changed", baseline, baseline, changed, 59.85)

    def test_accepts_legitimate_trim_in_initial_baseline(self):
        clips = speaker(0, 20.2, 39.65)
        baseline = index(duration=20.2, clips=clips)
        snapshot = guard.validate_progress(baseline, baseline, index(duration=20.2, clips=clips, effects=[effect(1)]), 20.2)
        self.assertEqual(snapshot["duration"], 20.2)

    def test_rejects_malformed_and_duplicate_ids(self):
        baseline = index()
        self.assert_code("invalid_index_html", baseline, baseline, '<div id="stage">', 59.85)
        duplicate = index(effects=[effect(1), effect(1)])
        self.assert_code("duplicate_effect_id", baseline, baseline, duplicate, 59.85)

    def test_rejects_a_second_stage_even_without_a_second_root(self):
        baseline = index()
        candidate = index(effects=[effect(1)]) + '<div id="stage"></div>'
        self.assert_code("invalid_root", baseline, baseline, candidate, 59.85)

    def test_caption_hosts_do_not_count_as_effects(self):
        baseline = index()
        caption = ('<div class="visual-host clip" data-composition-id="narrator-captions" '
                   'data-composition-src="compositions/narrator_captions.html" data-start="0" '
                   'data-duration="59.85" data-track-index="9"></div>')
        self.assert_code("invalid_effect_transition", baseline, baseline, index(caption=caption), 59.85)
        snapshot = guard.validate_progress(baseline, baseline, index(effects=[effect(1)], caption=caption), 59.85)
        self.assertEqual(set(snapshot["effects"]), {"effect-1"})

    def test_requires_complete_paired_audio_video_coverage(self):
        baseline = index(clips=speaker(0, 20, 0))
        self.assert_code("incomplete_speaker_coverage", baseline, baseline, index(effects=[effect(1)]), 20)


if __name__ == "__main__":
    unittest.main()
