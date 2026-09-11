---
name: aip-plugin-local
description: "Build, install, refresh, and debug AI Producer Local in Codex or Claude Code; prepare controlled video experiments and audit client token cost. Use for /aip-plugin-local or local plugin installation, updates, debugging, and cost comparisons. Ordinary video editing uses the installed aip skill."
---

# AI Producer Local

Turn a local checkout into an identifiable development plugin and keep experiments comparable. This repository skill is developer tooling; do not copy it into `plugins/aip/skills/` or load it in a video-generation task.

## Choose the requested action

| Request | Read and execute |
| --- | --- |
| Install, build, refresh, switch source, or restore production | [Local development](references/local-development.md) |
| Test a prompt/skill change or compare quality | [Experiments](references/experiments.md) |
| Inspect a finished/running task's cost or duration | [Cost accounting](references/cost-accounting.md) |

Resolve an omitted action from the current task. For a bare invocation, inspect the installed AIP source and report its state before choosing setup or refresh. Installation alone does not authorize video generation. Use existing media and experiment choices when supplied; ask only for missing inputs that block the requested test.

## Shared decisions

- Display the generated plugin as **AI Producer Local**, with the bundled [SVG icon](assets/local.svg). Retain plugin `aip`, marketplace `ai-producer-plugins`, and MCP server `aip`. Operate on the requested host only.
- "Local" means local plugin instructions. The MCP endpoint is inherited from the selected source and normally remains production. State the endpoint before a test; changing it requires an explicit endpoint choice. This skill does not launch a backend.
- Start a new experiment from fresh `origin/main` in an owned worktree. Resume an existing experiment at its recorded source; refreshing an installation does not mean rebasing or discarding edits. Record source commit, dirty-content hashes, installed version, and endpoint.
- Edit source files, build a generated local package, reinstall through the host CLI, and verify installed content. Source edits alone do not update the host cache. Use a new video task after every refresh.
- Keep evaluation separate from generation: preserve the runtime skill's preview delivery, in-app handoff, explicit-export policy, and no-inspection stopping rule. A requested quality review is a separate action after recording generation usage.
- Report client model tokens and API-equivalent cost separately from service charges and actual subscription billing. Distinguish task elapsed time, source duration, requested output duration, and delivered duration. Unknown measurements remain unknown.

Finish with the actual source/version/endpoint, checks performed, and the next runnable action. For installation, say which plugin to select in a new task. For experiments, report comparable results and confounders before recommending changes. Do not publish private run records or add version bumps to functional PRs.
