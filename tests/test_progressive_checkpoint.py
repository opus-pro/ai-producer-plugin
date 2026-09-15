"""Verify crash-safe state across one-effect host-model checkpoints."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/aip/skills/aip/scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import progressive_checkpoint as checkpoint
from progressive_checkpoint import checkpoint_lock, initialize, publish, read_checkpoint, write_checkpoint
from progressive_publish import ProgressPublisher
from test_progressive_publish import FakeMcp, index


class ProgressiveCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.task = Path(self.temp.name)
        self.root = self.task / "render-engine"
        self.root.mkdir()
        (self.root / "index.html").write_text(index(), encoding="utf-8")
        self.state_path = self.task / ".aip-progress.json"
        self.mcp = FakeMcp()
        self.events = []

    def upload(self, snapshot, rows):
        self.mcp.expected = []
        for row in rows:
            relative = row["path"].removeprefix("render-engine/")
            self.mcp.expected.append({
                "path": row["path"],
                "sha256": hashlib.sha256((snapshot / relative).read_bytes()).hexdigest(),
            })

    def factory(self, *_args, **_kwargs):
        return self.mcp

    def author(self, count):
        (self.root / "index.html").write_text(index(count), encoding="utf-8")
        child = self.root / f"compositions/beat{count - 1}.html"
        child.parent.mkdir(exist_ok=True)
        child.write_text(
            f'<template><div data-composition-id="beat{count - 1}"></div></template>',
            encoding="utf-8",
        )
        return ["index.html", child.relative_to(self.root).as_posix()]

    def test_each_effect_publishes_from_a_new_process_state(self):
        initialize(self.root, self.state_path, "test-project", 59.85)
        for count in range(1, 7):
            report = publish(
                self.root, self.state_path, "aip", self.author(count), count == 6,
                mcp_factory=self.factory, uploader=self.upload, on_progress=self.events.append,
            )
            self.assertEqual(report["published_effects"], count)
            state = read_checkpoint(self.state_path)
            self.assertEqual(state["publications"], count)
            self.assertEqual(state["status"], "finished" if count == 6 else "ready")
        self.assertEqual(len(self.mcp.commits), 6)

    def test_tampered_state_is_refused(self):
        initialize(self.root, self.state_path, "test-project", 59.85)
        envelope = json.loads(self.state_path.read_text(encoding="utf-8"))
        envelope["state"]["project_id"] = "other-project"
        self.state_path.write_text(json.dumps(envelope), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid_checkpoint_checksum"):
            read_checkpoint(self.state_path)

    def test_in_flight_checkpoint_cannot_resume(self):
        publisher = ProgressPublisher(self.root, "test-project", 59.85, self.mcp)
        write_checkpoint(self.state_path, publisher.checkpoint("publishing"))
        with self.assertRaisesRegex(RuntimeError, "checkpoint_closed"):
            ProgressPublisher.resume(self.root, read_checkpoint(self.state_path), self.mcp)

    def test_failure_is_persisted_and_cannot_restart(self):
        initialize(self.root, self.state_path, "test-project", 59.85)
        self.mcp.refuse_sign = True
        with self.assertRaisesRegex(RuntimeError, "publication_signing_refused"):
            publish(
                self.root, self.state_path, "aip", self.author(1),
                mcp_factory=self.factory, uploader=self.upload,
            )
        state = read_checkpoint(self.state_path)
        self.assertEqual(state["status"], "failed")
        with self.assertRaisesRegex(RuntimeError, "checkpoint_closed"):
            ProgressPublisher.resume(self.root, state, self.mcp)

    def test_checkpoint_must_stay_outside_published_workspace(self):
        with self.assertRaisesRegex(ValueError, "checkpoint_must_be_outside_workspace"):
            initialize(self.root, self.root / ".aip-progress.json", "test-project", 59.85)

    def test_concurrent_transition_is_refused_before_mcp_start(self):
        initialize(self.root, self.state_path, "test-project", 59.85)
        with checkpoint_lock(self.state_path):
            with self.assertRaisesRegex(RuntimeError, "checkpoint_busy"):
                publish(
                    self.root, self.state_path, "aip", self.author(1),
                    mcp_factory=self.factory, uploader=self.upload,
                )
        self.assertEqual(self.mcp.calls, [])
        self.assertEqual(read_checkpoint(self.state_path)["status"], "ready")

    def test_atomic_write_does_not_require_posix_fchmod(self):
        with patch.object(checkpoint.os, "fchmod", None, create=True):
            write_checkpoint(self.state_path, {"portable": True})
        self.assertEqual(read_checkpoint(self.state_path), {"portable": True})


if __name__ == "__main__":
    unittest.main()
