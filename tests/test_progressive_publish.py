"""Exercise the entire publication loop with a deterministic MCP service double."""
import hashlib
from contextlib import nullcontext
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/aip/skills/aip/scripts"
sys.path.insert(0, str(SCRIPTS))
from progressive_publish import ProgressPublisher, SERVER_RUNTIME_PATHS
import upload_batch


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


class FakeMcp:
    def __init__(self):
        self.calls = []
        self.digest = "initial"
        self.commits = []
        self.expected = []
        self.refuse_sign = False
        self.refuse_commit = False
        self.fail_task = False
        self.task_issues = []
        self.warnings = []
        self.pending_once = False
        self.extra_accepted = []

    def call(self, tool, args):
        self.calls.append((tool, args))
        if tool == "list_workspace":
            return {"digest": self.digest, "files": [{"path": "render-engine/public/source.mp4"},
                    {"path": "render-engine/public/source.mp3"}], "staged": [], "next_cursor": None}
        if tool == "sign_workspace_upload":
            if self.refuse_sign:
                return {"uploads": [], "rejected": [{
                    "code": "invalid_content_type", "path": args["files"][0]["path"],
                    "repair_hint": "Use a bare MIME type.",
                }]}
            return {"uploads": [{"path": row["path"], "upload_url": "https://example.invalid/signed",
                                 "headers": {}} for row in args["files"]], "rejected": []}
        if tool == "commit_workspace":
            if self.refuse_commit:
                raise RuntimeError("stale_base_digest")
            assert args["base_digest"] == self.digest
            assert args["expected_files"] == self.expected
            self.commits.append(args)
            self.digest = f"revision-{len(self.commits)}"
            return {"task_id": f"task-{len(self.commits)}"}
        if tool == "get_task":
            assert args["wait_seconds"] == 45
            if self.pending_once:
                self.pending_once = False
                return {"terminal": False, "succeeded": False}
            return {"terminal": True, "succeeded": not self.fail_task, "result": {
                "outcome": "refused" if self.fail_task else (
                    "accepted_with_warnings" if self.warnings else "accepted"),
                "accepted": [row["path"] for row in self.expected] + self.extra_accepted, "digest": self.digest,
                "issues": self.task_issues, "warnings": self.warnings}}
        if tool == "get_project":
            return {"active_task_id": None, "editable_ready": True,
                    "external_authoring": {"host": "codex"} if self.commits[-1]["authoring"] else None}
        raise AssertionError("Unexpected MCP tool: " + tool)


class ProgressivePublishTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "index.html").write_text(index())
        self.mcp = FakeMcp()
        self.events = []
        self.uploads = []
        self.publisher = ProgressPublisher(self.root, "test-project", 59.85, self.mcp,
                                           uploader=self.upload, on_progress=self.events.append)

    def upload(self, snapshot, rows):
        self.mcp.expected = []
        for row in rows:
            rel = row["path"].removeprefix("render-engine/")
            self.mcp.expected.append({"path": row["path"],
                                      "sha256": hashlib.sha256((snapshot / rel).read_bytes()).hexdigest()})
        self.uploads.append([row["path"] for row in rows])

    def author(self, count, duration=59.85):
        (self.root / "index.html").write_text(index(count, duration))
        child = self.root / f"compositions/beat{count - 1}.html"
        child.parent.mkdir(exist_ok=True)
        child.write_text(f'<template><div data-composition-id="beat{count - 1}"></div></template>')
        return ["index.html", child.relative_to(self.root).as_posix()]

    def test_six_effects_are_accepted_before_the_next_is_authored(self):
        for count in range(1, 7):
            self.assertEqual(len(self.events), count - 1)
            files = self.author(count)
            self.publisher.publish(files, final=count == 6)
            self.assertEqual(self.events[-1]["published_effects"], count)
        self.assertEqual([row["duration_seconds"] for row in self.events], [59.85] * 6)
        self.assertEqual([row["authoring"] for row in self.mcp.commits], [True] * 5 + [False])
        self.assertEqual([row["base_digest"] for row in self.mcp.commits],
                         ["initial"] + [f"revision-{i}" for i in range(1, 6)])
        self.assertEqual({row["host_model_turns"] for row in self.events}, {0})
        self.assertEqual(len(self.mcp.calls), 25)
        self.assertFalse(any("source.mp" in path for batch in self.uploads for path in batch))
        with self.assertRaisesRegex(RuntimeError, "session_closed"):
            self.publisher.publish(files)

    def test_short_partial_is_rejected_before_any_mcp_call(self):
        files = self.author(1, 20.2)
        with self.assertRaisesRegex(ValueError, "planned_duration_mismatch"):
            self.publisher.publish(files)
        self.assertEqual(self.mcp.calls, [])

    def test_service_staged_runtime_is_accepted_alongside_requested_files(self):
        self.mcp.extra_accepted = sorted(SERVER_RUNTIME_PATHS)
        self.publisher.publish(self.author(1), final=True)
        self.assertTrue(self.publisher.finished)
        self.assertIn("public/vendor/fit-engine.js", self.publisher.remote)

    def test_unexpected_document_in_receipt_stops_publication(self):
        self.mcp.extra_accepted = ["render-engine/compositions/unexpected.html"]
        with self.assertRaisesRegex(RuntimeError, "receipt_mismatch"):
            self.publisher.publish(self.author(1))
        self.assertTrue(self.publisher.failed)

    def test_three_effect_batch_is_rejected_before_any_mcp_call(self):
        files = self.author(3)
        with self.assertRaisesRegex(ValueError, "invalid_effect_transition"):
            self.publisher.publish(files)
        self.assertEqual(self.mcp.calls, [])

    def test_local_but_unpublished_dependency_is_rejected_before_signing(self):
        files = self.author(1)
        (self.root / "compositions/beat0.html").write_text(
            '<template><div data-composition-id="beat0"><img src="public/new.png"></div></template>')
        (self.root / "public").mkdir()
        (self.root / "public/new.png").write_bytes(b"new image")
        with self.assertRaisesRegex(ValueError, "missing_local_reference"):
            self.publisher.publish(files)
        self.assertEqual([row[0] for row in self.mcp.calls], ["list_workspace"])

    def test_failed_upload_never_commits_or_retries(self):
        files = self.author(1)
        self.publisher.uploader = lambda *_: (_ for _ in ()).throw(RuntimeError("publication_upload_failed"))
        with self.assertRaisesRegex(RuntimeError, "upload_failed"):
            self.publisher.publish(files)
        with self.assertRaisesRegex(RuntimeError, "session_closed"):
            self.publisher.publish(files)
        self.assertNotIn("commit_workspace", [row[0] for row in self.mcp.calls])

    def test_signing_refusal_stops_before_upload(self):
        self.mcp.refuse_sign = True
        with self.assertRaisesRegex(RuntimeError, "signing_refused.*invalid_content_type.*Use a bare MIME type"):
            self.publisher.publish(self.author(1))
        self.assertEqual(self.uploads, [])
        self.assertEqual(self.mcp.commits, [])

    def test_stale_commit_never_adopts_new_digest_or_retries(self):
        self.mcp.refuse_commit = True
        with self.assertRaisesRegex(RuntimeError, "stale_base_digest"):
            self.publisher.publish(self.author(1))
        self.assertEqual([name for name, _ in self.mcp.calls].count("list_workspace"), 1)
        self.assertEqual([name for name, _ in self.mcp.calls].count("commit_workspace"), 1)

    def test_terminal_failure_does_not_continue(self):
        self.mcp.fail_task = True
        self.mcp.task_issues = [{
            "code": "unpromotable_type",
            "path": "render-engine/public/images/clipping.avif",
            "repair_hint": "Convert the image to PNG or WebP and publish again.",
        }, {
            "code": "unsafe code",
            "path": "https://private.invalid/secret",
            "repair_hint": "Read https://private.invalid/?token=secret",
        }]
        with self.assertRaisesRegex(
            RuntimeError,
            "publication_task_failed.*unpromotable_type.*clipping.avif.*Convert the image",
        ) as raised:
            self.publisher.publish(self.author(1))
        self.assertNotIn("private.invalid", str(raised.exception))
        self.assertNotIn("secret", str(raised.exception))
        self.assertEqual(self.events, [])
        self.assertEqual(len(self.mcp.commits), 1)

    def test_held_wait_and_accepted_warning_do_not_trigger_models(self):
        self.mcp.pending_once = True
        self.mcp.warnings = [{"rule": "runtime_check_unavailable", "message": "https://private.invalid/?secret"}]
        self.publisher.publish(self.author(1), final=True)
        self.assertEqual([name for name, _ in self.mcp.calls].count("get_task"), 2)
        self.assertEqual(self.events[0]["warning_codes"], ["runtime_check_unavailable"])
        self.assertNotIn("secret", str(self.events))

    def test_unrelated_staged_files_stop_before_mutation(self):
        original = self.mcp.call
        def call(tool, args):
            result = original(tool, args)
            if tool == "list_workspace":
                result["staged"] = [{"path": "render-engine/other.html"}]
            return result
        self.mcp.call = call
        with self.assertRaisesRegex(RuntimeError, "uncommitted_workspace_files"):
            self.publisher.publish(self.author(1))
        self.assertEqual(len(self.mcp.calls), 1)

    def test_index_cannot_change_between_validation_and_upload(self):
        files = self.author(1)
        copy = self.publisher._copy
        def changed(relative, target):
            if relative == "index.html":
                (self.root / "index.html").write_text(index(1, 20.2))
            return copy(relative, target)
        with patch.object(self.publisher, "_copy", changed):
            with self.assertRaisesRegex(RuntimeError, "workspace_changed_during_snapshot"):
                self.publisher.publish(files)
        self.assertEqual(self.uploads, [])

    def test_temporary_snapshot_alias_is_resolved_for_real_upload_preflight(self):
        files = self.author(1)
        physical = self.root / "snapshot-physical"
        physical.mkdir()
        alias = self.root / "snapshot-alias"
        alias.symlink_to(physical, target_is_directory=True)
        def checked_upload(snapshot, rows):
            jobs = upload_batch.prepare(snapshot, rows)
            self.assertEqual(len(jobs), 2)
            self.upload(snapshot, rows)
        self.publisher.uploader = checked_upload
        with patch("progressive_publish.tempfile.TemporaryDirectory", return_value=nullcontext(str(alias))):
            self.publisher.publish(files, final=True)
        self.assertEqual(self.events[0]["published_effects"], 1)


if __name__ == "__main__":
    unittest.main()
