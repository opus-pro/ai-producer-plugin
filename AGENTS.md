# AI Producer Plugin

This repository owns the public OpusClip AI Producer plugin for Codex and Claude Code. Read README.md and CONTRIBUTING.md before changing the package.

- Keep public plugin content in `plugins/aip/`; retain both host manifests and both marketplaces as separate files.
- Preserve marketplace `ai-producer-plugin`, plugin `ai-producer`, and server `ai-producer` unless a coordinated migration is requested.
- Keep the production MCP URL and OAuth resource aligned.
- Ship only skills and MCP configuration: no lifecycle hooks, no self-update commands. Installation and updates belong to the host client.
- Skills teach capabilities; tool descriptions own service procedures and refusals. Keep each SKILL.md at most 500 lines, with its linked references and helper scripts.
- Run `python3 scripts/test.py` after changes; validate packaging changes with both host parsers. State which checks actually ran.
- Keep CI runnable without service credentials or private runners. Employee environments, private integration tests, internal notifications, and internal release orchestration belong outside this repository. Codex and Claude Code publish releases locally using the user's authenticated GitHub identity; CI only validates and never publishes.
- Never add personal data, private transcripts, credentials, internal tickets, private infrastructure addresses, or developer-specific paths; inspect the full public diff and metadata before publishing.
- Preserve third-party notices. Use ASCII punctuation in agent instructions and English repository prose, with one source line per prose block.
- Scope `skills/aip/` to AIP capabilities and the workspace file contract, and the bundled `aip-composition` skill to the composition, timing, and editor contract. Authoring tools are selected separately; do not bundle framework dependencies or rendering implementations. Verify file requirements against the service before changing the contract.
- For release preparation, version bumps, version alignment, or publication, read and follow the [release rule](.agents/rules/release.md). Before selecting a new version, verify the published GitHub Release version and default to a patch bump; minor or major bumps require the user's separate second confirmation before version edits. Announce the current and target versions with inspection links, then continue the default patch release without another confirmation. A full release request covers PR preparation, checks, merge, and verified publication in the same session; preparation-only requests stop at the PR. Use the PR title `chore: release vX.Y.Z`, keep the version bump in its own PR, align all six version values with `releases/latest_version.json`, and add the matching `releases/vX.Y.Z.md` log from `releases/template.md`. Publish using the user's GitHub identity.
