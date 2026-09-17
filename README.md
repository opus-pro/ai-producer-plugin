<p align="center">
  <a href="https://producer.opus.pro/plugin">
    <img src="plugins/aip/assets/icon.png" alt="AI Producer" width="80" height="80">
  </a>
</p>

<h1 align="center">AI Producer Plugin</h1>

<p align="center">The official OpusClip plugin for editing videos in Codex and Claude Code.</p>

<p align="center">
  <a href="https://producer.opus.pro/plugin"><strong>Get started</strong></a> &nbsp; | &nbsp;
  <a href="https://producer.opus.pro/docs">Documentation</a>
</p>

## Installation

The production marketplace is `ai-producer-plugin`, the plugin is `ai-producer`, and the MCP server is `ai-producer`. The complete plugin ID is `ai-producer@ai-producer-plugin`. The package lives at `plugins/aip/`; its directory and skill names are implementation paths, not installation identifiers.

Codex:

```bash
codex plugin marketplace add https://github.com/opus-pro/ai-producer-plugin.git --ref main
codex plugin add ai-producer@ai-producer-plugin
codex mcp login ai-producer
```

Claude Code:

```bash
claude plugin marketplace add https://github.com/opus-pro/ai-producer-plugin.git#main
claude plugin install ai-producer@ai-producer-plugin
```

Open a new task and select AI Producer. In Claude Code, use `/mcp` to authenticate the AI Producer server if prompted.

### Existing installations

The former production ID was `aip@ai-producer-plugins`, with MCP server `aip`. A marketplace refresh alone does not migrate an installed plugin to a new ID. Before changing an old installation, inspect `codex plugin marketplace list --json` and `codex plugin list --json`, or their `claude plugin` equivalents. Confirm the old marketplace source is this public repository; do not remove another distribution with a matching name.

Keep the old installation until the new one is installed and authenticated. Add the source with `main` as shown above, then verify that marketplace discovery reports `ai-producer-plugin`. If the host returns the cached `ai-producer-plugins` instead, retry the same source without a ref to refresh from the default branch:

```bash
# Codex
codex plugin marketplace add https://github.com/opus-pro/ai-producer-plugin.git

# Claude Code
claude plugin marketplace add https://github.com/opus-pro/ai-producer-plugin.git
```

If the singular marketplace still does not appear, stop and keep the old installation. Otherwise install `ai-producer@ai-producer-plugin` and authenticate it using the client-specific instructions above. Confirm the new ID is enabled in the plugin list. Only then remove the confirmed old production entries:

```bash
# Codex
codex plugin remove aip@ai-producer-plugins
codex plugin marketplace remove ai-producer-plugins

# Claude Code, for the default user installation scope
claude plugin uninstall aip@ai-producer-plugins --scope user
claude plugin marketplace remove ai-producer-plugins --scope user
```

Run the commands only for the client and old entries you use. For a Claude project or local installation, use that same scope instead of `user` for installation and removal. Leave other marketplaces and plugins alone. Installation and migration are host-managed; the plugin has no update hooks and does not edit client settings or credentials. The production endpoint remains `https://producer.opus.pro/api/mcp`. Start a new task afterward so it loads the new tool names. Existing projects remain at their current URLs.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and checks, and [SECURITY.md](SECURITY.md) for vulnerability reporting.

## License

[MIT](LICENSE), with [third-party notices](THIRD_PARTY_NOTICES.md).
