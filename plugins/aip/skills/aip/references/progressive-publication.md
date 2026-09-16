# Progressive publication in Codex

Use this path for a fresh prepared project with no visual effects. Each completed effect is signed, uploaded, committed, and accepted before source for the next effect is authored. Call the AIP MCP tools already loaded in the current task. Never run `codex`, start an app server, create an ephemeral task, extract OAuth credentials, change host configuration, or approve a permission request for publication.

The local checkpoint helper performs no network or MCP call. It validates the fixed timeline, one-effect transition, references, file hashes, and accepted receipt. The current task remains the only MCP client and uses its normal plugin authentication. A commit still uses normal service admission capacity and rate limits.

## Initialize the checkpoint

Read the current workspace once with `list_workspace`. Require no staged files, keep its `digest`, and collect every confirmed remote path. Plan the full edit duration and write a complete base `index.html` with no visual hosts. Its root and continuous speaker/audio clips must cover the whole planned output. Keep source audio and video paired with the same `data-hf-id`, output starts and durations. Declare explicit IDs, source paths, `data-media-start`, `data-track-index`, and `data-volume`. The base may represent a deliberately shortened edit; intermediate effects cannot shorten it further.

Initialize task-local state outside `render-engine/` before writing the first effect. Pass the workspace digest as `--base-digest` and every listed path as a repeated `--remote-file`. The checkpoint contains semantic timeline state, accepted paths, hashes, and the latest digest. It contains no effect source, signed URL, OAuth credential, or tool response body. Never place it in the published workspace.

```sh
python3 "$AIP_SKILL/scripts/progressive_checkpoint.py" init \
  --workspace "$TASK_ROOT/render-engine" \
  --state "$TASK_ROOT/.aip-progress.json" \
  --project-id "$PROJECT_ID" \
  --duration "$PLANNED_DURATION" \
  --base-digest "$WORKSPACE_DIGEST" \
  --remote-file render-engine/public/source.mp4 \
  --remote-file render-engine/public/source.mp3
```

## Prepare and publish one effect

Write only the current effect and its newly needed dependencies, then update the cumulative index with exactly one additional host. Do not define a multi-effect authoring function, fill a list with future effect source, embed future HTML in Python or shell, or create later composition files before the current publication is accepted.

Run `prepare` with `index.html`, the new composition, and every new dependency. Add `--final` only for the last requested effect. The command checks the full planned duration, unchanged speaker/audio ranges and earlier effects, performs preflight on an immutable snapshot, closes the checkpoint against another prepare, and returns one JSON publication plan.

```sh
python3 "$AIP_SKILL/scripts/progressive_checkpoint.py" prepare \
  --workspace "$TASK_ROOT/render-engine" \
  --state "$TASK_ROOT/.aip-progress.json" \
  --file index.html \
  --file compositions/effect-1.html
```

Use the returned plan without changing its values:

1. For each entry in `sign_batches`, call `sign_workspace_upload` in the current task with its `project_id`, `authoring: true`, and that entry as `files`. Each frozen batch stays within the service's 50-file limit. Stop on any rejection.
2. Combine every returned upload target and upload from the workspace with [upload_batch.py](../scripts/upload_batch.py), or the host's batch HTTP tools. Stop if any upload fails.
3. Call `commit_workspace` with the plan's `project_id`, `base_digest`, `expected_files`, and `authoring`. Do not retry a stale or refused mutation.
4. Wait on the returned `task_id` with the task tool's held-wait arguments until `terminal=true`. Require `succeeded=true` and an outcome of `accepted` or `accepted_with_warnings`.
5. Run `accept` with that exact task ID, receipt digest, every accepted path, and each bounded warning code. Do not pass messages, signed URLs, or repair text.

```sh
python3 "$AIP_SKILL/scripts/progressive_checkpoint.py" accept \
  --workspace "$TASK_ROOT/render-engine" \
  --state "$TASK_ROOT/.aip-progress.json" \
  --task-id "$TASK_ID" \
  --digest "$ACCEPTED_DIGEST" \
  --accepted-file render-engine/index.html \
  --accepted-file render-engine/compositions/effect-1.html
```

Only after `accept` returns the new accepted effect count may the model begin a continuation that authors the next effect. Repeat the same sequence. The final plan sets `authoring` to `false`; intermediate plans set it to `true`. The final cumulative index must mount every requested effect. No additional `finish_project`, transcript read, status heartbeat, app-server call, or hidden Codex task is needed.

Root framing may change as effects arrive, but unfinished beats must retain a usable presenter view. Do not move the presenter aside for a visual that has not been mounted. Keep BGM and caption changes outside these per-effect steps unless their dependencies are included and the speaker timeline stays unchanged.

The helper holds a process lock for every state transition and saves state atomically. A concurrent command is refused. After `prepare`, any signing, upload, commit, task, receipt, process, or host failure leaves a closed checkpoint so the mutation is not replayed. An invalid duration, incomplete AV coverage, changed speaker timing, changed prior host, more than one new effect, future composition file, changed prepared file, unexpected accepted path, or malformed receipt is also refused. Preserve the last accepted project and report the failure; do not delete, rewrite, or automatically restart the sequence.

Publication now uses the current task's normal MCP tool continuations. For N effects it creates no extra Codex task or provider call, but the current model reads the bounded signing, commit, and held-task results for each effect. Measure actual client tokens when changing this flow. Other hosts and existing effect graphs use the ordinary complete-graph path until they provide a matching checkpoint contract.
