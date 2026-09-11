# release

Follow this rule whenever asked to prepare a release, bump the plugin version, or align release metadata in this repository. Release preparation updates local version files and a release log; it does not publish a tag or GitHub Release.

## Version source

`releases/latest_version.json` is the canonical declared plugin version. Its complete shape is `{"version": "X.Y.Z"}`. It records the version in the repository, not confirmation of publication on GitHub. The helper files `latest_version.json` and `template.md` sort before the `vX.Y.Z.md` release logs by name.

Keep these six values identical:

- `releases/latest_version.json`: `version`.
- `plugins/aip/.codex-plugin/plugin.json`: `version`.
- `plugins/aip/.claude-plugin/plugin.json`: `version`.
- `.claude-plugin/marketplace.json`: the AIP entry's `version`.
- `plugins/aip/.mcp.json`: `mcpServers.aip.headers.X-AIP-Plugin-Version` and `mcpServers.aip.http_headers.X-AIP-Plugin-Version`.

Use the user's requested version when provided. Otherwise inspect the unreleased changes and select patch for compatible fixes, minor for new compatible behavior, or major for breaking changes; state the choice. Use SemVer without `v` in JSON, and with `v` in log names and PR titles. Prerelease and build suffixes are allowed, but a build-metadata-only change is not a version increase. The new version must have greater precedence than both the starting version and the current base branch version.

## Prepare a release PR

1. Read `AGENTS.md`, `CONTRIBUTING.md`, the latest-version file, and the latest release log. Check the working tree and the current base branch. Keep unrelated user changes intact and use a dedicated release branch or isolated worktree if needed. Functional changes must already be in the base branch.
2. Run `python3 scripts/prepare_release.py X.Y.Z` with the selected version. This validates the current copies, aligns all six version values, and copies `releases/template.md` into a new `releases/vX.Y.Z.md`. If existing versions disagree, inspect and resolve the discrepancy before preparing a new release.
3. Complete the new log using the format below. Replace placeholders in retained sections and delete unused sections and categories entirely. Use public information and preserve third-party notices; never include private data or invent validation results. Keep the full validation evidence and checks not run in the PR description even when the release log omits Validation.
4. Run `python3 scripts/test.py` and the packaging checks required by `CONTRIBUTING.md`. Inspect the complete diff. A release PR may change only the version fields in the five JSON files above and add exactly one matching release log. Keep `template.md`, previous logs, rules, scripts, workflow configuration, and functional changes out of the release PR.
5. After the release changes are committed, run `python3 scripts/check_release_pr.py --base origin/main --head HEAD --title 'chore: release vX.Y.Z'`, using the actual PR base when it differs from `main`. Fetch complete base and head history first. The committed PR diff is what this check validates.
6. Use the exact PR title `chore: release vX.Y.Z`, replacing `X.Y.Z` with the version in the JSON files and log. Include the release summary and validation results in the PR description. Merge and publication follow the maintainer's authorization; a request to prepare a release does not by itself authorize publishing it.

## Release log format

- Start with `# vX.Y.Z`. Changes, Compatibility, and Validation are optional; retain that order when present. Omit sections without noteworthy content, including routine "no migration needed" or "all checks passed" statements.
- Under Changes, group short, user-visible summaries under categories such as `### Added`, `### Changed`, and `### Fixed`. Combine related PRs into one change rather than repeating their titles. Omit empty categories.
- End each change with its actual PR numbers and links, for example `- Clarify the intake workflow. ([#11](https://github.com/opus-pro/ai-producer-plugin/pull/11), [#13](https://github.com/opus-pro/ai-producer-plugin/pull/13))`. Verify the linked PRs belong to the release range. One change may reference multiple PRs.
- End the log with `**Full Changelog**: [vPREVIOUS...vX.Y.Z](https://github.com/opus-pro/ai-producer-plugin/compare/vPREVIOUS...vX.Y.Z)`. The preparation script fills both versions using the current declared version and the requested version. Check the comparison range before submitting; it must start at the current PR base version.

See the [release directory guide](../../releases/README.md) for legacy notes. Published `v1.0.0` through `v1.1.2` bodies retain their original format and are exempt from the new template; `v1.1.3.md` already follows the new format. Do not rewrite legacy notes or apply their exemption to new releases. Verify imported content against GitHub Releases without inventing PR associations or validation results.

## CI enforcement

The `Release PR policy` check detects version changes regardless of title, checks the complete PR diff against the allowed files and fields, verifies all six version values and the new release log, and rejects version reuse or decreases. Historical release logs are append-only. Only during initial adoption, when neither the starting commit nor the current base has version tracking, may an ordinary tooling PR add historical logs at or below the declared version; existing logs cannot be changed. Ordinary PRs otherwise keep version values and logs unchanged; template or release-tooling changes belong in their own ordinary PRs. Repository maintainers must make this check required and require the branch to be up to date before merging.
