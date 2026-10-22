<p align="center">
  <a href="https://producer.opus.pro/plugin">
    <img src="plugins/aip/assets/icon.png" alt="AI Producer" width="80" height="80">
  </a>
</p>

<h1 align="center">AI Producer Plugin</h1>

<p align="center">The official OpusClip plugin for editing videos in Codex, Claude Code, Cursor and ChatGPT Work.</p>

<p align="center">
  <a href="https://producer.opus.pro/plugin"><strong>Get started</strong></a> &nbsp; | &nbsp;
  <a href="https://producer.opus.pro/docs">Documentation</a>
</p>

## Where it runs

AI Producer needs a computer behind the conversation: a shell to send your footage from and a place to write the edit before it is published. These hosts have one:

- Codex, in the CLI and in the Codex tab of the ChatGPT desktop app.
- Claude Code.
- Cursor Desktop Agent with local filesystem and terminal access.
- ChatGPT Work, on the web and in the desktop app.

A ChatGPT Chat conversation has no computer of its own, so a video attached there never reaches AI Producer, and the failure is reported as if the plugin or the video were at fault. Switch to Work with the tab at the top of ChatGPT, or open a Codex task, mention AI Producer, and attach the video again there.

## Cursor

Use Cursor Desktop on your computer. Web and Cloud Agents are outside this setup. The package includes native Cursor metadata and uses the same skills and MCP configuration as the other hosts.

Clone this repository at a revision containing `plugins/aip/.cursor-plugin/plugin.json`, then copy the complete plugin, including its dotfiles, to a new local plugin directory:

```bash
git clone https://github.com/opus-pro/ai-producer-plugin.git
cd ai-producer-plugin
mkdir -p "$HOME/.cursor/plugins/local"
test ! -e "$HOME/.cursor/plugins/local/aip" &&
  cp -R plugins/aip "$HOME/.cursor/plugins/local/aip"
```

If that directory already exists, inspect its ownership and use the update procedure below. Do not overwrite an unrelated installation. Cursor skips external directory symlinks, so copy the files. An installed marketplace plugin with the same name takes precedence over a local copy; select the intended installation before testing. Organization policy may also restrict local plugins. See [Cursor's local plugin instructions](https://cursor.com/docs/plugins#test-plugins-locally).

Run **Developer: Reload Window**, then open **Customize**. Confirm the five skills (`aip`, `aip-composition`, `aip-dynamic-caption`, `aip-framing`, and `aip-setup`) and the `ai-producer` MCP server appear. Under **Customize > MCPs**, choose **Authenticate** for that server and finish sign-in in your browser. Use the `aip` skill from Cursor's slash-command menu, or ask AI Producer to edit a local video. A free `get_pricing` call verifies the connection before an edit.

To update a copy you installed this way, update this checkout, move the previous `aip` directory to a backup location outside `~/.cursor/plugins/local/`, and copy the complete new `plugins/aip` directory into its place. Reload the window and start a fresh conversation. Local copies do not update automatically. To remove the plugin, move that same directory outside the local plugin directory and reload. Leave other plugins and MCP configuration untouched.

If authentication expires, return to **Customize > MCPs > ai-producer > Authenticate**. Finished edits open through a browser project link; copy a selection's reference and paste it back into the Cursor conversation for a follow-up edit.

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
