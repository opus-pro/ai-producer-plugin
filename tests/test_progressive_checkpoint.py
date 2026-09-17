"""Exercise persisted progressive state across host-model checkpoints."""

import json
from pathlib import Path
from editing_script_fixtures import write_editing_script
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/aip/skills/aip/scripts"
sys.path.insert(0, str(SCRIPTS))
import progressive_checkpoint as checkpoint
from progressive_checkpoint import accept, checkpoint_lock, initialize, prepare, read_checkpoint, write_checkpoint


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


class ProgressiveCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "render-engine"
        self.root.mkdir()
        (self.root / "index.html").write_text(index(), encoding="utf-8")
        write_editing_script(self.root)
        self.state_path = self.base / ".aip-progress.json"

    def init(self):
        return initialize(
            self.root,
            self.state_path,
            "test-project",
            59.85,
            "initial",
            ["render-engine/public/source.mp4", "render-engine/public/source.mp3"],
        )

    def author(self, count):
        (self.root / "index.html").write_text(index(count), encoding="utf-8")
        child = self.root / f"compositions/beat{count - 1}.html"
        child.parent.mkdir(exist_ok=True)
        child.write_text(
            f'<template><div data-composition-id="beat{count - 1}"></div></template>',
            encoding="utf-8",
        )
        return ["index.html", child.relative_to(self.root).as_posix()]

    def test_each_effect_uses_prepare_and_accept_process_states(self):
        self.assertEqual(self.init()["status"], "ready")
        for count in range(1, 7):
            plan = prepare(self.root, self.state_path, self.author(count), final=count == 6)
            self.assertEqual(read_checkpoint(self.state_path)["status"], "prepared")
            report = accept(
                self.root,
                self.state_path,
                f"task-{count}",
                f"revision-{count}",
                [row["path"] for row in plan["expected_files"]],
            )
            self.assertEqual(report["published_effects"], count)
            state = read_checkpoint(self.state_path)
            self.assertEqual(state["publications"], count)
            self.assertEqual(state["status"], "finished" if count == 6 else "ready")

    def test_tampered_state_is_refused(self):
        self.init()
        envelope = json.loads(self.state_path.read_text(encoding="utf-8"))
        envelope["state"]["project_id"] = "other-project"
        self.state_path.write_text(json.dumps(envelope), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid_checkpoint_checksum"):
            read_checkpoint(self.state_path)

    def test_prepared_checkpoint_cannot_start_another_publication(self):
        self.init()
        prepare(self.root, self.state_path, self.author(1))
        with self.assertRaisesRegex(RuntimeError, "checkpoint_closed"):
            prepare(self.root, self.state_path, self.author(2))

    def test_failed_receipt_leaves_checkpoint_closed(self):
        self.init()
        prepare(self.root, self.state_path, self.author(1))
        with self.assertRaisesRegex(ValueError, "receipt_mismatch"):
            accept(self.root, self.state_path, "task-1", "revision-1", ["render-engine/index.html"])
        self.assertEqual(read_checkpoint(self.state_path)["status"], "prepared")
        with self.assertRaisesRegex(RuntimeError, "checkpoint_closed"):
            prepare(self.root, self.state_path, self.author(2))

    def test_checkpoint_must_stay_outside_published_workspace(self):
        with self.assertRaisesRegex(ValueError, "checkpoint_must_be_outside_workspace"):
            initialize(
                self.root, self.root / ".aip-progress.json", "test-project", 59.85, "initial", [],
            )

    def test_concurrent_transition_is_refused_before_state_change(self):
        self.init()
        with checkpoint_lock(self.state_path):
            with self.assertRaisesRegex(RuntimeError, "checkpoint_busy"):
                prepare(self.root, self.state_path, self.author(1))
        self.assertEqual(read_checkpoint(self.state_path)["status"], "ready")

    def test_atomic_write_does_not_require_posix_fchmod(self):
        with patch.object(checkpoint.os, "fchmod", None, create=True):
            write_checkpoint(self.state_path, {"portable": True})
        self.assertEqual(read_checkpoint(self.state_path), {"portable": True})


if __name__ == "__main__":
    unittest.main()
