from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts/check_release_pr.py"
SPEC = importlib.util.spec_from_file_location("check_release_pr", SCRIPT)
assert SPEC and SPEC.loader
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)


class ReleasePRTest(unittest.TestCase):
    """Exercise complete Git diffs using disposable repositories and real JSON."""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.commit_number = 0
        self.git("init", "-q")
        self.git("config", "user.name", "Release Test")
        self.git("config", "user.email", "release-tests@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.filemode", "true")
        for relative in policy.VERSION_FIELDS:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / relative, target)
        shutil.copyfile(REPO / policy.RELEASE_TEMPLATE, self.root / policy.RELEASE_TEMPLATE)
        self.set_version("0.8.33")
        (self.root / "README.md").write_text("Synthetic fixture.\n", encoding="utf-8")
        self.base = self.commit()

    def git(self, *args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(self.root), *args], stderr=subprocess.PIPE,
        ).decode().strip()

    def commit(self) -> str:
        self.commit_number += 1
        self.git("add", "--all")
        self.git("commit", "--quiet", "--allow-empty", "-m", f"Synthetic fixture {self.commit_number}")
        return self.git("rev-parse", "HEAD")

    def document(self, path: str) -> dict:
        return json.loads((self.root / path).read_text(encoding="utf-8"))

    def write_document(self, path: str, document: dict) -> None:
        (self.root / path).write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    def set_version(self, version: str) -> None:
        for path, fields in policy.VERSION_FIELDS.items():
            document = self.document(path)
            for field in fields:
                parent = document
                for key in field[:-1]:
                    parent = parent[key]
                parent[field[-1]] = version
            self.write_document(path, document)
        log = self.root / policy.release_log_path(version)
        if not log.exists():
            log.write_text(
                f"# v{version}\n\n## Changes\n\n- Synthetic release fixture.\n\n"
                "## Compatibility\n\n- No migration required.\n\n"
                "## Validation\n\n- Fixture JSON checked.\n", encoding="utf-8",
            )

    def check(self, title: str = "chore: release v0.8.34", base: str | None = None) -> str:
        return policy.check_release_pr(self.root, base or self.base, self.commit(), title)

    def test_version_only_pr_passes(self) -> None:
        self.set_version("0.8.34")
        self.assertIn("release 0.8.33 -> 0.8.34", self.check())

    def test_ordinary_pr_can_change_content_without_bumping(self) -> None:
        (self.root / "README.md").write_text("Updated fixture.\n", encoding="utf-8")
        path = "plugins/aip/.codex-plugin/plugin.json"
        document = self.document(path)
        document["description"] = "Updated description"
        self.write_document(path, document)
        self.assertIn("ordinary PR", self.check("fix: clarify the plugin"))

    def test_version_change_requires_exact_title(self) -> None:
        self.set_version("0.8.34")
        head = self.commit()
        for title in (
            "chore(release): v0.8.34",
            "fix: release", "chore: v0.8.34", "chore: release 0.8.34",
            "chore: release v0.8.34 extra", "chore: release v0.8.34\n",
            "chore: release v0.8.35", "chore: release v00.8.34",
        ):
            with self.subTest(title=title), self.assertRaises(ValueError):
                policy.check_release_pr(self.root, self.base, head, title)

    def test_title_edit_is_checked_against_same_commits(self) -> None:
        self.set_version("0.8.34")
        head = self.commit()
        policy.check_release_pr(self.root, self.base, head, "chore: release v0.8.34")
        with self.assertRaisesRegex(ValueError, "separate PR"):
            policy.check_release_pr(self.root, self.base, head, "fix: changed title")

    def test_release_title_without_bump_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "must change the version"):
            self.check("chore: release v0.8.33")

    def test_extra_file_fails_even_with_valid_title(self) -> None:
        self.set_version("0.8.34")
        (self.root / "new-skill.md").write_text("Extra content.\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unexpected paths"):
            self.check()

    def test_deleted_file_fails(self) -> None:
        self.set_version("0.8.34")
        (self.root / "README.md").unlink()
        with self.assertRaisesRegex(ValueError, "unexpected paths"):
            self.check()

    def test_renamed_file_fails(self) -> None:
        self.set_version("0.8.34")
        (self.root / "README.md").rename(self.root / "RENAMED.md")
        with self.assertRaisesRegex(ValueError, "unexpected paths"):
            self.check()

    def test_other_fields_in_each_allowed_file_fail(self) -> None:
        for path in policy.VERSION_FIELDS:
            with self.subTest(path=path):
                # Reset only this test's disposable repository between cases.
                self.git("reset", "--hard", self.base)
                self.set_version("0.8.34")
                document = self.document(path)
                document["extra"] = "Unrelated change"
                self.write_document(path, document)
                with self.assertRaises(ValueError):
                    self.check()

    def test_stale_version_in_each_field_fails(self) -> None:
        for path, fields in policy.VERSION_FIELDS.items():
            for field in fields:
                with self.subTest(path=path, field=field):
                    self.set_version("0.8.34")
                    document = self.document(path)
                    parent = document
                    for key in field[:-1]:
                        parent = parent[key]
                    parent[field[-1]] = "0.8.33"
                    self.write_document(path, document)
                    with self.assertRaisesRegex(ValueError, "six version fields must match"):
                        self.check("fix: no release title")

    def test_removed_version_field_fails(self) -> None:
        self.set_version("0.8.34")
        path = "plugins/aip/.mcp.json"
        document = self.document(path)
        del document["mcpServers"]["aip"]["http_headers"]
        self.write_document(path, document)
        with self.assertRaisesRegex(ValueError, "Invalid version file"):
            self.check()

    def test_removed_version_file_fails(self) -> None:
        self.set_version("0.8.34")
        (self.root / "plugins/aip/.mcp.json").unlink()
        with self.assertRaisesRegex(ValueError, "must exist"):
            self.check()

    def test_executable_version_file_fails(self) -> None:
        self.set_version("0.8.34")
        (self.root / "plugins/aip/.mcp.json").chmod(0o755)
        with self.assertRaisesRegex(ValueError, "non-executable"):
            self.check()

    def test_symlink_version_file_fails(self) -> None:
        path = self.root / "plugins/aip/.mcp.json"
        path.unlink()
        path.symlink_to("../../../README.md")
        with self.assertRaisesRegex(ValueError, "regular"):
            self.check("fix: symlink")

    def test_duplicate_json_key_fails(self) -> None:
        self.set_version("0.8.34")
        path = self.root / "plugins/aip/.codex-plugin/plugin.json"
        path.write_text('{"version":"0.8.33", "version":"0.8.34"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            self.check()

    def test_decrease_fails(self) -> None:
        self.set_version("0.8.32")
        with self.assertRaisesRegex(ValueError, "must be newer"):
            self.check("chore: release v0.8.32")

    def test_base_only_changes_are_not_part_of_release_diff(self) -> None:
        (self.root / "README.md").write_text("Base-only change.\n", encoding="utf-8")
        base_tip = self.commit()
        self.git("checkout", "--detach", self.base)
        self.set_version("0.8.34")
        self.assertIn("OK: release", self.check(base=base_tip))

    def test_concurrent_release_cannot_reuse_current_base_version(self) -> None:
        self.set_version("0.8.34")
        base_tip = self.commit()
        self.git("checkout", "--detach", self.base)
        self.set_version("0.8.34")
        with self.assertRaisesRegex(ValueError, "base version 0.8.34"):
            self.check(base=base_tip)

    def test_prerelease_to_stable_passes(self) -> None:
        self.set_version("0.9.0-rc.1")
        self.base = self.commit()
        self.set_version("0.9.0")
        self.assertIn("OK: release", self.check("chore: release v0.9.0"))

    def test_build_metadata_only_is_not_a_bump(self) -> None:
        self.set_version("0.8.33+build.2")
        with self.assertRaisesRegex(ValueError, "must be newer"):
            self.check("chore: release v0.8.33+build.2")

    def test_missing_new_log_fails(self) -> None:
        self.set_version("0.8.34")
        (self.root / policy.release_log_path("0.8.34")).unlink()
        with self.assertRaisesRegex(ValueError, "must add a new release log"):
            self.check()

    def test_wrong_log_heading_fails(self) -> None:
        self.set_version("0.8.34")
        path = self.root / policy.release_log_path("0.8.34")
        path.write_text(path.read_text().replace("# v0.8.34", "# v0.8.35"))
        with self.assertRaisesRegex(ValueError, "must start with"):
            self.check()

    def test_unfilled_log_fails(self) -> None:
        self.set_version("0.8.34")
        (self.root / policy.release_log_path("0.8.34")).write_text("# v0.8.34\n\n{{changes}}\n")
        with self.assertRaisesRegex(ValueError, "template placeholders"):
            self.check()

    def test_empty_log_section_fails(self) -> None:
        self.set_version("0.8.34")
        path = self.root / policy.release_log_path("0.8.34")
        path.write_text(path.read_text().replace("- No migration required.", "<!-- fill later -->"))
        with self.assertRaisesRegex(ValueError, "must be filled in: Compatibility"):
            self.check()

    def test_historical_log_edit_in_release_fails(self) -> None:
        self.set_version("0.8.34")
        (self.root / policy.release_log_path("0.8.33")).write_text("Changed history.\n")
        with self.assertRaisesRegex(ValueError, "unexpected paths"):
            self.check()

    def test_log_edit_without_bump_fails(self) -> None:
        (self.root / policy.release_log_path("0.8.33")).write_text("Changed history.\n")
        with self.assertRaisesRegex(ValueError, "historical logs cannot be changed"):
            self.check("docs: adjust release history")

    def test_multiple_new_logs_fail(self) -> None:
        self.set_version("0.8.34")
        (self.root / policy.release_log_path("0.8.35")).write_text("Extra release.\n")
        with self.assertRaisesRegex(ValueError, "unexpected paths"):
            self.check()

    def test_release_cannot_edit_template(self) -> None:
        self.set_version("0.8.34")
        (self.root / policy.RELEASE_TEMPLATE).write_text("Different template.\n")
        with self.assertRaisesRegex(ValueError, "unexpected paths"):
            self.check()

    def test_ordinary_pr_can_edit_template(self) -> None:
        (self.root / policy.RELEASE_TEMPLATE).write_text("Different template.\n")
        self.assertIn("ordinary PR", self.check("chore: release tooling"))

    def test_bootstrap_tracking_keeps_existing_version(self) -> None:
        (self.root / policy.LATEST_VERSION_FILE).unlink()
        (self.root / policy.release_log_path("0.8.33")).unlink()
        self.base = self.commit()
        (self.root / policy.LATEST_VERSION_FILE).write_text('{"version":"0.8.33"}\n')
        self.set_version("0.8.33")
        self.assertIn("ordinary PR", self.check("chore: add release tracking"))

    def test_symlink_release_log_fails(self) -> None:
        self.set_version("0.8.34")
        path = self.root / policy.release_log_path("0.8.34")
        path.unlink()
        path.symlink_to("../README.md")
        with self.assertRaisesRegex(ValueError, "regular"):
            self.check()

    def test_bare_repository_cli_reads_pr_without_executing_it(self) -> None:
        (self.root / "check_release_pr.py").write_text("raise RuntimeError('Do not execute PR code')\n", encoding="utf-8")
        head = self.commit()
        with tempfile.TemporaryDirectory() as directory:
            bare = Path(directory) / "fixture.git"
            subprocess.run(["git", "clone", "--quiet", "--bare", str(self.root), str(bare)], check=True)
            result = subprocess.run(
                [sys.executable, "-I", str(SCRIPT), "--repo", str(bare),
                 "--base", self.base, "--head", head, "--title=fix: $(false) `false`"],
                capture_output=True, text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ordinary PR", result.stdout)


class SemVerTest(unittest.TestCase):
    def test_semver_precedence(self) -> None:
        versions = [
            "1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-alpha.beta", "1.0.0-beta",
            "1.0.0-beta.2", "1.0.0-beta.11", "1.0.0-rc.1", "1.0.0", "1.0.1", "1.1.0", "2.0.0",
        ]
        for previous, current in zip(versions, versions[1:]):
            with self.subTest(previous=previous, current=current):
                self.assertLess(policy.precedence(previous), policy.precedence(current))
        self.assertEqual(policy.precedence("1.0.0+one"), policy.precedence("1.0.0+two"))

    def test_invalid_semver_fails(self) -> None:
        for version in ("v1.2.3", "01.2.3", "1.2", "1.2.3-01", "1.2.3-", "1.2.3+", "1.2.3\n", "1.2.\u0663"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                policy.precedence(version)


if __name__ == "__main__":
    unittest.main()
