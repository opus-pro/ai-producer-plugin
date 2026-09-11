from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
SCRIPT = REPO / "scripts" / "validate.py"
SPEC = importlib.util.spec_from_file_location("validate", SCRIPT)
assert SPEC and SPEC.loader
validate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validate
SPEC.loader.exec_module(validate)

FIXTURE_PARTS = (".agents", ".claude-plugin", "plugins", "releases")
ENTRY_SKILL = Path("plugins/aip/skills/aip/SKILL.md")
MCP_CONFIG = "plugins/aip/.mcp.json"


class ValidateFixtureTest(unittest.TestCase):
    """Run the validator against mutated copies of the real repo tree."""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        for part in FIXTURE_PARTS:
            source = REPO / part
            shutil.copytree(source, self.root / part)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def rewrite(self, relative: str, old: str, new: str) -> None:
        path = self.root / relative
        contents = path.read_text(encoding="utf-8")
        self.assertIn(old, contents, f"fixture mutation target not found in {relative}")
        path.write_text(contents.replace(old, new), encoding="utf-8")

    def test_pristine_copy_passes(self) -> None:
        validate.main(self.root)

    def test_missing_skill_reference_fails(self) -> None:
        reference = self.root / "plugins/aip/skills/aip/references/workspace.md"
        reference.unlink()
        with self.assertRaisesRegex(AssertionError, "missing relative reference"):
            validate.main(self.root)

    def test_skill_reference_cannot_escape_package(self) -> None:
        skill = self.root / ENTRY_SKILL
        with skill.open("a", encoding="utf-8") as handle:
            handle.write("\n[escape](../../../../../../outside.md)\n")
        with self.assertRaisesRegex(AssertionError, "reference escapes package"):
            validate.main(self.root)

    def test_bundled_license_cannot_be_truncated(self) -> None:
        license_file = self.root / "plugins/aip/licenses/Apache-2.0.txt"
        license_file.write_bytes(license_file.read_bytes()[:100])
        with self.assertRaisesRegex(AssertionError, "verified upstream text"):
            validate.main(self.root)

    def test_missing_bundled_license_fails(self) -> None:
        (self.root / "plugins/aip/licenses/Apache-2.0.txt").unlink()
        with self.assertRaises(AssertionError):
            validate.main(self.root)

    def test_nonproduction_endpoint_fails(self) -> None:
        self.rewrite(MCP_CONFIG, validate.EXPECTED_ENDPOINT, "https://example.invalid/api/mcp")
        with self.assertRaises(AssertionError):
            validate.main(self.root)

    def test_manifest_version_mismatch_fails(self) -> None:
        manifest = self.root / "plugins/aip/.claude-plugin/plugin.json"
        contents = manifest.read_text(encoding="utf-8")
        version = validate.load_json(manifest)["version"]
        manifest.write_text(contents.replace(str(version), "999.0.0"), encoding="utf-8")

        with self.assertRaisesRegex(AssertionError, "version"):
            validate.main(self.root)

    def test_stale_plugin_version_header_fails(self) -> None:
        """A release that bumps the manifests but not the header ships a lie."""
        version = validate.load_json(self.root / "plugins/aip/.claude-plugin/plugin.json")["version"]
        self.rewrite(MCP_CONFIG, f'"{validate.PLUGIN_VERSION_HEADER}": "{version}"',
                     f'"{validate.PLUGIN_VERSION_HEADER}": "0.0.1"')

        with self.assertRaisesRegex(AssertionError, validate.PLUGIN_VERSION_HEADER):
            validate.main(self.root)

    def test_missing_host_header_key_fails(self) -> None:
        """Dropping one host's key silently stops that host from reporting at all."""
        for key in validate.MCP_HEADER_KEYS:
            with self.subTest(key=key):
                path = self.root / MCP_CONFIG
                config = validate.load_json(path)
                config["mcpServers"]["aip"].pop(key)
                path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

                with self.assertRaisesRegex(AssertionError, key):
                    validate.main(self.root)

                shutil.copy(REPO / MCP_CONFIG, path)

    def test_stale_latest_version_fails(self) -> None:
        (self.root / "releases/_latest_version.json").write_text('{"version": "0.0.1"}\n', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "six version fields must match"):
            validate.main(self.root)

    def test_missing_latest_release_log_fails(self) -> None:
        version = validate.load_json(self.root / "releases/_latest_version.json")["version"]
        (self.root / f"releases/v{version}.md").unlink()
        with self.assertRaisesRegex(AssertionError, "must have a release log"):
            validate.main(self.root)

    def test_unfilled_release_log_fails(self) -> None:
        version = validate.load_json(self.root / "releases/_latest_version.json")["version"]
        path = self.root / f"releases/v{version}.md"
        path.write_text(f"# v{version}\n\n{{{{changes}}}}\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "template placeholders"):
            validate.main(self.root)

    def test_skill_name_mismatch_fails(self) -> None:
        self.rewrite(str(ENTRY_SKILL), "name: aip", "name: renamed-skill")

        with self.assertRaisesRegex(AssertionError, "skill name must match directory"):
            validate.main(self.root)

    def test_skill_without_description_fails(self) -> None:
        skill = self.root / ENTRY_SKILL
        contents = skill.read_text(encoding="utf-8")
        head, _, rest = contents.partition("description:")
        _, _, after_line = rest.partition("\n")
        skill.write_text(head + after_line, encoding="utf-8")

        with self.assertRaisesRegex(AssertionError, "frontmatter description"):
            validate.main(self.root)

    def test_skill_over_line_guidance_fails(self) -> None:
        skill = self.root / ENTRY_SKILL
        padding = "\n<!-- padding -->" * (validate.MAX_SKILL_LINES + 1)
        skill.write_text(skill.read_text(encoding="utf-8") + padding, encoding="utf-8")

        with self.assertRaisesRegex(AssertionError, "over the .*-line guidance"):
            validate.main(self.root)

    def test_manifest_declaring_hooks_fails(self) -> None:
        for directory in (".codex-plugin", ".claude-plugin"):
            with self.subTest(host=directory):
                path = self.root / "plugins/aip" / directory / "plugin.json"
                original = path.read_text(encoding="utf-8")
                payload = json.loads(original)
                payload["hooks"] = "./lifecycle.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaisesRegex(AssertionError, "must not declare lifecycle hooks"):
                    validate.main(self.root)
                path.write_text(original, encoding="utf-8")

    def test_bundled_hook_file_fails(self) -> None:
        for relative in ("hooks/hooks.json", ".claude-plugin/hooks.json", ".codex-plugin/hooks.json"):
            with self.subTest(path=relative):
                path = self.root / "plugins/aip" / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('{"hooks": {}}', encoding="utf-8")
                with self.assertRaisesRegex(AssertionError, "must not bundle lifecycle hooks"):
                    validate.main(self.root)
                path.unlink()


if __name__ == "__main__":
    unittest.main()
