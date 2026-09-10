# AI Producer Plugin

This repository owns the public OpusClip AI Producer plugin for Codex and Claude Code.
Read README.md and CONTRIBUTING.md before changing the package.

- Keep public plugin content in `plugins/aip/`; retain both host manifests and both marketplaces as separate files.
- Preserve marketplace `ai-producer-plugins`, plugin `aip`, and server `aip` unless a coordinated migration is requested.
- Keep the production MCP URL and OAuth resource aligned. Both static version-header keys must match the manifest version.
- The plugin ships skills and MCP configuration without lifecycle hooks or self-update commands. Installation and updates belong to the host client.
- Skills teach capabilities; tool descriptions own service procedures and refusals. Keep each SKILL.md at most 500 lines and retain its linked references and helper scripts.
- Run `python3 scripts/test.py` after changes. For packaging changes, validate with both host parsers and state which checks were actually performed.
- Keep CI runnable without service credentials or private runners. Employee environments, private integration tests, internal notifications, and release orchestration belong outside this repository.
- Never add personal data, private transcripts, credentials, internal tickets, private infrastructure addresses, or developer-specific paths. Inspect the complete proposed public diff and metadata before publishing.
- Preserve third-party notices. Use ASCII punctuation in agent instructions and English repository prose, with one source line per prose block.

- Keep `skills/aip/` focused on AIP capabilities and the workspace file contract. Keep the bundled `hyperframes` skill focused on the composition, timing, and editor contract. Authoring tools are selected separately; do not bundle framework dependencies or rendering implementations. Verify file requirements against the service before changing the contract.
