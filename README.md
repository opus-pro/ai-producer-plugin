# AI Producer Plugin

Edit talking-head videos in Codex or Claude Code with AI Producer: create an editable preview with captions and motion graphics. Deliver the editable preview link by default and export only on explicit request. Stop without inspecting the generated preview or MP4, or starting automatic repair or aesthetic iteration.

**[Installation and usage documentation](https://producer.opus.pro/docs)**

This repository contains the AIP skill, [HyperFrames contract](plugins/aip/skills/aip-composition/SKILL.md), [workspace contract](plugins/aip/skills/aip/references/workspace.md), and MCP connection. Video processing runs on the hosted AIP service; service access and credits are separate from installing this plugin.

The bundled static-check and upload helpers use Python 3.10 or newer on the client host. Hosts without it can use their own static-check and batch HTTP tools.

## Development

Requires Python 3.10 or newer for the offline checks.

In a Codex or Claude Code task opened in this repository, say "set up the local plugin" or invoke `/aip-plugin-local` to use the [local development workflow](.agents/skills/aip-plugin-local/SKILL.md). It builds **AI Producer Local**, refreshes host installation, and guides controlled quality, duration, and client-cost comparisons. Local instructions use the selected source's MCP service; a local plugin does not start a local backend.

```bash
python3 scripts/test.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for development, [SECURITY.md](SECURITY.md) for vulnerability reporting, and [third-party notices](THIRD_PARTY_NOTICES.md) for source and branding boundaries. Original plugin source is licensed under [MIT](LICENSE); the HyperFrames-derived composition skill is licensed under [Apache-2.0](plugins/aip/licenses/Apache-2.0.txt).
