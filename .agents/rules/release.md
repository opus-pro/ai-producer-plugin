# release

Follow this rule whenever asked to prepare or publish a release, bump the plugin version, align release metadata, or finish a merged release in this repository. Codex and Claude Code share this procedure. Preparation updates version files and a release log; after an authorized merge, the agent completes tag and GitHub Release publication by default using the user's authenticated GitHub identity. CI only validates; there is no publication workflow to wait for or rerun.

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
6. Use the exact PR title `chore: release vX.Y.Z`, replacing `X.Y.Z` with the version in the JSON files and log. Include the release summary and validation results in the PR description. A request to prepare a release does not by itself authorize merging it. Approval to merge a release PR also authorizes the agent to publish that release with the user's GitHub identity. After the merge completes, continue with publication without requesting the same approval again, unless the user explicitly limited the task to merging or preparation.

## Release log format

- Start with `# vX.Y.Z`. Changes, Compatibility, and Validation are optional; retain that order when present. Omit sections without noteworthy content, including routine "no migration needed" or "all checks passed" statements.
- Under Changes, group short, user-visible summaries under categories such as `### Added`, `### Changed`, and `### Fixed`. Combine related PRs into one change rather than repeating their titles. Omit empty categories.
- End each change with its actual PR numbers and links, for example `- Clarify the intake workflow. ([#11](https://github.com/opus-pro/ai-producer-plugin/pull/11), [#13](https://github.com/opus-pro/ai-producer-plugin/pull/13))`. Verify the linked PRs belong to the release range. One change may reference multiple PRs.
- End the log with `**Full Changelog**: [vPREVIOUS...vX.Y.Z](https://github.com/opus-pro/ai-producer-plugin/compare/vPREVIOUS...vX.Y.Z)`. The preparation script fills both versions using the current declared version and the requested version. Check the comparison range before submitting; it must start at the current PR base version.

See the [release directory guide](../../releases/README.md) for legacy notes. Published `v1.0.0` through `v1.1.2` bodies retain their original format and are exempt from the new template; `v1.1.3.md` already follows the new format. Do not rewrite legacy notes or apply their exemption to new releases. Verify imported content against GitHub Releases without inventing PR associations or validation results.

## Publish with the user's GitHub identity

1. Use the local GitHub CLI authenticated as the user. Check `gh auth status --active --hostname github.com` and `gh api --hostname github.com user --jq .login`. Use this identity for both tag and Release creation. Do not use an Actions `GITHUB_TOKEN`, a bot account, or simulated CI environment variables. If authentication or repository access fails, report the exact blocker and leave publication pending; never print tokens or fall back to CI.
2. Confirm the release PR is merged into `opus-pro/ai-producer-plugin` on `main`, and record its merged commit SHA with `gh pr view <pr-number> --repo opus-pro/ai-producer-plugin --json state,baseRefName,mergeCommit,url`. Fetch upstream main and verify that SHA is in its history. Use the release PR's merged commit, even if main has advanced; never tag the unmerged PR head or an arbitrary local HEAD.
3. Use a clean detached worktree at that SHA to read `releases/latest_version.json` and its matching `releases/vX.Y.Z.md`. Confirm the version matches the authorized release and run `python3 scripts/test.py` there before any writes. This checks all six version values and the release log. Missing metadata, a missing log, or failed validation blocks publication. Publish only this declared version; do not scan historical logs to create other releases.
4. Look up the remote tag with `gh api --hostname github.com repos/opus-pro/ai-producer-plugin/git/ref/tags/vX.Y.Z`. Only HTTP 404 means the tag is absent; authentication, permission, rate-limit, and network errors block publication. If the tag exists, leave it unchanged and follow the existing-tag procedure below. Never replace, move, or delete a tag or overwrite a Release.
5. If the tag is absent, create it at the verified SHA with the command below, then create the GitHub Release with the log from the same worktree. Run these as separate steps: continue to Release creation only after successful tag creation. If another publisher creates the tag concurrently or a write has an uncertain result, inspect the remote tag and Release before continuing through the existing-tag procedure.
6. Verify the remote tag resolves to the selected merged commit, and check the Release's URL, tag, title, body, draft status, and prerelease flag against the validated log and version. Report the published URL and checks actually run. A merged PR, a created tag, or a failed CLI command is not evidence that publication completed.

From the validated worktree, set `release_tag` to the declared `vX.Y.Z` and `release_sha` to the verified full merged commit SHA. Create the tag:

```bash
gh api --hostname github.com --method POST repos/opus-pro/ai-producer-plugin/git/refs \
  -f "ref=refs/tags/$release_tag" -f "sha=$release_sha"
```

After tag creation succeeds, publish a stable release:

```bash
gh release create "$release_tag" --repo github.com/opus-pro/ai-producer-plugin \
  --verify-tag --title "$release_tag" --notes-file "releases/$release_tag.md"
```

For a SemVer prerelease, add `--prerelease --latest=false` to the Release command. Stable releases use GitHub's default latest-release selection. The Markdown log is the complete Release body; do not use generated notes or a draft. `--verify-tag` prevents implicit tag creation at a different commit. See the [GitHub CLI reference](https://cli.github.com/manual/gh_release_create) for these flags.

### Existing tags and partial publication

Resolve an existing tag to its commit, dereferencing an annotated tag if needed. If it differs from the selected merged commit, stop and report the mismatch without modifying it. If a matching published Release also exists, verify its body and metadata and report its URL without editing it. An existing draft or mismatched Release needs user direction rather than being overwritten.

If the tag matches but the Release is absent, including after tag creation succeeded and Release creation failed, complete the already-authorized publication using the same `gh release create ... --verify-tag` command and validated log. Confirm absence with the Releases API; only HTTP 404 means absent. Preserve the tag throughout recovery, and inspect remote state after an uncertain write before retrying. If access remains blocked, report the preserved tag and missing Release so the task can resume under the user's account.

## CI enforcement

The `Release PR policy` check detects version changes regardless of title, checks the complete PR diff against the allowed files and fields, verifies all six version values and the new release log, and rejects version reuse or decreases. Historical release logs are append-only. Only during initial adoption, when neither the starting commit nor the current base has version tracking, may an ordinary tooling PR add historical logs at or below the declared version; existing logs cannot be changed. Ordinary PRs otherwise keep version values and logs unchanged; template or release-tooling changes belong in their own ordinary PRs. Repository maintainers must make this check required and require the branch to be up to date before merging.
