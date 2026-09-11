from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import prepare_release
from check_release_pr import (
    LATEST_VERSION_FILE, RELEASE_TEMPLATE, VERSION_FIELDS, release_log_path,
    validate_release_log, version_from_documents,
)


class PrepareReleaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        for relative in (*VERSION_FIELDS, RELEASE_TEMPLATE):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / relative, path)
        self.current = version_from_documents(self.documents())
        major = int(self.current.split(".")[0])
        self.target = f"{major + 1}.0.0"

    def documents(self) -> dict:
        return {path: json.loads((self.root / path).read_text()) for path in VERSION_FIELDS}

    def files(self) -> dict:
        return {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}

    def test_aligns_every_version_and_preserves_other_fields(self) -> None:
        before = self.documents()
        log = prepare_release.prepare_release(self.root, self.target)
        after = self.documents()
        self.assertEqual(version_from_documents(after), self.target)
        self.assertEqual(json.loads((self.root / LATEST_VERSION_FILE).read_text()), {"version": self.target})
        for path, fields in VERSION_FIELDS.items():
            for field in fields:
                parent = after[path]
                original = before[path]
                for key in field[:-1]:
                    parent, original = parent[key], original[key]
                parent[field[-1]] = original[field[-1]]
            self.assertEqual(after[path], before[path])
        self.assertEqual(log.relative_to(self.root).as_posix(), release_log_path(self.target))
        template = (self.root / RELEASE_TEMPLATE).read_text()
        self.assertEqual(log.read_text(), template.replace("{{version}}", self.target))
        with self.assertRaisesRegex(ValueError, "template placeholders"):
            validate_release_log(log.read_text(), self.target)

    def test_unchanged_decreased_and_invalid_versions_leave_files_untouched(self) -> None:
        original = self.files()
        for version in (self.current, "0.0.0", "v2.0.0", "02.0.0", "2.0.0-01"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                prepare_release.prepare_release(self.root, version)
            self.assertEqual(self.files(), original)

    def test_mismatched_copies_leave_files_untouched(self) -> None:
        path = self.root / LATEST_VERSION_FILE
        path.write_text('{"version":"0.0.1"}\n')
        original = self.files()
        with self.assertRaisesRegex(ValueError, "six version fields must match"):
            prepare_release.prepare_release(self.root, self.target)
        self.assertEqual(self.files(), original)

    def test_existing_log_is_not_overwritten(self) -> None:
        (self.root / release_log_path(self.target)).write_text("Existing notes.\n")
        original = self.files()
        with self.assertRaisesRegex(ValueError, "already exists"):
            prepare_release.prepare_release(self.root, self.target)
        self.assertEqual(self.files(), original)

    def test_missing_template_leaves_versions_untouched(self) -> None:
        (self.root / RELEASE_TEMPLATE).unlink()
        original = self.files()
        with self.assertRaises(OSError):
            prepare_release.prepare_release(self.root, self.target)
        self.assertEqual(self.files(), original)

    def test_invalid_template_leaves_versions_untouched(self) -> None:
        path = self.root / RELEASE_TEMPLATE
        template = path.read_text()
        for contents in ("No template placeholders.\n", template.replace("## Changes", "## Notes")):
            with self.subTest(contents=contents):
                path.write_text(contents)
                original = self.files()
                with self.assertRaises(ValueError):
                    prepare_release.prepare_release(self.root, self.target)
                self.assertEqual(self.files(), original)

    def test_non_regular_version_file_is_rejected(self) -> None:
        path = self.root / LATEST_VERSION_FILE
        path.chmod(0o755)
        original = self.files()
        with self.assertRaisesRegex(ValueError, "regular and non-executable"):
            prepare_release.prepare_release(self.root, self.target)
        self.assertEqual(self.files(), original)

    def test_cli_accepts_an_explicit_repository(self) -> None:
        result = subprocess.run(
            [sys.executable, str(REPO / "scripts/prepare_release.py"), self.target, "--repo", str(self.root)],
            cwd=self.root, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"chore: release v{self.target}", result.stdout)
        self.assertEqual(version_from_documents(self.documents()), self.target)


if __name__ == "__main__":
    unittest.main()
