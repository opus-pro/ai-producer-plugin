"""Exercise isolated effect drafts while the previous publication is pending."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/aip/skills/aip/scripts"
sys.path.insert(0, str(SCRIPTS))
import progressive_checkpoint as checkpoint
import progressive_publish as publication
from progressive_checkpoint import accept, fail, initialize, prepare, read_checkpoint


DURATION = 59.85
REMOTE_FILES = ["render-engine/public/source.mp4", "render-engine/public/source.mp3"]


def index(count=0, duration=DURATION):
    speaker = "".join(
        f'<{tag} id="{identifier}" class="clip speaker-clip" data-hf-id="speaker-main" '
        f'src="public/source.{extension}" data-start="0" data-duration="{duration}" '
        f'data-media-start="0" data-track-index="{track}" data-volume="{volume}"></{tag}>'
        for tag, identifier, extension, track, volume in [
            ("video", "speaker", "mp4", 0, 0), ("audio", "speaker-audio", "mp3", 2, 1)])
    effects = "".join(
        f'<div class="visual-host clip" data-composition-id="beat{i}" '
        f'data-composition-src="compositions/beat{i}.html" data-start="{i}" '
        'data-duration="1" data-track-index="3"></div>' for i in range(count))
    return (f'<div id="stage" data-composition-id="finecut-root" data-start="0" '
            f'data-duration="{duration}">{speaker}{effects}</div>')


def author(directory, count, duration=DURATION):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "index.html").write_text(index(count, duration), encoding="utf-8")
    relative = f"compositions/beat{count - 1}.html"
    child = directory / relative
    child.parent.mkdir(exist_ok=True)
    child.write_text(
        f'<template><div data-composition-id="beat{count - 1}">Effect {count}</div></template>',
        encoding="utf-8",
    )
    return ["index.html", relative]


def workspace_bytes(directory):
    return {path.relative_to(directory).as_posix(): path.read_bytes()
            for path in directory.rglob("*") if path.is_file()}


def receipt_files(plan):
    return [row["path"] for row in plan["expected_files"]]


class ProgressiveDraftTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root, self.state_path = self.initialize_at(self.base / "overlapped")

    def initialize_at(self, directory):
        root = directory / "render-engine"
        root.mkdir(parents=True)
        (root / "index.html").write_text(index(), encoding="utf-8")
        state_path = directory / ".aip-progress.json"
        initialize(root, state_path, "test-project", DURATION, "initial", REMOTE_FILES)
        return root, state_path

    def prepare_first(self):
        return prepare(self.root, self.state_path, author(self.root, 1))

    def accept_first(self, plan):
        return accept(self.root, self.state_path, "task-1", "revision-1", receipt_files(plan))

    def accepted_first_and_draft(self):
        plan = self.prepare_first()
        draft = self.base / "draft-2"
        files = author(draft, 2)
        self.accept_first(plan)
        return draft, files

    def assert_rejected_without_publication(self, draft, files, pattern=None):
        published = workspace_bytes(self.root)
        state = self.state_path.read_bytes()
        context = (self.assertRaisesRegex(ValueError, pattern) if pattern
                   else self.assertRaises(ValueError))
        with context:
            prepare(self.root, self.state_path, files, draft=draft)
        self.assertEqual(workspace_bytes(self.root), published)
        self.assertEqual(self.state_path.read_bytes(), state)

    def start_waiting_draft(self, draft, files):
        observed_prepared = threading.Event()
        completed = threading.Event()
        outcome = {}

        def observe_state(path):
            state = read_checkpoint(path)
            if state["status"] == "prepared":
                observed_prepared.set()
            return state

        def run():
            try:
                outcome["plan"] = prepare(
                    self.root, self.state_path, files, draft=draft, after_effect=1, wait_seconds=1)
            except Exception as error:
                outcome["error"] = error
            finally:
                completed.set()

        observer = patch.object(checkpoint, "read_checkpoint", side_effect=observe_state)
        observer.start()
        self.addCleanup(observer.stop)
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 1.1)
        self.assertTrue(observed_prepared.wait(1), "Draft never observed the pending publication")
        self.assertFalse(completed.is_set(), outcome)
        return completed, outcome

    def test_drafting_next_effect_preserves_prepared_bytes_hashes_and_receipt(self):
        first = self.prepare_first()
        published = workspace_bytes(self.root)
        prepared = read_checkpoint(self.state_path)
        draft = self.base / "draft-2"
        files = author(draft, 2)
        self.assertEqual(set(workspace_bytes(draft)), set(files))
        self.assertEqual(workspace_bytes(self.root), published)
        self.assertEqual(read_checkpoint(self.state_path), prepared)
        for row in first["expected_files"]:
            relative = row["path"].removeprefix("render-engine/")
            self.assertEqual(hashlib.sha256(published[relative]).hexdigest(), row["sha256"])
        report = self.accept_first(first)
        self.assertEqual(report["published_effects"], 1)
        self.assertEqual(read_checkpoint(self.state_path)["digest"], "revision-1")
        self.assertEqual(workspace_bytes(self.root), published)

    def test_next_prepare_requires_exact_previous_acceptance(self):
        first = self.prepare_first()
        draft = self.base / "draft-2"
        files = author(draft, 2)
        published = workspace_bytes(self.root)
        prepared = self.state_path.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "checkpoint_closed"):
            prepare(self.root, self.state_path, files, draft=draft)
        with self.assertRaisesRegex(ValueError, "receipt_mismatch"):
            accept(self.root, self.state_path, "task-1", "revision-1", ["render-engine/index.html"])
        with self.assertRaisesRegex(RuntimeError, "checkpoint_closed"):
            prepare(self.root, self.state_path, files, draft=draft)
        self.assertEqual(workspace_bytes(self.root), published)
        self.assertEqual(self.state_path.read_bytes(), prepared)

        self.accept_first(first)
        accepted = read_checkpoint(self.state_path)
        second = prepare(self.root, self.state_path, files, draft=draft)
        state = read_checkpoint(self.state_path)
        self.assertEqual(second["base_digest"], "revision-1")
        self.assertEqual(second["published_effects"], 2)
        self.assertEqual(second["duration_seconds"], DURATION)
        self.assertEqual(state["schema"], accepted["schema"])
        self.assertEqual(state["baseline"], accepted["baseline"])
        self.assertEqual(state["effects"], accepted["effects"])
        self.assertEqual(state["accepted_hashes"], accepted["accepted_hashes"])
        self.assertEqual(state["pending"]["effects"]["beat0"], accepted["effects"]["beat0"])
        self.assertEqual((self.root / "compositions/beat0.html").read_bytes(),
                         published["compositions/beat0.html"])
        for relative in files:
            self.assertEqual((self.root / relative).read_bytes(), (draft / relative).read_bytes())

    def test_waiting_draft_prepares_only_after_previous_receipt_is_accepted(self):
        first = self.prepare_first()
        published = workspace_bytes(self.root)
        prepared = self.state_path.read_bytes()
        draft = self.base / "draft-2"
        files = author(draft, 2)
        completed, outcome = self.start_waiting_draft(draft, files)
        self.assertEqual(workspace_bytes(self.root), published)
        self.assertEqual(self.state_path.read_bytes(), prepared)
        self.assertFalse(completed.wait(0.02))

        self.accept_first(first)
        self.assertTrue(completed.wait(1), "Draft did not resume after the accepted receipt")
        self.assertNotIn("error", outcome)
        self.assertEqual(outcome["plan"]["base_digest"], "revision-1")
        self.assertEqual(outcome["plan"]["published_effects"], 2)
        state = read_checkpoint(self.state_path)
        self.assertEqual(state["status"], "prepared")
        self.assertEqual(state["publications"], 1)
        self.assertEqual(set(state["pending"]["effects"]), {"beat0", "beat1"})
        for relative in files:
            self.assertEqual((self.root / relative).read_bytes(), (draft / relative).read_bytes())

    def test_ready_checkpoint_waits_for_previous_publisher_to_release_lock(self):
        draft, files = self.accepted_first_and_draft()
        published = workspace_bytes(self.root)
        ready = self.state_path.read_bytes()
        attempted = threading.Event()
        completed = threading.Event()
        outcome = {}
        acquire = checkpoint.checkpoint_lock

        def observe_lock(path):
            attempted.set()
            return acquire(path)

        def run():
            try:
                outcome["plan"] = prepare(
                    self.root, self.state_path, files, draft=draft, after_effect=1, wait_seconds=1)
            except Exception as error:
                outcome["error"] = error
            finally:
                completed.set()

        thread = threading.Thread(target=run, daemon=True)
        self.addCleanup(thread.join, 1.1)
        with patch.object(checkpoint, "checkpoint_lock", side_effect=observe_lock):
            with acquire(self.state_path):
                self.assertEqual(read_checkpoint(self.state_path)["status"], "ready")
                thread.start()
                self.assertTrue(attempted.wait(1), "Draft never attempted the publication lock")
                self.assertFalse(completed.wait(0.02), outcome)
                self.assertEqual(workspace_bytes(self.root), published)
                self.assertEqual(self.state_path.read_bytes(), ready)
            self.assertTrue(completed.wait(1), "Draft did not resume after the publisher released its lock")
        self.assertNotIn("error", outcome)
        self.assertEqual(outcome["plan"]["base_digest"], "revision-1")
        self.assertEqual(outcome["plan"]["published_effects"], 2)
        self.assertEqual(read_checkpoint(self.state_path)["status"], "prepared")

    def test_warning_codes_survive_resumed_accepts_and_appear_in_final_receipt(self):
        warnings = (("runtime_check_unavailable",),
                    ("asset_warning", "runtime_check_unavailable"), ())
        expected = set()
        for count, codes in enumerate(warnings, start=1):
            draft = self.base / f"draft-{count}"
            plan = prepare(self.root, self.state_path, author(draft, count),
                           draft=draft, final=count == len(warnings))
            report = accept(self.root, self.state_path, f"task-{count}", f"revision-{count}",
                            receipt_files(plan), warning_codes=codes)
            expected.update(codes)
            state = read_checkpoint(self.state_path)
            self.assertEqual(state["schema"], 3)
            self.assertEqual(state["warning_codes"], sorted(expected))
            self.assertEqual(report["warning_codes"], sorted(expected))
        self.assertTrue(report["final"])
        self.assertEqual(state["status"], "finished")
        self.assertEqual(report["warning_codes"], ["asset_warning", "runtime_check_unavailable"])

    def test_publisher_failure_wakes_waiting_draft_without_changing_root(self):
        first = self.prepare_first()
        published = workspace_bytes(self.root)
        draft = self.base / "draft-2"
        files = author(draft, 2)
        completed, outcome = self.start_waiting_draft(draft, files)
        report = fail(self.root, self.state_path, 1)
        self.assertTrue(completed.wait(1), "Draft did not stop after publication failed")
        self.assertNotIn("plan", outcome)
        self.assertIsInstance(outcome["error"], RuntimeError)
        self.assertIn("previous_publication_not_accepted", str(outcome["error"]))
        self.assertEqual(report, {"status": "failed", "published_effects": 0})
        state = read_checkpoint(self.state_path)
        self.assertEqual(state["status"], "failed")
        self.assertIsNone(state["pending"])
        self.assertEqual(state["digest"], "initial")
        self.assertEqual(workspace_bytes(self.root), published)
        failed = self.state_path.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "checkpoint_not_prepared"):
            self.accept_first(first)
        self.assertEqual(self.state_path.read_bytes(), failed)

    def test_delayed_failure_does_not_poison_accepted_effect_or_next_preparation(self):
        draft, files = self.accepted_first_and_draft()
        for next_prepared in (False, True):
            with self.subTest(next_prepared=next_prepared):
                if next_prepared:
                    prepare(self.root, self.state_path, files, draft=draft)
                published = workspace_bytes(self.root)
                state = self.state_path.read_bytes()
                self.assertEqual(fail(self.root, self.state_path, 1),
                                 {"status": "already_accepted", "published_effects": 1})
                self.assertEqual(workspace_bytes(self.root), published)
                self.assertEqual(self.state_path.read_bytes(), state)

    def test_failure_for_future_effect_is_refused_without_state_or_file_changes(self):
        self.prepare_first()
        published = workspace_bytes(self.root)
        state = self.state_path.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "publication_failure_mismatch"):
            fail(self.root, self.state_path, 2)
        self.assertEqual(workspace_bytes(self.root), published)
        self.assertEqual(self.state_path.read_bytes(), state)

    def test_zero_wait_times_out_without_changing_prepared_publication(self):
        self.prepare_first()
        draft = self.base / "draft-2"
        files = author(draft, 2)
        published = workspace_bytes(self.root)
        prepared = self.state_path.read_bytes()
        with self.assertRaisesRegex(TimeoutError, "publication_join_timeout"):
            prepare(self.root, self.state_path, files, draft=draft, after_effect=1, wait_seconds=0)
        self.assertEqual(workspace_bytes(self.root), published)
        self.assertEqual(self.state_path.read_bytes(), prepared)

    def test_wrong_previous_effect_count_is_refused_before_publication(self):
        first = self.prepare_first()
        draft = self.base / "draft-2"
        files = author(draft, 2)
        published = workspace_bytes(self.root)
        for accepted in (False, True):
            with self.subTest(previous_accepted=accepted):
                if accepted:
                    self.accept_first(first)
                state = self.state_path.read_bytes()
                with self.assertRaisesRegex(RuntimeError, "previous_publication_not_accepted"):
                    prepare(self.root, self.state_path, files, draft=draft, after_effect=2, wait_seconds=0)
                self.assertEqual(workspace_bytes(self.root), published)
                self.assertEqual(self.state_path.read_bytes(), state)

    def test_second_install_failure_restores_original_files_and_ready_state(self):
        draft, files = self.accepted_first_and_draft()
        child = self.root / "compositions/beat1.html"
        replace = publication.os.replace
        for existing in (False, True):
            if existing:
                child.write_text("previous local effect bytes", encoding="utf-8")
            for paths in (files, list(reversed(files))):
                with self.subTest(existing_effect_file=existing, first_path=paths[0]):
                    published = workspace_bytes(self.root)
                    state = self.state_path.read_bytes()
                    attempted = []

                    def fail_second_replace(source, target):
                        attempted.append(Path(target))
                        if len(attempted) == 2:
                            raise OSError("injected_install_failure")
                        return replace(source, target)

                    with patch.object(publication.os, "replace", side_effect=fail_second_replace):
                        with self.assertRaisesRegex(OSError, "injected_install_failure"):
                            prepare(self.root, self.state_path, paths, draft=draft)
                    self.assertEqual(attempted[:2], [(self.root / path).resolve() for path in paths])
                    self.assertEqual(workspace_bytes(self.root), published)
                    self.assertEqual(self.state_path.read_bytes(), state)
                    self.assertEqual(read_checkpoint(self.state_path)["status"], "ready")

    def test_checkpoint_save_failure_rolls_back_installed_draft(self):
        draft, files = self.accepted_first_and_draft()
        published = workspace_bytes(self.root)
        state = self.state_path.read_bytes()

        def reject_save(path, proposed):
            self.assertEqual(Path(path), self.state_path.resolve())
            self.assertEqual(proposed["status"], "prepared")
            for relative in files:
                self.assertEqual((self.root / relative).read_bytes(), (draft / relative).read_bytes())
            raise OSError("injected_checkpoint_failure")

        with patch.object(checkpoint, "write_checkpoint", side_effect=reject_save) as save:
            with self.assertRaisesRegex(OSError, "injected_checkpoint_failure"):
                prepare(self.root, self.state_path, files, draft=draft)
        save.assert_called_once()
        self.assertEqual(workspace_bytes(self.root), published)
        self.assertEqual(self.state_path.read_bytes(), state)
        self.assertEqual(read_checkpoint(self.state_path)["status"], "ready")

    def test_serial_and_overlapped_runs_have_identical_bytes_manifests_and_flags(self):
        serial_root, serial_state = self.initialize_at(self.base / "serial")
        serial_plans, overlapped_plans = [], []
        serial_reports, overlapped_reports = [], []
        next_draft = self.base / "draft-1"
        next_files = author(next_draft, 1)
        for count in range(1, 7):
            serial_plan = prepare(
                serial_root, serial_state, author(serial_root, count), final=count == 6)
            overlap_plan = prepare(
                self.root, self.state_path, next_files, final=count == 6, draft=next_draft)
            serial_plans.append(serial_plan)
            overlapped_plans.append(overlap_plan)
            self.assertEqual(workspace_bytes(self.root), workspace_bytes(serial_root))
            if count < 6:
                next_draft = self.base / f"draft-{count + 1}"
                next_files = author(next_draft, count + 1)
            serial_reports.append(accept(
                serial_root, serial_state, f"task-{count}", f"revision-{count}", receipt_files(serial_plan)))
            overlapped_reports.append(accept(
                self.root, self.state_path, f"task-{count}", f"revision-{count}", receipt_files(overlap_plan)))
        self.assertEqual(overlapped_plans, serial_plans)
        self.assertEqual(overlapped_reports, serial_reports)
        self.assertEqual([plan["authoring"] for plan in overlapped_plans], [True] * 5 + [False])
        self.assertEqual([plan["base_digest"] for plan in overlapped_plans],
                         ["initial"] + [f"revision-{count}" for count in range(1, 6)])
        serial_checkpoint = read_checkpoint(serial_state)
        overlap_checkpoint = read_checkpoint(self.state_path)
        serial_checkpoint.pop("workspace")
        overlap_checkpoint.pop("workspace")
        self.assertEqual(overlap_checkpoint, serial_checkpoint)
        self.assertEqual(overlap_checkpoint["status"], "finished")

    def test_duration_change_is_rejected_before_root_changes(self):
        draft, files = self.accepted_first_and_draft()
        (draft / "index.html").write_text(index(2, duration=20.2), encoding="utf-8")
        self.assert_rejected_without_publication(draft, files, "planned_duration_mismatch")

    def test_speaker_timeline_change_is_rejected_before_root_changes(self):
        draft, files = self.accepted_first_and_draft()
        (draft / "index.html").write_text(
            index(2).replace('data-media-start="0"', 'data-media-start="1"'), encoding="utf-8")
        self.assert_rejected_without_publication(draft, files, "speaker_timeline_changed")

    def test_prior_effect_timing_change_is_rejected_before_root_changes(self):
        draft, files = self.accepted_first_and_draft()
        (draft / "index.html").write_text(
            index(2).replace('compositions/beat0.html" data-start="0"',
                             'compositions/beat0.html" data-start="0.5"'), encoding="utf-8")
        self.assert_rejected_without_publication(draft, files, "existing_effect_changed")

    def test_prior_effect_bytes_cannot_be_overwritten_by_draft(self):
        draft, files = self.accepted_first_and_draft()
        relative = "compositions/beat0.html"
        (draft / relative).write_text('<template><div data-composition-id="beat0">Changed</div></template>',
                                      encoding="utf-8")
        self.assert_rejected_without_publication(draft, files + [relative], "accepted_file_changed")

    def test_prior_published_bytes_are_verified_before_publishing_draft(self):
        draft, files = self.accepted_first_and_draft()
        (self.root / "compositions/beat0.html").write_text(
            '<template><div data-composition-id="beat0">Changed</div></template>', encoding="utf-8")
        self.assert_rejected_without_publication(draft, files, "accepted_file_changed")

    def test_missing_dependency_is_rejected_before_root_changes(self):
        draft, files = self.accepted_first_and_draft()
        (draft / "compositions/beat1.html").write_text(
            '<template><div data-composition-id="beat1"><img src="public/missing.png"></div></template>',
            encoding="utf-8")
        self.assert_rejected_without_publication(draft, files, "missing_local_reference")

    def test_draft_must_not_overlap_publication_workspace(self):
        _, files = self.accepted_first_and_draft()
        nested = self.root / "draft"
        author(nested, 2)
        alias = self.base / "root-alias"
        alias.symlink_to(self.root, target_is_directory=True)
        for candidate in (self.root, nested, self.root.parent, alias):
            with self.subTest(draft=candidate.name):
                self.assert_rejected_without_publication(candidate, files, "draft_must_be_outside_workspace")

    def test_publication_file_path_cannot_escape_draft(self):
        draft, files = self.accepted_first_and_draft()
        outside = self.base / "outside.css"
        outside.write_text("body { color: red; }", encoding="utf-8")
        for relative in ("../outside.css", str(outside)):
            with self.subTest(path=relative):
                self.assert_rejected_without_publication(draft, files + [relative])
        self.assertEqual(outside.read_text(encoding="utf-8"), "body { color: red; }")

    def test_draft_file_symlink_cannot_escape_draft(self):
        draft, files = self.accepted_first_and_draft()
        child = draft / "compositions/beat1.html"
        outside = self.base / "outside.html"
        outside.write_bytes(child.read_bytes())
        child.unlink()
        child.symlink_to(outside)
        self.assert_rejected_without_publication(draft, files, "draft_path_outside_workspace")

    def test_publication_target_symlink_cannot_escape_workspace(self):
        draft, files = self.accepted_first_and_draft()
        outside = self.base / "outside.html"
        outside.write_text("outside sentinel", encoding="utf-8")
        (self.root / "compositions/beat1.html").symlink_to(outside)
        self.assert_rejected_without_publication(draft, files, "publication_path_outside_workspace")
        self.assertEqual(outside.read_text(encoding="utf-8"), "outside sentinel")

    def test_draft_cli_emits_publication_plan(self):
        draft = self.base / "draft-1"
        files = author(draft, 1)
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "progressive_checkpoint.py"), "prepare",
             "--workspace", str(self.root), "--state", str(self.state_path), "--draft", str(draft),
             "--file", files[0], "--file", files[1], "--final"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual(plan["status"], "prepared")
        self.assertEqual(plan["base_digest"], "initial")
        self.assertFalse(plan["authoring"])
        self.assertTrue(plan["final"])
        self.assertEqual(workspace_bytes(self.root), workspace_bytes(draft))
        self.assertEqual(read_checkpoint(self.state_path)["status"], "prepared")

    def test_batch_join_waits_across_two_accepted_effects(self):
        self.accept_first(self.prepare_first())
        drafts = [self.base / f"batch-draft-{i}" for i in (2, 3, 4)]
        files = [author(draft, i) for draft, i in zip(drafts, (2, 3, 4))]
        second = prepare(self.root, self.state_path, files[0], draft=drafts[0])
        saw_intermediate = threading.Event()
        saw_ready = threading.Event()
        finished = threading.Event()
        outcome = {}

        def observe(path):
            state = read_checkpoint(path)
            if state["publications"] == 1:
                saw_intermediate.set()
            if state["status"] == "ready" and state["publications"] == 2:
                saw_ready.set()
            return state

        def next_batch():
            try:
                outcome["plan"] = prepare(
                    self.root, self.state_path, files[2], draft=drafts[2], after_effect=3,
                    batch_join=True, wait_seconds=3, final=True)
            except Exception as error:
                outcome["error"] = error
            finally:
                finished.set()

        with patch.object(checkpoint, "read_checkpoint", side_effect=observe):
            thread = threading.Thread(target=next_batch, daemon=True)
            thread.start()
            self.addCleanup(thread.join, 3.1)
            self.assertTrue(saw_intermediate.wait(1))
            self.assertFalse(finished.is_set())
            accept(self.root, self.state_path, "task-2", "revision-2", receipt_files(second))
            self.assertTrue(saw_ready.wait(1))
            self.assertFalse(finished.is_set())
            third = prepare(self.root, self.state_path, files[1], draft=drafts[1])
            accept(self.root, self.state_path, "task-3", "revision-3", receipt_files(third))
            self.assertTrue(finished.wait(1), outcome)
        self.assertNotIn("error", outcome)
        self.assertEqual(outcome["plan"]["base_digest"], "revision-3")
        self.assertEqual(outcome["plan"]["published_effects"], 4)
        self.assertTrue(outcome["plan"]["final"])

    def test_batch_join_refuses_failed_finished_or_unrelated_prior_batches(self):
        self.accept_first(self.prepare_first())
        draft = self.base / "batch-next"
        files = author(draft, 4)
        with self.assertRaisesRegex(RuntimeError, "previous_publication_not_accepted"):
            prepare(self.root, self.state_path, files, draft=draft,
                    after_effect=5, batch_join=True, wait_seconds=0)
        second_draft = self.base / "batch-second"
        second = prepare(self.root, self.state_path, author(second_draft, 2),
                         draft=second_draft, final=True)
        prepared = read_checkpoint(self.state_path)
        fail(self.root, self.state_path, 2)
        with self.assertRaisesRegex(RuntimeError, "previous_publication_not_accepted"):
            prepare(self.root, self.state_path, files, draft=draft,
                    after_effect=3, batch_join=True, wait_seconds=0)
        checkpoint.write_checkpoint(self.state_path, prepared)
        accept(self.root, self.state_path, "task-2", "revision-2", receipt_files(second))
        with self.assertRaisesRegex(RuntimeError, "previous_publication_not_accepted"):
            prepare(self.root, self.state_path, files, draft=draft,
                    after_effect=3, batch_join=True, wait_seconds=0)

    def test_batch_join_requires_draft_and_previous_count(self):
        draft = self.base / "batch-first"
        files = author(draft, 1)
        for options in ({"draft": draft}, {"after_effect": 1}):
            with self.subTest(options=options):
                with self.assertRaisesRegex(ValueError, "batch_join_requires"):
                    prepare(self.root, self.state_path, files, batch_join=True, **options)

    def test_failed_batch_draft_closes_waiters_without_touching_accepted_bytes(self):
        self.accept_first(self.prepare_first())
        published = workspace_bytes(self.root)
        with self.assertRaisesRegex(RuntimeError, "publication_failure_mismatch"):
            fail(self.root, self.state_path, 3)
        draft = self.base / "invalid-batch-draft"
        files = author(draft, 2, duration=1)
        with self.assertRaises(ValueError):
            prepare(self.root, self.state_path, files, draft=draft)
        fail(self.root, self.state_path, 2)
        self.assertEqual(workspace_bytes(self.root), published)
        self.assertEqual(read_checkpoint(self.state_path)["status"], "failed")
        with self.assertRaisesRegex(RuntimeError, "previous_publication_not_accepted"):
            prepare(self.root, self.state_path, files, draft=draft,
                    after_effect=3, batch_join=True, wait_seconds=0)

    def test_eight_and_nine_effect_batches_preserve_the_exact_final_graph(self):
        for count in (8, 9):
            with self.subTest(count=count):
                root, state = self.initialize_at(self.base / f"batch-{count}")
                after = 0
                while after < count:
                    size = 1 if after == 0 else min(2, count - after)
                    drafts = []
                    for number in range(after + 1, after + size + 1):
                        directory = self.base / f"draft-{count}-{number}"
                        drafts.append((directory, author(directory, number)))
                    for offset, (directory, files) in enumerate(drafts):
                        number = after + offset + 1
                        plan = prepare(root, state, files, draft=directory,
                                       after_effect=number - 1 if number > 1 else None,
                                       batch_join=offset == 0 and number > 1, final=number == count)
                        accept(root, state, f"task-{number}", f"revision-{number}", receipt_files(plan))
                    after += size
                self.assertEqual((root / "index.html").read_text(), index(count))
                self.assertEqual(len(list((root / "compositions").glob("*.html"))), count)
                self.assertEqual(read_checkpoint(state)["status"], "finished")


if __name__ == "__main__":
    unittest.main()
