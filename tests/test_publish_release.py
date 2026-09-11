from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch
from urllib.error import HTTPError


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
SPEC = importlib.util.spec_from_file_location("publish_release", REPO / "scripts/publish_release.py")
assert SPEC and SPEC.loader
publisher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publisher)
SHA = "a" * 40
RELEASE_URL = "https://github.com/opus-pro/ai-producer-plugin/releases/tag/v1.1.4"


def http_error(status: int) -> HTTPError:
    error = HTTPError("https://api.github.com/", status, "Synthetic API error", {}, io.BytesIO())
    error.close()
    return error


class PublishReleaseTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for relative in publisher.VERSION_FIELDS:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / relative, target)
        self.set_version("1.1.4")

    def set_version(self, version: str) -> None:
        for relative, fields in publisher.VERSION_FIELDS.items():
            path = self.root / relative
            document = json.loads(path.read_text())
            for field in fields:
                parent = document
                for key in field[:-1]:
                    parent = parent[key]
                parent[field[-1]] = version
            path.write_text(json.dumps(document))
        self.notes = (
            f"# v{version}\n\n## Changes\n\n### Fixed\n\n"
            "- Fix a synthetic issue. ([#1](https://github.com/opus-pro/ai-producer-plugin/pull/1))\n\n"
            f"**Full Changelog**: [v1.1.3...v{version}]"
            f"(https://github.com/opus-pro/ai-producer-plugin/compare/v1.1.3...v{version})\n"
        )
        self.log = self.root / publisher.release_log_path(version)
        self.log.write_text(self.notes)

    def test_publishes_only_declared_version_at_triggering_commit(self) -> None:
        (self.root / "releases/v1.0.0.md").write_text("Historical notes.\n")
        api = Mock(side_effect=[http_error(404), {}, {"html_url": RELEASE_URL}])
        self.assertEqual(publisher.publish_release(self.root, SHA, api), f"Published {RELEASE_URL}")
        self.assertEqual(api.call_args_list, [
            call("GET", "git/ref/tags/v1.1.4"),
            call("POST", "git/refs", {"ref": "refs/tags/v1.1.4", "sha": SHA}),
            call("POST", "releases", {
                "tag_name": "v1.1.4", "target_commitish": SHA, "name": "v1.1.4",
                "body": self.notes, "draft": False, "prerelease": False,
                "make_latest": "legacy", "generate_release_notes": False,
            }),
        ])

    def test_existing_tag_skips_release_even_without_existing_release(self) -> None:
        api = Mock(return_value={"ref": "refs/tags/v1.1.4"})
        self.assertIn("already exists", publisher.publish_release(self.root, SHA, api))
        api.assert_called_once_with("GET", "git/ref/tags/v1.1.4")

    def test_missing_matching_log_or_version_file_skips_without_api_calls(self) -> None:
        api = Mock()
        (self.root / "releases/v1.0.0.md").write_text("Historical notes.\n")
        self.log.unlink()
        self.assertIn("no release log", publisher.publish_release(self.root, SHA, api))
        (self.root / publisher.LATEST_VERSION_FILE).unlink()
        self.assertIn("latest_version.json is absent", publisher.publish_release(self.root, SHA, api))
        api.assert_not_called()

    def test_invalid_version_cannot_select_paths_or_create_tags(self) -> None:
        for document in ('{"version":"../../README"}', '{"version":"v1.1.4"}', '{"version":4}', '[]',
                         '{"version":"1.1.4","version":"1.1.5"}'):
            with self.subTest(document=document):
                (self.root / publisher.LATEST_VERSION_FILE).write_text(document)
                api = Mock()
                with self.assertRaises(ValueError):
                    publisher.publish_release(self.root, SHA, api)
                api.assert_not_called()

    def test_version_mismatch_and_invalid_notes_fail_before_writes(self) -> None:
        manifest = self.root / "plugins/aip/.codex-plugin/plugin.json"
        original = manifest.read_text()
        manifest.write_text(original.replace('"1.1.4"', '"1.1.3"'))
        api = Mock(side_effect=[http_error(404)])
        with self.assertRaisesRegex(ValueError, "must match"):
            publisher.publish_release(self.root, SHA, api)
        self.assertEqual(api.call_count, 1)
        manifest.write_text(original)
        self.log.write_text("# v1.1.4\n\n{{changes}}\n")
        api = Mock(side_effect=[http_error(404)])
        with self.assertRaisesRegex(ValueError, "placeholders"):
            publisher.publish_release(self.root, SHA, api)
        self.assertEqual(api.call_count, 1)

    def test_prereleases_are_not_marked_latest(self) -> None:
        self.set_version("1.2.0-rc.1+build.2")
        api = Mock(side_effect=[http_error(404), {}, {"html_url": RELEASE_URL}])
        publisher.publish_release(self.root, SHA, api)
        self.assertEqual(api.call_args_list[0], call("GET", "git/ref/tags/v1.2.0-rc.1%2Bbuild.2"))
        payload = api.call_args.args[2]
        self.assertEqual(payload["tag_name"], "v1.2.0-rc.1+build.2")
        self.assertTrue(payload["prerelease"])
        self.assertEqual(payload["make_latest"], "false")

    def test_tag_lookup_errors_are_not_treated_as_missing(self) -> None:
        for status in (401, 403, 429, 500):
            with self.subTest(status=status):
                api = Mock(side_effect=http_error(status))
                with self.assertRaises(HTTPError):
                    publisher.publish_release(self.root, SHA, api)
                self.assertEqual(api.call_count, 1)

    def test_concurrent_tag_creation_skips_without_creating_release(self) -> None:
        for status in (409, 422):
            with self.subTest(status=status):
                api = Mock(side_effect=[http_error(404), http_error(status), {"ref": "refs/tags/v1.1.4"}])
                self.assertIn("created concurrently", publisher.publish_release(self.root, SHA, api))
                self.assertEqual(api.call_count, 3)
                self.assertEqual(api.call_args, call("GET", "git/ref/tags/v1.1.4"))

    def test_tag_creation_failure_without_a_tag_still_fails(self) -> None:
        api = Mock(side_effect=[http_error(404), http_error(422), http_error(404)])
        with self.assertRaises(HTTPError):
            publisher.publish_release(self.root, SHA, api)
        self.assertEqual(api.call_count, 3)

    def test_release_failure_preserves_tag_and_rerun_skips(self) -> None:
        api = Mock(side_effect=[http_error(404), {}, http_error(403)])
        with self.assertRaisesRegex(RuntimeError, "tag is preserved and reruns will skip"):
            publisher.publish_release(self.root, SHA, api)
        self.assertEqual(api.call_count, 3)
        rerun = Mock(return_value={"ref": "refs/tags/v1.1.4"})
        self.assertIn("already exists", publisher.publish_release(self.root, SHA, rerun))
        rerun.assert_called_once()

    def test_entry_point_rejects_pr_dispatch_other_branches_and_forks(self) -> None:
        for event, ref, repository in (
            ("pull_request", "refs/heads/main", publisher.REPOSITORY),
            ("workflow_dispatch", "refs/heads/main", publisher.REPOSITORY),
            ("push", "refs/heads/feature", publisher.REPOSITORY),
            ("push", "refs/heads/main", "example/plugin-fork"),
        ):
            with self.subTest(event=event, ref=ref, repository=repository), patch.dict(os.environ, {
                "GITHUB_EVENT_NAME": event, "GITHUB_REF": ref, "GITHUB_REPOSITORY": repository,
            }, clear=True), patch.object(publisher, "publish_release") as publish, contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(publisher.main(), 1)
                publish.assert_not_called()

    def test_entry_point_accepts_upstream_main_push(self) -> None:
        with patch.dict(os.environ, {
            "GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/main",
            "GITHUB_REPOSITORY": publisher.REPOSITORY, "GITHUB_SHA": SHA, "GH_TOKEN": "synthetic-token",
        }, clear=True), patch.object(publisher, "publish_release", return_value="Published fixture") as publish, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(publisher.main(), 0)
            publish.assert_called_once_with(REPO, SHA)


if __name__ == "__main__":
    unittest.main()
