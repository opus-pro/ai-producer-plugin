# Release history

This directory records the declared plugin version and release notes. Preparing or backfilling these files does not create a tag or publish a GitHub Release.

## latest_version.json

`latest_version.json` is the canonical declared version in the repository, with only a `version` field and no `v` prefix:

```json
{
  "version": "1.1.3"
}
```

It must match both host manifests, the Claude marketplace entry, and both MCP version headers. It records repository state, which may be ahead of the latest published GitHub Release while a release is being prepared. Backfilling older notes does not change this value.

## template.md

Use `template.md` for new releases. From the repository root, run `python3 scripts/prepare_release.py X.Y.Z` to align all six version values and create `releases/vX.Y.Z.md`. The helper fills the version and previous-version placeholders, including the final Full Changelog comparison link; complete the remaining content before running checks.

Changes, Compatibility, and Validation are optional and appear in that order when retained. Delete sections and categories with nothing noteworthy to report. Group concise change summaries by category and end each entry with one or more related PR-number links. Do not leave placeholders or empty sections.

Keep each version update in its own PR titled `chore: release vX.Y.Z`. Follow the shared [release rule](../.agents/rules/release.md) and [contributing guide](../CONTRIBUTING.md) for the allowed files and checks. Changes to this README, the template, or release tooling belong in ordinary PRs.

## Legacy releases

The [GitHub Releases](https://github.com/opus-pro/ai-producer-plugin/releases) from `v1.0.0` through `v1.1.2` predate this template. Their published bodies are preserved as legacy notes, with a `# vX.Y.Z` heading added and line endings normalized. They may use different headings, omit PR links, or use a plain Full Changelog URL. The first release links to its tag's commit history because it has no previous release. These historical formats are supported and do not need to be rewritten to match the template.

The `v1.1.3.md` log was already summarized in the new format when version tracking was introduced. Together, the seven logs cover all versions published at the time of the initial import. Published release notes are the source for historical statements; they do not mean that old validation or integration checks were rerun during the backfill.

The initial version-tracking PR may add historical logs at or below the declared version, without modifying any existing logs. The checker requires matching version headings and nonempty content without template placeholders for imported legacy logs, while the current log must follow the new format. Once version tracking exists on the base branch, historical logs are immutable and cannot be added or changed by ordinary PRs. New releases must follow `template.md`; the legacy exemption does not apply to them.
