#!/usr/bin/env python3
"""Validate cross-client AI Producer plugin invariants.

Structural invariants (manifests, marketplaces, MCP config, icon, no lifecycle
hooks) and the two skill invariants (a SKILL.md names its directory and
carries a description; its body stays under the host's line guidance) live
here. There is no content contract on skill wording: what a skill promises is
reviewed in the PR, not pinned by substring. Every check takes an explicit repo
root so the test suite can run it against broken fixture trees.
"""

from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIRNAME = "aip"
EXPECTED_REPOSITORY = "https://github.com/opus-pro/ai-producer-plugin"
EXPECTED_ENDPOINT = "https://producer.opus.pro/api/mcp"
EXPECTED_SKILLS = {"aip", "hyperframes"}


# The service needs the plugin version on each tool call.
PLUGIN_VERSION_HEADER = "X-AIP-Plugin-Version"
# Both host-specific header keys carry the same version.
MCP_HEADER_KEYS = ("headers", "http_headers")
SEMVER = re.compile(
    r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
# Claude Code's published guidance for a skill body. The description is always
# in context and the body loads on invocation, so a body past this point is a
# skill that has started carrying procedure the tool replies should carry.
MAX_SKILL_LINES = 500


def plugin_dir(root: Path) -> Path:
    return root / "plugins" / PLUGIN_DIRNAME


def load_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    assert header[:8] == b"\x89PNG\r\n\x1a\n", f"asset must be PNG: {path}"
    return struct.unpack(">II", header[16:24])


def skill_dirs(root: Path) -> list[Path]:
    dirs = sorted(p.parent for p in (plugin_dir(root) / "skills").glob("*/SKILL.md"))
    assert dirs, "plugin must ship at least one skill"
    return dirs


def validate_manifests(root: Path) -> str:
    plugin = plugin_dir(root)
    codex_manifest = load_json(plugin / ".codex-plugin" / "plugin.json")
    claude_manifest = load_json(plugin / ".claude-plugin" / "plugin.json")

    assert codex_manifest["name"] == claude_manifest["name"] == PLUGIN_DIRNAME
    version = codex_manifest["version"]
    assert version == claude_manifest["version"], "manifest versions must match"
    assert isinstance(version, str) and SEMVER.fullmatch(version)
    assert codex_manifest["repository"] == claude_manifest["repository"] == EXPECTED_REPOSITORY
    assert (plugin / str(codex_manifest["skills"])).is_dir()
    assert (plugin / str(codex_manifest["mcpServers"])).is_file()

    interface = codex_manifest["interface"]
    assert isinstance(interface, dict)
    assert interface["composerIcon"] == interface["logo"] == "./assets/icon.png"
    for field in ("composerIcon", "logo"):
        asset = interface[field]
        assert isinstance(asset, str) and (plugin / asset).is_file()
    icon_width, icon_height = png_dimensions(plugin / "assets" / "icon.png")
    assert icon_width == icon_height >= 512, "plugin icon must be square and at least 512px"
    return version


def validate_marketplaces(root: Path, version: str) -> None:
    codex_marketplace = load_json(root / ".agents" / "plugins" / "marketplace.json")
    claude_marketplace = load_json(root / ".claude-plugin" / "marketplace.json")

    assert codex_marketplace["name"] == claude_marketplace["name"] == "ai-producer-plugins"
    codex_entry = codex_marketplace["plugins"][0]  # type: ignore[index]
    claude_entry = claude_marketplace["plugins"][0]  # type: ignore[index]
    assert codex_entry["name"] == claude_entry["name"] == PLUGIN_DIRNAME  # type: ignore[index]
    assert codex_entry["source"]["path"] == f"./plugins/{PLUGIN_DIRNAME}"  # type: ignore[index]
    assert claude_entry["source"] == f"./plugins/{PLUGIN_DIRNAME}"  # type: ignore[index]
    assert claude_entry["version"] == version  # type: ignore[index]


def validate_mcp(root: Path, version: str) -> None:
    mcp = load_json(plugin_dir(root) / ".mcp.json")
    aip = mcp["mcpServers"]["aip"]  # type: ignore[index]
    assert aip["type"] == "http"  # type: ignore[index]
    assert aip["url"] == aip["oauth_resource"] == EXPECTED_ENDPOINT  # type: ignore[index]

    # A version bump that forgets this header leaves the service reading a stale
    # version for every install of the new bundle, and nothing else fails, so
    # pin it to the manifests here.
    for key in MCP_HEADER_KEYS:
        headers = aip.get(key)  # type: ignore[union-attr]
        assert isinstance(headers, dict) and headers, (
            f".mcp.json must set {key!r}; without it the "
            f"{'Claude Code' if key == 'headers' else 'Codex'} bundle sends no "
            f"{PLUGIN_VERSION_HEADER} and the service cannot tell which plugin called"
        )
        declared = headers.get(PLUGIN_VERSION_HEADER)
        assert declared == version, (
            f".mcp.json {key}.{PLUGIN_VERSION_HEADER} is {declared!r} but the plugin "
            f"manifests ship {version!r}; bump the header with the version"
        )


def validate_skill_structure(root: Path) -> None:
    directories = skill_dirs(root)
    assert {path.name for path in directories} == EXPECTED_SKILLS, "unexpected bundled skill set"
    for skill_dir in directories:
        skill = skill_dir / "SKILL.md"
        contents = skill.read_text(encoding="utf-8")
        match = re.search(r"^name:\s*([^\s]+)\s*$", contents, re.MULTILINE)
        assert match and match.group(1) == skill_dir.name, (
            f"skill name must match directory: {skill}"
        )
        description = re.search(r"^description:\s*(\S.*)$", contents, re.MULTILINE)
        assert description, f"skill must carry a frontmatter description: {skill}"
        lines = contents.count("\n")
        assert lines <= MAX_SKILL_LINES, (
            f"skill {skill_dir.name} is {lines} lines, over the {MAX_SKILL_LINES}-line guidance; "
            f"move long material into references/ and point at it from SKILL.md"
        )


def validate_host_hooks(root: Path) -> None:
    """The client plugin must not run code through lifecycle hooks."""
    plugin = plugin_dir(root)
    for directory in (".codex-plugin", ".claude-plugin"):
        manifest = load_json(plugin / directory / "plugin.json")
        assert "hooks" not in manifest, f"{directory} must not declare lifecycle hooks"
    hooks = sorted(str(path.relative_to(plugin)) for path in plugin.rglob("hooks*.json"))
    assert not hooks, f"plugin must not bundle lifecycle hooks: {hooks}"


def validate_relative_links(root: Path) -> None:
    """A distribution must retain the local Markdown references its skills load."""
    for source in plugin_dir(root).rglob("*.md"):
        for target in re.findall(r"\[[^\]]+\]\(([^\s)]+)\)", source.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            path = (source.parent / target.split("#", 1)[0]).resolve()
            assert path.is_relative_to(plugin_dir(root).resolve()), f"reference escapes package: {source}: {target}"
            assert path.exists(), f"missing relative reference: {source}: {target}"


def main(root: Path = ROOT) -> None:
    version = validate_manifests(root)
    validate_marketplaces(root, version)
    validate_mcp(root, version)
    validate_skill_structure(root)
    validate_host_hooks(root)
    validate_relative_links(root)
    print(f"Validated {PLUGIN_DIRNAME} {version} for Codex and Claude Code")


if __name__ == "__main__":
    main()
