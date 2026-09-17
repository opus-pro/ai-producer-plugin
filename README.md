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

## MCP server update

The plugin remains `aip@ai-producer-plugins`. Its MCP server is `ai-producer`; existing installations update the same plugin through their client. No plugin or marketplace removal is needed. After a release containing this change is available, refresh and update the installed package:

```bash
# Codex
codex plugin marketplace upgrade ai-producer-plugins
codex plugin add aip@ai-producer-plugins
codex mcp login ai-producer

# Claude Code, for a user-scoped installation
claude plugin marketplace update ai-producer-plugins
claude plugin update aip@ai-producer-plugins --scope user
```

Use the existing installation scope for Claude Code. Restart or open a new task after updating, then use `/mcp` in Claude Code to authenticate `plugin:aip:ai-producer` if prompted. The production endpoint remains `https://producer.opus.pro/api/mcp`, and existing project URLs are unchanged. The new server name may require signing in again. Host clients control capitalization of tool activity labels.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and checks, and [SECURITY.md](SECURITY.md) for vulnerability reporting.

## License

[MIT](LICENSE), with [third-party notices](THIRD_PARTY_NOTICES.md).
