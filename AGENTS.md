# AI Producer Plugin

This repository owns the public OpusClip AI Producer plugin for Codex and Claude Code. Read README.md and CONTRIBUTING.md before changing the package.

For local plugin setup, installation, updates, debugging, or cost/quality comparisons, use [aip-plugin-local](.agents/skills/aip-plugin-local/SKILL.md). It responds to `/aip-plugin-local` and requests such as "install the local plugin", "update the local plugin", or "compare the cost and quality of these two runs". This developer workflow stays outside the distributed runtime skills.

- Keep public plugin content in `plugins/aip/`; retain both host manifests and both marketplaces as separate files.
- Preserve marketplace `ai-producer-plugins`, plugin `aip`, and server `aip` unless a coordinated migration is requested.
- Keep the production MCP URL and OAuth resource aligned.
- Ship only skills and MCP configuration: no lifecycle hooks, no self-update commands. Installation and updates belong to the host client.
- Skills teach capabilities; tool descriptions own service procedures and refusals. Keep each SKILL.md at most 500 lines, with its linked references and helper scripts.
- Run `python3 scripts/test.py` after changes; validate packaging changes with both host parsers. State which checks actually ran.
- Keep CI runnable without service credentials or private runners. Employee environments, private integration tests, internal notifications, and release orchestration belong outside this repository.
- Never add personal data, private transcripts, credentials, internal tickets, private infrastructure addresses, or developer-specific paths; inspect the full public diff and metadata before publishing.
- Preserve third-party notices. Use ASCII punctuation in agent instructions and English repository prose, with one source line per prose block.
- Scope `skills/aip/` to AIP capabilities and the workspace file contract, and the bundled `aip-composition` skill to the composition, timing, and editor contract. Authoring tools are selected separately; do not bundle framework dependencies or rendering implementations. Verify file requirements against the service before changing the contract.
- Follow semantic versioning. Bump the version in its own pull request, never alongside functional changes; both static version-header keys must match the manifest version.
