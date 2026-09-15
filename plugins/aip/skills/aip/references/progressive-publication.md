# Progressive publication in Codex

Use this path for a fresh prepared project with no visual effects. Each completed effect ends one host execution by publishing and waiting for acceptance. Control returns to the model only after that effect is visible, so the next effect's codegen happens after the prior publication. The helper never starts a model turn, calls a media provider, extracts OAuth credentials, changes host configuration or approves a permission request. Do not add a separate host call just to publish or deliberately delay publication to simulate work. A commit still uses normal server hydration, admission capacity and rate limits.

The native transport requires a Codex CLI exposing `mcpServer/tool/call` on its app-server protocol. It uses `codex` from PATH by default; pass `--codex-cli` only for a known installed Codex executable when the host supplies its path. It fails closed if unavailable or if approval or input is requested. Do not install a runtime, disable permission checks, change authentication or fall back to a different MCP server. The `--server` value is the exact server name of the loaded plugin, not an endpoint URL.

## Create the checkpoint

Load the checkpoint helper from this skill's own `scripts/` directory. Read the current project workspace once as usual. Plan the full edit duration and write a complete base `index.html` with no visual hosts. Its root and continuous speaker/audio clips must cover the whole planned output. Keep source audio and video paired with the same `data-hf-id`, output starts and durations. Declare explicit IDs, source paths, `data-media-start`, `data-track-index` and `data-volume`. The base may represent a deliberately shortened edit; intermediate effects cannot shorten it further.

Initialize a task-local checkpoint outside `render-engine/` before writing the first effect. The checkpoint contains semantic timeline state, accepted paths and the workspace digest. It contains no effect source, signed URL or credential. Never place it in the published workspace.

```sh
python3 "$AIP_SKILL/scripts/progressive_checkpoint.py" init \
  --workspace "$TASK_ROOT/render-engine" \
  --state "$TASK_ROOT/.aip-progress.json" \
  --project-id "$PROJECT_ID" \
  --duration "$PLANNED_DURATION"
```

## Author one effect, then publish it

In the same host shell call, write only the current effect and its newly needed dependencies, update the cumulative index with exactly one additional host, and finish the command with `publish`. Include `index.html`, the new composition and every newly referenced dependency in `--file`. Paths are relative to `render-engine/` or begin with that service prefix. Already accepted dependencies need not be uploaded again.

```sh
# Earlier commands in this host call write effect-1 and mount it in index.html.
python3 "$AIP_SKILL/scripts/progressive_checkpoint.py" publish \
  --workspace "$TASK_ROOT/render-engine" \
  --state "$TASK_ROOT/.aip-progress.json" \
  --server "$AIP_MCP_SERVER" \
  --file index.html \
  --file compositions/effect-1.html
```

Wait for this shell call to return an accepted effect count. Only then begin a new model continuation and host call for effect 2. Repeat the same sequence, adding `--final` to the last effect. The first host call may initialize the checkpoint, write effect 1 and publish it in sequence. Do not define a multi-effect authoring function, fill a list with future effect source, embed future HTML in Python or shell, or create later composition files before the current publication returns. The helper also refuses unaccepted composition HTML left ahead in the workspace.

The helper snapshots the named batch, checks references against that immutable snapshot and confirmed remote files, and uses the accepted receipt digest for the next checkpoint. Each return exposes only the accepted effect count, fixed planned duration, task ID, final flag and bounded warning codes. Intermediate commits retain authoring state; `--final` closes it. The final cumulative index must mount every requested effect. No additional `finish_project`, publication, transcript read or status heartbeat is needed.

Root framing may change as effects arrive, but unfinished beats must retain a usable presenter view. Do not move the presenter aside for a visual that has not been mounted. Keep BGM and caption changes outside these per-effect steps unless their dependencies are included and the speaker timeline stays unchanged.

The helper holds a process lock across each read, mutation and state write, and atomically marks the checkpoint as publishing before the mutation. It saves the next resumable state only after the service accepts the commit. A concurrent command is refused. A process interruption in between leaves a closed checkpoint instead of risking a duplicate mutation. An invalid duration, incomplete AV coverage, changed speaker timing, changed prior host, more than one new effect, future composition file, upload failure, task failure, stale digest, permission request or unaccepted receipt also closes the checkpoint. Preserve the last accepted project and report the failure; do not delete, rewrite or automatically restart the sequence.

The helper's zero-model-turn property covers publication control. Creative authoring intentionally resumes once per accepted effect. For N effects this creates at most N-1 extra model continuations, while cached context limits the incremental model cost. Measure the actual host session when changing the flow. Other hosts and existing effect graphs use the ordinary complete-graph path until they provide a matching continuation and transport contract.
