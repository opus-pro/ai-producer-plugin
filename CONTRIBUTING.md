# Contributing

Open an issue for a bug or proposal, or submit a focused pull request. Include the expected behavior, observed behavior, and steps to reproduce. Use synthetic examples; do not upload private footage, transcripts, credentials, project identifiers, or account data.

## Local checks

Python 3.9 or newer is sufficient for the offline checks:

```bash
python3 scripts/test.py
```

The suite validates both manifests, marketplace entries, MCP version headers, skill structure, package-relative Markdown links, and the absence of lifecycle hooks. No authentication or hosted processing is performed.

For packaging changes, validate the marketplace and bundle with Claude Code and test marketplace discovery in an isolated Codex profile. Report client versions and distinguish static validation from authenticated integration checks. CI runs on GitHub-hosted runners without service credentials; private integration checks are maintained separately.

## Ownership and compatibility

This repository owns the public client plugin. Keep shared editing knowledge under `plugins/aip/skills/` and keep the Codex and Claude manifests separate. Do not introduce employee environments, private fixtures, internal notification integrations, or organization-specific release orchestration.

Preserve the `ai-producer-plugins` marketplace identifier, `aip` plugin name, and `aip` MCP server name unless a change includes an explicit migration. The plugin contains no lifecycle hooks or self-update commands. Users manage installation and updates through their client.

## Workspace contract

Keep the plugin focused on AIP capabilities and the workspace files accepted by the service. The editing skill and its workspace reference live under `plugins/aip/skills/aip/`. The `aip-composition` skill describes the composition, timing, and editor contract. The agent chooses its authoring tools; this package does not install an authoring framework or bundle animation runtimes or caption implementations.

Verify workspace requirements against the service's current acceptance and playback behavior. Separate required files from optional conventions, and transfer acceptance from preview/export validation. Tool descriptions own service procedures and costs; the workspace reference owns the file contract.

## Versions

Follow the shared [release rule](.agents/rules/release.md) when preparing a version update. Codex reaches it through `AGENTS.md`; Claude Code imports it through `CLAUDE.md`. Merge functional changes through ordinary PRs first, then prepare a separate PR titled exactly `chore: release vX.Y.Z`, for example `chore: release v1.1.4`. Documentation-only or test-only changes do not require a plugin version bump.

`releases/latest_version.json` is the canonical declared version. A release PR may change only the version fields in these five files and add the matching `releases/vX.Y.Z.md` log:

- `releases/latest_version.json`: `version`.
- `plugins/aip/.codex-plugin/plugin.json`: `version`.
- `plugins/aip/.claude-plugin/plugin.json`: `version`.
- `.claude-plugin/marketplace.json`: the AIP entry's `version`.
- `plugins/aip/.mcp.json`: `X-AIP-Plugin-Version` under both `headers` and `http_headers`.

All six values must agree with the PR title and log version, and the version must increase in SemVer precedence over both the PR's starting version and the current base version. Prerelease and build suffixes are supported; a metadata-only change does not increase precedence. Other fields in those JSON files, other files, renames, deletions, and file-mode changes are not allowed in a release PR. Historical logs cannot be changed. Template and release-tooling changes belong in separate ordinary PRs.

Prepare the files locally, then complete the generated log. Omit Changes, Compatibility, or Validation when there is nothing noteworthy to report. Group changes by category, summarize related PRs together, and append one or more PR-number links to each change. Keep the generated Full Changelog comparison link at the end. Unfilled placeholders and empty retained sections fail validation. Full validation evidence belongs in the PR description even when omitted from the log. This command does not commit, push, tag, or publish:

```bash
python3 scripts/prepare_release.py 1.1.4
# Fill in releases/v1.1.4.md before running checks.
python3 scripts/test.py
```

The directory uses `latest_version.json` and `template.md` for its two helper files, followed by `vX.Y.Z.md` logs when sorted by name. See the [release directory guide](releases/README.md) for their usage and the initial import of published `v1.0.0` through `v1.1.3` notes. Legacy logs retain their published format; new releases follow the template. The initial import may add historical logs at or below the declared version without editing existing logs, and does not publish another release. Once tracking exists, ordinary PRs cannot add or change historical logs.

The `Validate release PR` workflow runs on PR creation, reopening, new commits, and edits, including title changes. It detects version updates regardless of the PR title and validates ordinary PRs for version consistency. It runs the trusted validator from the workflow's commit and reads PR Git objects without checking out or executing PR code. It needs no credentials. After this workflow reaches the default branch, configure `Release PR policy` as a required status check and require branches to be up to date before merging so the base-version comparison stays current.

To run the same check locally with both commits and their history fetched:

```bash
python3 scripts/check_release_pr.py --base origin/main --head HEAD --title 'chore: release v1.1.4'
```

Use patch versions for compatible fixes, minor versions for new behavior, and major versions for breaking changes. Describe user-visible behavior and validation in the pull request. Release maintainers review and publish changes; the CI workflow does not publish a release.

## Source and assets

Submit only material you have the right to contribute under this repository's license. Preserve applicable third-party notices. Do not add recordings or copied assets without a documented redistribution basis. Contribution review includes the complete diff and public issue or pull-request text, including links and screenshots.
