# Release history

This directory records the declared plugin version and release notes. Local preparation does not publish. After an authorized release PR merge, Codex or Claude Code completes publication using the user's GitHub identity as described below; existing tags are preserved.

## latest_version.json

`latest_version.json` is the canonical declared version in the repository, with only a `version` field and no `v` prefix:

```json
{
  "version": "1.1.3"
}
```

It must match both host manifests, the Claude marketplace entry, and both MCP version headers. It records repository state, which may be ahead of the latest published GitHub Release while a release is being prepared. Backfilling older notes does not change this value.

## template.md

Use `template.md` for new releases. First follow the shared [version-selection procedure](../.agents/rules/release.md#choose-a-new-version): verify the published GitHub Release version, default to the next patch, and obtain a separate second confirmation before any minor or major version edits. From the repository root, run `python3 scripts/prepare_release.py X.Y.Z` with that selected version to align all six version values and create `releases/vX.Y.Z.md`. The helper fills the version and Full Changelog comparison link; v1.2.9 uses v1.2.7 as its comparison base because the deleted immutable v1.2.8 tag cannot be reused. Complete the remaining content before running checks.

Changes, Compatibility, and Validation are optional and appear in that order when retained. Delete sections and categories with nothing noteworthy to report. Group concise change summaries by category and end each entry with one or more related PR-number links. Do not leave placeholders or empty sections.

Keep each version update in its own PR titled `chore: release vX.Y.Z`. Follow the shared [release rule](../.agents/rules/release.md) and [contributing guide](../CONTRIBUTING.md) for the allowed files and checks. Changes to this README, the template, or release tooling belong in ordinary PRs.

## Publication with a user account

Codex and Claude Code use the shared [release rule](../.agents/rules/release.md#request-scope-and-progress) to complete a full release request in one session with the user's authenticated GitHub CLI session: fetch the published version, announce the target and inspection links, prepare the PR, wait for checks and required reviews, merge, publish, and verify. Default patch releases continue without another version or merge confirmation; minor and major increases require the user's separate second confirmation before version edits. A preparation-only request stops at the PR. CI continues to validate the package and release PR policy; it does not create tags or Releases.

The agent verifies the release PR's merged commit is on upstream `main`, validates the declared version and matching log in a clean worktree at that commit, and creates `vX.Y.Z` there. It then publishes a GitHub Release named `vX.Y.Z` using the log verbatim. Only the authorized version is published. Prereleases are marked accordingly, and publication is verified before the agent reports the Release URL.

Publication requires the user's account to have permission to create tags and Releases in `opus-pro/ai-producer-plugin`. Authentication, repository access, or API failures leave publication pending with the specific error; they are not treated as missing tags. No Actions token or CI runner is involved.

Existing tags and Releases are preserved. If a tag points to the intended merged commit and its Release is already published, the agent verifies and reports it. If the tag exists but its Release is absent, the agent can finish the authorized publication with `gh release create --verify-tag` and the validated log. A conflicting tag or Release is reported without overwriting it. See the shared rule's [existing-tag and recovery procedure](../.agents/rules/release.md#existing-tags-and-partial-publication) for the commands and checks.

## Legacy releases

The [GitHub Releases](https://github.com/opus-pro/ai-producer-plugin/releases) from `v1.0.0` through `v1.1.2` predate this template. Their published bodies are preserved as legacy notes, with a `# vX.Y.Z` heading added and line endings normalized. They may use different headings, omit PR links, or use a plain Full Changelog URL. The first release links to its tag's commit history because it has no previous release. These historical formats are supported and do not need to be rewritten to match the template.

The `v1.1.3.md` log was already summarized in the new format when version tracking was introduced. Together, the seven logs cover all versions published at the time of the initial import. Published release notes are the source for historical statements; they do not mean that old validation or integration checks were rerun during the backfill.

The initial version-tracking PR may add historical logs at or below the declared version, without modifying any existing logs. The checker requires matching version headings and nonempty content without template placeholders for imported legacy logs, while the current log must follow the new format. Once version tracking exists on the base branch, historical logs are immutable and cannot be added or changed by ordinary PRs. New releases must follow `template.md`; the legacy exemption does not apply to them.
