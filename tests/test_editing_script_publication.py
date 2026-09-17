"""Keep the cut document in the same transaction as progressive HTML publication."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from editing_script_fixtures import write_editing_script


SCRIPTS = Path(__file__).resolve().parents[1] / "plugins/aip/skills/aip/scripts"
sys.path.insert(0, str(SCRIPTS))
from editing_script_sync import EDITING_SCRIPT, validate_workspace
from preflight import check
from progressive_checkpoint import accept, initialize, prepare, read_checkpoint


REMOTE = ["render-engine/public/source.mp4", "render-engine/public/source.mp3",
          "render-engine/" + EDITING_SCRIPT]


def cut_index(count=0):
    speaker = []
    for number, (source, start, length) in enumerate([(0, 0, 2), (4, 2, 2)]):
        for tag, base, extension, lane, gain in [
                ("video", "speaker", "mp4", 0, 0), ("audio", "speaker-audio", "mp3", 2, 1)]:
            identifier = base if not number else f"{base}-{number}"
            speaker.append(f'<{tag} id="{identifier}" class="clip speaker-clip" '
                           f'data-hf-id="clip-{number}" src="public/source.{extension}" '
                           f'data-start="{start}" data-media-start="{source}" data-duration="{length}" '
                           f'data-track-index="{lane}" data-volume="{gain}"></{tag}>')
    effects = "".join(f'<div class="visual-host clip" data-composition-id="effect-{i}" '
                      f'data-composition-src="compositions/effect-{i}.html" data-start="{i}" '
                      'data-duration="1" data-track-index="3"></div>' for i in range(count))
    return ('<div id="stage" data-composition-id="finecut-root" data-start="0" data-duration="4">'
            + "".join(speaker) + effects + '</div>')


class EditingScriptPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "render-engine"
        self.root.mkdir()
        self.state = self.base / "checkpoint.json"
        self.script = write_editing_script(self.root, 6)
        (self.root / "index.html").write_text(cut_index(), encoding="utf-8")

    def initialize(self):
        return initialize(self.root, self.state, "synthetic-project", 4, "base", REMOTE)

    def draft(self, count):
        path = self.base / f"draft-{count}"
        (path / "compositions").mkdir(parents=True)
        (path / "index.html").write_text(cut_index(count), encoding="utf-8")
        relative = f"compositions/effect-{count - 1}.html"
        (path / relative).write_text(
            f'<template><div data-composition-id="effect-{count - 1}">Visual</div></template>',
            encoding="utf-8")
        return path, ["index.html", relative]

    def test_initial_cut_document_is_uploaded_once_with_the_first_draft(self):
        initial_html = (self.root / "index.html").read_bytes()
        self.initialize()
        self.assertEqual((self.root / "index.html").read_bytes(), initial_html)
        document = json.loads(self.script.read_text())
        clips = [item for item in document["tracks"][0]["items"] if not item.get("state")]
        self.assertEqual([(item["srcStart"], item["timelineIn"], item["timelineOut"]) for item in clips],
                         [(0, 0, 2000), (4000, 2000, 4000)])
        first, files = self.draft(1)
        plan = prepare(self.root, self.state, files, draft=first)
        rows = {row["path"]: row for row in plan["expected_files"]}
        script_key = "render-engine/" + EDITING_SCRIPT
        self.assertEqual(set(rows), {"render-engine/" + item for item in files} | {script_key})
        self.assertEqual(rows[script_key]["sha256"], hashlib.sha256(self.script.read_bytes()).hexdigest())
        self.assertFalse((first / EDITING_SCRIPT).exists())
        accept(self.root, self.state, "task-1", "rev-1", list(rows))
        saved = self.script.read_bytes()
        second, files = self.draft(2)
        plan = prepare(self.root, self.state, files, draft=second, final=True)
        self.assertNotIn(script_key, [row["path"] for row in plan["expected_files"]])
        self.assertEqual(self.script.read_bytes(), saved)
        self.assertFalse(validate_workspace(self.root)["changed"])

    def test_later_document_tampering_is_rejected_without_advancing_checkpoint(self):
        self.initialize()
        draft, files = self.draft(1)
        plan = prepare(self.root, self.state, files, draft=draft)
        accept(self.root, self.state, "task-1", "rev-1", [row["path"] for row in plan["expected_files"]])
        prior_state = read_checkpoint(self.state)
        document = json.loads(self.script.read_text())
        document["rev"] += 1
        self.script.write_text(json.dumps(document))
        draft, files = self.draft(2)
        with self.assertRaisesRegex(ValueError, "accepted_file_changed"):
            prepare(self.root, self.state, files, draft=draft)
        self.assertEqual(read_checkpoint(self.state), prior_state)

    def test_missing_document_does_not_create_a_checkpoint(self):
        self.script.unlink()
        with self.assertRaisesRegex(ValueError, "editing_script_missing_document"):
            self.initialize()
        self.assertFalse(self.state.exists())

    def test_preflight_requires_sync_and_reports_the_file_to_upload(self):
        before = self.script.read_bytes()
        result = check(self.root, REMOTE)
        self.assertIn("editing_script_out_of_sync", [error["code"] for error in result["errors"]])
        self.assertEqual(self.script.read_bytes(), before)
        command = [sys.executable, str(SCRIPTS / "preflight.py"), str(self.root), "--sync-editing-script"]
        for path in REMOTE:
            command.extend(["--remote-file", path])
        completed = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        self.assertTrue(result["ok"])
        self.assertEqual(result["synchronized_files"], [EDITING_SCRIPT])
        self.assertNotIn("text", result)


if __name__ == "__main__":
    unittest.main()
