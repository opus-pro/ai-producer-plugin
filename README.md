# AI Producer Plugin

Edit talking-head videos in Codex or Claude Code with AI Producer: cut dead air, add captions and motion graphics, add music, and export a finished video.

**[Installation and usage documentation](https://producer.opus.pro/docs)**

This repository contains the AIP skill, [HyperFrames contract](plugins/aip/skills/hyperframes/SKILL.md), [workspace contract](plugins/aip/skills/aip/references/workspace.md), and MCP connection. Video processing runs on the hosted AIP service; service access and credits are separate from installing this plugin.

## Development

Requires Python 3.10 or newer for the offline checks.

```bash
python3 scripts/test.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for development, [SECURITY.md](SECURITY.md) for vulnerability reporting, and [third-party notices](THIRD_PARTY_NOTICES.md) for source and branding boundaries. Original plugin source is licensed under [MIT](LICENSE).
