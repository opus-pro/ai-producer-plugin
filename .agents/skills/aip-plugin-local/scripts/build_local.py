#!/usr/bin/env python3
"""Build an isolated local AIP package or verify its installed cache."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

KIND = "aip-plugin-local-v1"
DISPLAY_NAME = "AI Producer Local"
PLUGIN_ID = "aip@ai-producer-plugins"
RECEIPT = "local-build.json"
VERSION_HEADER = "X-AIP-Plugin-Version"
SKIP_PARTS = {"__pycache__", ".git", ".DS_Store"}
SKILL_ROOT = Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def files(root: Path) -> dict[str, str]:
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Package symlink is not supported: {path.relative_to(root)}")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def endpoint(value: str) -> str:
    parsed = urlsplit(value)
    local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if (parsed.scheme != "https" and not (local and parsed.scheme == "http")) or not parsed.hostname:
        raise ValueError("MCP URL must use HTTPS, or HTTP on loopback for a local service")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("MCP URL must not contain credentials, query parameters, or fragments")
    return value


def check_owned_output(output: Path) -> None:
    if output.is_symlink():
        raise ValueError("Output must not be a symlink")
    if not output.exists():
        return
    marker = output / RECEIPT
    if not marker.is_file() or read_json(marker).get("kind") != KIND:
        raise ValueError("Refusing to replace an output directory not owned by this builder")
    expected = read_json(marker)["bundle_files"]
    actual = files(output)
    actual.pop(RECEIPT, None)
    if actual != expected:
        raise ValueError("Generated bundle was edited; preserve those edits in source before rebuilding")


def git_revision(source: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else None


def build(source: Path, output: Path, mcp_url: str | None = None) -> dict:
    source = source.expanduser().resolve()
    # Inspect symlinks before resolving a caller-supplied output path.
    output = output.expanduser().absolute()
    check_owned_output(output)
    output = output.resolve()
    plugin = source / "plugins/aip"
    if not plugin.is_dir():
        raise ValueError("Source must be an AIP checkout containing plugins/aip")
    if source.is_relative_to(output) or output.is_relative_to(plugin):
        raise ValueError("Output must not contain the source or sit inside the runtime package")
    source_files = files(plugin)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".aip-local-build-", dir=output.parent) as temp:
        stage = Path(temp) / "marketplace"
        target = stage / "plugins/aip"
        for relative in source_files:
            rel = Path(relative)
            if set(rel.parts) & SKIP_PARTS or rel.suffix in {".pyc", ".pyo"}:
                continue
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(plugin / rel, dest)
        manifests = [target / host / "plugin.json" for host in (".codex-plugin", ".claude-plugin")]
        codex, claude = (read_json(path) for path in manifests)
        if codex.get("name") != "aip" or claude.get("name") != "aip":
            raise ValueError("Both source manifests must identify plugin aip")
        if codex.get("version") != claude.get("version"):
            raise ValueError("Source manifest versions differ")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        version = f"{codex['version'].split('+', 1)[0]}+codex.{stamp}"
        for manifest in (codex, claude):
            if "hooks" in manifest:
                raise ValueError("This workflow builds the public package without lifecycle hooks")
            manifest["version"] = version
        codex["interface"].update(
            displayName=DISPLAY_NAME, composerIcon="./assets/local.svg", logo="./assets/local.svg"
        )
        claude["description"] = f"{DISPLAY_NAME}. {claude['description']}"
        shutil.copyfile(SKILL_ROOT / "assets/local.svg", target / "assets/local.svg")
        for path, data in zip(manifests, (codex, claude)):
            write_json(path, data)
        config = read_json(target / ".mcp.json")
        server = config["mcpServers"]["aip"]
        if server.get("url") != server.get("oauth_resource"):
            raise ValueError("Source MCP URL and OAuth resource differ")
        selected_url = endpoint(mcp_url or server["url"])
        server["url"] = server["oauth_resource"] = selected_url
        for key in ("headers", "http_headers"):
            headers = server.setdefault(key, {})
            if any(word in name.lower() for name in headers for word in ("authorization", "token", "secret", "api-key")):
                raise ValueError("Do not store credentials in the plugin's static MCP headers")
            headers[VERSION_HEADER] = version
        write_json(target / ".mcp.json", config)
        for relative in (".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json"):
            market = read_json(source / relative)
            if market.get("name") != "ai-producer-plugins" or [p["name"] for p in market["plugins"]] != ["aip"]:
                raise ValueError("Source marketplace must contain only aip in ai-producer-plugins")
            entry = market["plugins"][0]
            if relative.startswith(".agents"):
                entry["source"] = {"source": "local", "path": "./plugins/aip"}
                market.setdefault("interface", {})["displayName"] = DISPLAY_NAME
            else:
                entry.update(source="./plugins/aip", version=version, description=claude["description"])
            write_json(stage / relative, market)
        receipt = {
            "kind": KIND, "display_name": DISPLAY_NAME, "plugin_id": PLUGIN_ID,
            "source": str(source), "source_commit": git_revision(source),
            "source_files": source_files, "version": version, "mcp_url": selected_url,
            "plugin_files": files(target), "bundle_files": files(stage),
        }
        write_json(stage / RECEIPT, receipt)
        backup = Path(temp) / "previous"
        if output.exists():
            output.rename(backup)
        try:
            stage.rename(output)
        except OSError:
            if backup.exists():
                backup.rename(output)
            raise
    return receipt


def verify(bundle: Path, cache: Path) -> dict:
    check_owned_output(bundle)
    receipt = read_json(bundle / RECEIPT)
    actual = files(cache)
    if actual != receipt["plugin_files"]:
        raise ValueError("Installed cache does not match the built package")
    return {"verified": True, "version": receipt["version"], "files": len(actual)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("build")
    create.add_argument("--source", type=Path, required=True)
    create.add_argument("--output", type=Path, required=True)
    create.add_argument("--mcp-url")
    check = commands.add_parser("verify")
    check.add_argument("--bundle", type=Path, required=True)
    check.add_argument("--cache", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "build":
            result = build(args.source, args.output, args.mcp_url)
            result = {key: result[key] for key in ("display_name", "plugin_id", "source", "source_commit", "version", "mcp_url")}
        else:
            result = verify(args.bundle, args.cache)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
