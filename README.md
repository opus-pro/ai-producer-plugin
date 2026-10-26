<p align="center">
  <a href="https://producer.opus.pro/plugin">
    <img src="plugins/aip/assets/icon.png" alt="AI Producer" width="80" height="80">
  </a>
</p>

<h1 align="center">AI Producer Plugin</h1>

<p align="center">The official OpusClip plugin for editing videos in ChatGPT, Codex, Claude Code, Claude Cowork, Cursor, and other AI agents.</p>

<p align="center">
  <a href="https://producer.opus.pro/plugin"><strong>Get started</strong></a> &nbsp; | &nbsp;
  <a href="https://producer.opus.pro/docs">Documentation</a>
</p>

## Where it runs

AI Producer needs a computer behind the conversation: a shell to upload your footage from, and a workspace to write the edit in before it is published. Any host with local file and terminal access can run it.

## Skills

The video editing skills live in [`plugins/aip/skills/`](plugins/aip/skills/). If you have access to MCP, please always read related skills to achieve better video editing results.

- [`aip`](plugins/aip/skills/aip/SKILL.md): the basic usage of MCP and the whole editing flow.
- [`aip-composition`](plugins/aip/skills/aip-composition/SKILL.md): the HTML workspace and editor contract an edit is written in.
- [`aip-reference-style`](plugins/aip/skills/aip-reference-style/SKILL.md): copy the captions, motion graphics, and transitions of a reference video.

## Updating

The plugin is `aip` from the `ai-producer-plugins` marketplace, and its MCP server is `ai-producer`. Codex and Claude Code update the installed plugin in place, so you do not need to remove the plugin or the marketplace. Cursor runs a local copy of the plugin, which the same commands install and update.

```bash
# Codex
codex plugin marketplace upgrade ai-producer-plugins
codex plugin add aip@ai-producer-plugins
codex mcp login ai-producer

# Claude Code (match --scope to your existing installation)
claude plugin marketplace update ai-producer-plugins
claude plugin update aip@ai-producer-plugins --scope user
# then run /mcp and authenticate plugin:aip:ai-producer

# Cursor (to update, run git pull in the checkout instead of git clone)
git clone https://github.com/opus-pro/ai-producer-plugin.git
mkdir -p ~/.cursor/plugins/local
rsync -a --delete ai-producer-plugin/plugins/aip/ ~/.cursor/plugins/local/aip/
# then run Developer: Reload Window and authenticate ai-producer under Customize > MCPs
```

Restart your client or open a new task after updating; you may need to sign in again. The production endpoint stays at `https://producer.opus.pro/api/mcp`, and existing project links do not change.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and checks, and [SECURITY.md](SECURITY.md) for vulnerability reporting.

## License

[MIT](LICENSE), with [third-party notices](THIRD_PARTY_NOTICES.md).
