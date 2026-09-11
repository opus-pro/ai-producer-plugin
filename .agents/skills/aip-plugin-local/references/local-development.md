# Local development

Use Python 3.10+ and the selected host's installed CLI. Resolve paths from this skill and the caller's checkout; never reuse a teammate's absolute paths or a remembered versioned cache directory.

## Select the source

Inspect the current host listing and its AIP marketplace source. A generated local package has `local-build.json` at its marketplace root; that receipt identifies the editable source checkout. An older local setup may point directly at a worktree. Preserve either source on refresh unless the user requested a new baseline.

For a new experiment, fetch the public repository's `origin/main`, then create an owned `codex/` branch and worktree under `.codex/worktrees/`. If there is no checkout, clone `https://github.com/opus-pro/ai-producer-plugin.git` into the user's chosen workspace first. Leave an existing dirty checkout intact. Use a separate branch for development-tool changes and for video-skill experiments.

Run the source's `python3 scripts/test.py` with `PYTHONDONTWRITEBYTECODE=1`. Build outside `plugins/`, in verified ignored scratch:

```text
python3 <this-skill>/scripts/build_local.py build --source <editable-checkout> --output <ignored-local-marketplace>
```

The builder copies the runtime package and both marketplace formats, sets the local display name and SVG, replaces the local cachebuster, aligns both manifests and both MCP version headers, and writes file hashes and source provenance. It does not edit the source checkout, install plugins, or run media tasks. It refuses an unowned output directory or edits made directly to a prior generated package; move those edits into source before rebuilding.

The endpoint and OAuth resource stay aligned. For a deliberately selected alternate service, pass `--mcp-url <URL>` on build and subsequent refreshes. Use the deployment owner's endpoint; do not infer a localhost port or assume a staging URL. Login and backend startup remain host/service responsibilities.

## Install or refresh in Codex

Read `codex plugin list --json` and `codex plugin marketplace list --json`. Save only AIP's source/ref and enabled/install state to ignored scratch; do not copy auth files. The generated marketplace and installed selector both retain `ai-producer-plugins` / `aip`.

- If that marketplace already points at this generated root, run `codex plugin add aip@ai-producer-plugins` after rebuilding.
- To switch from another AIP source, first verify the new build. Ensure the old marketplace contains only AIP; do not remove a shared marketplace with unrelated plugins. Remove only the installed AIP selector and its marketplace registration, then add the generated root and install AIP. If switching fails, restore the saved source/ref and prior installed state through the CLI; report a failed recovery without editing global config by hand.
- If no AIP source exists, add the generated marketplace root, then install AIP. Do not uninstall anything else.

```text
codex plugin remove aip@ai-producer-plugins
codex plugin marketplace remove ai-producer-plugins
codex plugin marketplace add <ignored-local-marketplace>
codex plugin add aip@ai-producer-plugins
```

The four-command block is for an actual source switch, not every refresh. Do not run removals for entries that are absent. State that switching affects future tasks using this host profile; do not interrupt existing tasks. OAuth may already be usable when the endpoint is unchanged. If the host requests login, complete its normal login flow without extracting credentials.

Re-read the installed listing: require exactly one enabled AIP entry, the expected version, and the selected local source. Locate the cache from the host's installation result or plugin metadata, then run:

```text
python3 <this-skill>/scripts/build_local.py verify --bundle <ignored-local-marketplace> --cache <installed-plugin-root>
```

Confirm the display name is `AI Producer Local`, the icon points at the packaged SVG, and the runtime skills match the receipt. Only then report installed. Open a **new** video task in a neutral media workspace, select the local plugin, and use the user's chosen test prompt. Keep repository instructions and this development skill out of that generation context.

## Claude Code companion

Build the same package, but operate only on Claude when requested. Inspect `claude plugin list --json`, `claude plugin marketplace list --json`, and the active scope first. Validate the generated plugin and marketplace with `claude plugin validate`. Register the generated root with `claude plugin marketplace add <ignored-local-marketplace> --scope <scope>`, then `claude plugin install aip@ai-producer-plugins --scope <scope>`. For a refresh use `claude plugin update aip@ai-producer-plugins --scope <scope>` and restart the session. A source switch uses only AIP's uninstall/marketplace-remove commands in that same scope; check current CLI help before executing them. Do not remove declarations from all scopes or alter Codex as a side effect.

Verify the installed manifest version and file hashes with the same verifier. Claude may not display the Codex-specific display name or SVG; report what its interface actually supports, and do not claim an authenticated Claude test from a Codex test.

## Restore production

On request, switch AIP's marketplace source back to `https://github.com/opus-pro/ai-producer-plugin.git` at the requested ref (normally `main`), using the same saved-source recovery procedure. Reinstall, verify the official display name/source/endpoint, and start a new task. Retain experimental source worktrees and receipts unless the user requests cleanup. A public release version bump belongs in its own PR; local cachebusters never become release versions.
