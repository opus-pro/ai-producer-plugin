# Publication

How a finished workspace reaches AI Producer from this computer. What the workspace holds is the [workspace format](workspace.md)'s; the hand-back that follows is the [AI Producer skill](../SKILL.md#delivery-boundary)'s.

## Which path

Every host, Codex, Claude Code and Cursor alike, publishes the complete graph: author every effect the plan calls for, run preflight once on the finished workspace, and commit it with the current `base_digest` in one commit. Then wait for that commit's accepted receipt before delivering. An edit with captions publishes them after that commit, as the [dynamic caption skill](../../aip-dynamic-caption/SKILL.md) says, and its last caption commit is the one that closes authoring; a caption-free edit closes authoring on its one commit. Do not launch another Codex CLI, app server, task, or model subtask to publish.

## Publishing

The bundled helpers require Python 3.9 or newer on the client host, invoked as `python3`, or as `py -3` on Windows. Without an interpreter, upload with the host's batch HTTP tools and skip the local check: submit and let admission report contract errors, rather than installing a runtime as part of the video task. The one exception is what the reference style skill sets up to read a reference, ffmpeg, python3 and uv, on a host that lets you install.

### Preflight

Run `python3 <loaded-aip-skill>/scripts/preflight.py <render-engine-root>` before each real publication. Use repeated `--remote-file` arguments only for paths confirmed present in `list_workspace` but absent locally, such as `public/source.mp4`, `public/source.mp3`, or `public/vendor/gsap.min.js`, or staged by a service build and named in its result's `files`. A copy of `public/vendor/gsap.min.js` [fetched for a local check](environment.md#checks-on-this-computer) is declared the same way, because the service owns that file and a script is otherwise refused as `unpromotable_type`. `public/vendor/three.min.js` needs no declaration: the service writes it in the same commit that first names it. `public/vendor/speaker-effects.js` is the same, and preflight also checks each speaker zoom and filter host against the composition contract. A declared composition the host cannot read is reported as `composition_not_locally_inspectable` as a warning; undeclared, it is an error. Both helpers accept local root-relative paths and service paths beginning with `render-engine/`; they remove exactly one such prefix. This checks known local integration mistakes, not rendering or visual quality. Fix reported errors before uploading.

A changed speaker cut runs preflight with `--sync-editing-script` and includes the synchronized `compositions/editing-script.json` in the same commit.

### Commit and upload

Commit with the current `base_digest`. Markup, stylesheets and JSON ride inline as `content` entries in `commit_workspace`, at most 256 KiB in one call, with no signing or upload. Each `content` is the file's bytes as written, read from disk in the same call that commits; never retype or re-emit a document from memory, because the service hashes what it is handed. Only bytes a commit cannot carry, an image, a font, a video, an audio file, or a batch past the inline budget, take the signed upload: for those, construct a temporary JSON array of objects with `path` (the service path or a path relative to the local render-engine root), `upload_url`, and `headers` from the signed-upload response. Feed it on stdin to `python3 <loaded-aip-skill>/scripts/upload_batch.py <render-engine-root>`, or use the host's batch HTTP tools. The helper runs bounded parallel PUTs through the host's HTTPS proxy when one is configured, and prints only relative paths and outcomes. Do not print signed URLs or persist them in project documentation. It does not sign, commit, retry failed uploads, call an LLM, or authenticate to MCP; if any upload fails, do not commit the incomplete batch.

## When a step fails

Every commit remains all-or-nothing, so a failed step never undoes accepted effects. A failed check, upload, or commit is not a reason to end the edit: fix what preflight or the refusal names and continue from the last accepted effect without restarting the sequence, at most twice for the same step. Stop and report the last accepted effect count only when the fix lies outside the edit (authentication, credits) or the workspace digest is no longer the last one you committed (another writer, or a commit whose outcome is unknown), without replaying a mutation or adopting another writer's digest. Tool descriptions own authentication, limits, and task state.
