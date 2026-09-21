"""Exercise local progressive plans and accepted-receipt transitions."""

from contextlib import nullcontext
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from editing_script_fixtures import write_editing_script


SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/aip/skills/aip/scripts"
sys.path.insert(0, str(SCRIPTS))
from progressive_publish import ProgressCheckpoint, SERVER_RUNTIME_PATHS, SIGN_BATCH_SIZE


def index(count=0, duration=59.85):
    av = "".join(
        f'<{tag} id="{identifier}" class="clip speaker-clip" data-hf-id="speaker-main" '
        f'src="public/source.{extension}" data-start="0" data-duration="{duration}" '
        f'data-media-start="0" data-track-index="{track}" data-volume="{volume}"></{tag}>'
        for tag, identifier, extension, track, volume in [
            ("video", "speaker", "mp4", 0, 0), ("audio", "speaker-audio", "mp3", 2, 1)])
    hosts = "".join(
        f'<div class="visual-host clip" data-composition-id="beat{i}" '
        f'data-composition-src="compositions/beat{i}.html" data-start="{i}" '
        'data-duration="1" data-track-index="3"></div>' for i in range(count))
    return f'<div id="stage" data-composition-id="finecut-root" data-start="0" data-duration="{duration}">{av}{hosts}</div>'


class ProgressivePublishTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "index.html").write_text(index(), encoding="utf-8")
        write_editing_script(self.root)
        self.progress = ProgressCheckpoint(
            self.root,
            "test-project",
            59.85,
            "initial",
            ["render-engine/public/source.mp4", "render-engine/public/source.mp3"],
        )

    def author(self, count, duration=59.85):
        (self.root / "index.html").write_text(index(count, duration), encoding="utf-8")
        child = self.root / f"compositions/beat{count - 1}.html"
        child.parent.mkdir(exist_ok=True)
        child.write_text(
            f'<template><div data-composition-id="beat{count - 1}"></div></template>',
            encoding="utf-8",
        )
        return ["index.html", child.relative_to(self.root).as_posix()]

    def accept(self, plan, count, extras=(), warnings=()):
        accepted = [row["path"] for row in plan["expected_files"]] + list(extras)
        return self.progress.accept(f"task-{count}", f"revision-{count}", accepted, warnings)

    def test_six_effects_are_planned_and_accepted_one_at_a_time(self):
        plans = []
        reports = []
        for count in range(1, 7):
            plan = self.progress.prepare(self.author(count), final=count == 6)
            plans.append(plan)
            self.assertEqual(plan["published_effects"], count)
            reports.append(self.accept(plan, count))
            self.assertEqual(reports[-1]["published_effects"], count)
        self.assertEqual([row["duration_seconds"] for row in reports], [59.85] * 6)
        self.assertEqual([row["authoring"] for row in plans], [True] * 5 + [False])
        self.assertEqual([row["base_digest"] for row in plans],
                         ["initial"] + [f"revision-{i}" for i in range(1, 6)])
        self.assertEqual(self.progress.status, "finished")
        with self.assertRaisesRegex(RuntimeError, "checkpoint_closed"):
            self.progress.prepare(self.author(6))

    def stage_media(self, files):
        """Add one user-supplied and one agent-found image to a batch."""
        for name in ["user-photo.jpg", "found-logo.png"]:
            image = self.root / "public/images" / name
            image.parent.mkdir(parents=True, exist_ok=True)
            image.write_bytes(name.encode("ascii"))
        return files + ["public/images/user-photo.jpg", "public/images/found-logo.png"]

    def test_staged_media_says_who_supplied_each_file(self):
        files = self.stage_media(self.author(1))
        plan = self.progress.prepare(files, uploads=["public/images/user-photo.jpg"])
        self.assertEqual(plan["asset_origins"], [
            {"path": "render-engine/public/images/user-photo.jpg", "origin": "upload"},
            {"path": "render-engine/public/images/found-logo.png", "origin": "agent"},
        ])

    def test_documents_alone_declare_no_origin(self):
        plan = self.progress.prepare(self.author(1))
        self.assertNotIn("asset_origins", plan)

    def test_a_supplied_file_this_batch_does_not_stage_is_refused_before_the_plan(self):
        files = self.stage_media(self.author(1))
        for upload in ["public/images/absent.jpg", "index.html"]:
            with self.assertRaises(ValueError):
                self.progress.prepare(files, uploads=[upload])
            self.assertEqual(self.progress.status, "ready")
        plan = self.progress.prepare(files, uploads=["public/images/user-photo.jpg"])
        self.assertEqual(self.accept(plan, 1)["published_effects"], 1)

    def test_six_effects_resume_from_separate_model_checkpoints(self):
        state = self.progress.checkpoint()
        for count in range(1, 7):
            progress = ProgressCheckpoint.resume(self.root, state)
            plan = progress.prepare(self.author(count), final=count == 6)
            prepared = progress.checkpoint()
            self.assertEqual(prepared["status"], "prepared")
            progress = ProgressCheckpoint.resume(self.root, prepared)
            accepted = [row["path"] for row in plan["expected_files"]]
            progress.accept(f"task-{count}", f"revision-{count}", accepted)
            state = progress.checkpoint()
            self.assertEqual(state["publications"], count)
            self.assertEqual(state["status"], "finished" if count == 6 else "ready")

    def test_short_partial_is_rejected_before_a_plan_exists(self):
        with self.assertRaisesRegex(ValueError, "planned_duration_mismatch"):
            self.progress.prepare(self.author(1, 20.2))
        self.assertEqual(self.progress.status, "ready")

    def test_service_runtime_paths_are_accepted_alongside_requested_files(self):
        plan = self.progress.prepare(self.author(1), final=True)
        self.accept(plan, 1, sorted(SERVER_RUNTIME_PATHS))
        self.assertEqual(self.progress.status, "finished")
        self.assertIn("public/vendor/fit-engine.js", self.progress.remote)

    def test_signing_plan_obeys_the_service_batch_limit(self):
        files = self.author(1)
        composition = self.root / "compositions/beat0.html"
        dependencies = []
        for number in range(SIGN_BATCH_SIZE):
            relative = f"styles/dependency-{number}.css"
            dependency = self.root / relative
            dependency.parent.mkdir(exist_ok=True)
            dependency.write_text(f".dependency-{number} {{ color: black; }}", encoding="utf-8")
            dependencies.append(relative)
        composition.write_text(
            "<template><div data-composition-id=\"beat0\"></div></template>"
            + "".join(f'<link rel="stylesheet" href="{path}">' for path in dependencies),
            encoding="utf-8",
        )
        plan = self.progress.prepare(files + dependencies)
        self.assertEqual([len(batch) for batch in plan["sign_batches"]], [SIGN_BATCH_SIZE, 3])

    def test_unexpected_document_in_receipt_stops_acceptance(self):
        plan = self.progress.prepare(self.author(1))
        with self.assertRaisesRegex(ValueError, "receipt_mismatch"):
            self.accept(plan, 1, ["render-engine/compositions/unexpected.html"])
        self.assertEqual(self.progress.status, "prepared")

    def test_three_effect_batch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_effect_transition"):
            self.progress.prepare(self.author(3))
        self.assertEqual(self.progress.status, "ready")

    def test_local_but_unpublished_dependency_is_rejected(self):
        files = self.author(1)
        (self.root / "compositions/beat0.html").write_text(
            '<template><div data-composition-id="beat0"><img src="public/new.png"></div></template>',
            encoding="utf-8",
        )
        (self.root / "public").mkdir()
        (self.root / "public/new.png").write_bytes(b"new image")
        with self.assertRaisesRegex(ValueError, "missing_local_reference"):
            self.progress.prepare(files)

    def test_future_effect_file_is_rejected(self):
        files = self.author(1)
        (self.root / "compositions/beat1.html").write_text(
            '<template><div data-composition-id="beat1"></div></template>', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "future_effect_files_present"):
            self.progress.prepare(files)

    def test_prior_accepted_effect_cannot_change(self):
        plan = self.progress.prepare(self.author(1))
        self.accept(plan, 1)
        (self.root / "compositions/beat0.html").write_text("<template>changed</template>", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "accepted_file_changed"):
            self.progress.prepare(self.author(2))

    def test_prepared_file_cannot_change_before_receipt(self):
        plan = self.progress.prepare(self.author(1))
        (self.root / "compositions/beat0.html").write_text("<template>changed</template>", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "prepared_file_changed"):
            self.accept(plan, 1)
        self.assertEqual(self.progress.status, "prepared")

    def test_prepared_checkpoint_cannot_prepare_another_effect(self):
        self.progress.prepare(self.author(1))
        with self.assertRaisesRegex(RuntimeError, "checkpoint_closed"):
            self.progress.prepare(self.author(2))

    def test_warning_codes_are_bounded(self):
        plan = self.progress.prepare(self.author(1), final=True)
        report = self.accept(plan, 1, warnings=["runtime_check_unavailable", "unsafe warning", "x" * 101])
        self.assertEqual(report["warning_codes"], ["runtime_check_unavailable"])

    def test_snapshot_alias_is_resolved_for_preflight(self):
        files = self.author(1)
        physical = self.root / "snapshot-physical"
        physical.mkdir()
        alias = self.root / "snapshot-alias"
        alias.symlink_to(physical, target_is_directory=True)
        with patch("progressive_publish.tempfile.TemporaryDirectory", return_value=nullcontext(str(alias))):
            plan = self.progress.prepare(files, final=True)
        self.assertEqual(sum(len(batch) for batch in plan["sign_batches"]), 3)


if __name__ == "__main__":
    unittest.main()
