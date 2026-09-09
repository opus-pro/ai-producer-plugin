# Contributing

Open an issue for a bug or proposal, or submit a focused pull request. Include the expected behavior, observed behavior, and steps to reproduce. Use synthetic examples; do not upload private footage, transcripts, credentials, project identifiers, or account data.

## Local checks

Python 3.10 or newer is sufficient for the offline checks:

```bash
python3 scripts/test.py
```

The suite validates both manifests, marketplace entries, MCP version headers, skill structure, package-relative Markdown links, and the absence of lifecycle hooks. No authentication or hosted processing is performed.

For packaging changes, validate the marketplace and bundle with Claude Code and test marketplace discovery in an isolated Codex profile. Report client versions and distinguish static validation from authenticated integration checks. CI runs on GitHub-hosted runners without service credentials; private integration checks are maintained separately.

## Ownership and compatibility

This repository owns the public client plugin. Keep shared editing knowledge under `plugins/aip/skills/` and keep the Codex and Claude manifests separate. Do not introduce employee environments, private fixtures, internal notification integrations, or organization-specific release orchestration.

Preserve the `ai-producer-plugins` marketplace identifier, `aip` plugin name, and `aip` MCP server name unless a change includes an explicit migration. The plugin contains no lifecycle hooks or self-update commands. Users manage installation and updates through their client.

## Workspace contract

Keep the plugin focused on AIP capabilities and the workspace files accepted by the service. The editing skill and its workspace reference live under `plugins/aip/skills/aip/`. The agent chooses its authoring tools; this package does not install an authoring framework or bundle framework manuals, animation runtimes, or caption implementations.

Verify workspace requirements against the service's current acceptance and playback behavior. Separate required files from optional conventions, and transfer acceptance from preview/export validation. Tool descriptions own service procedures and costs; the workspace reference owns the file contract.

## Versions

For a plugin-content change, update the semantic version in both plugin manifests, the Claude marketplace entry, and `X-AIP-Plugin-Version` under both `headers` and `http_headers` in `.mcp.json`. The validator checks that these values agree. Documentation-only or test-only changes do not require a plugin version bump.

Use patch versions for compatible fixes, minor versions for new behavior, and major versions for breaking changes. Describe user-visible behavior and validation in the pull request. Release maintainers review and publish changes; the CI workflow does not publish a release.

## Source and assets

Submit only material you have the right to contribute under this repository's license. Preserve applicable third-party notices. Do not add recordings or copied assets without a documented redistribution basis. Contribution review includes the complete diff and public issue or pull-request text, including links and screenshots.
