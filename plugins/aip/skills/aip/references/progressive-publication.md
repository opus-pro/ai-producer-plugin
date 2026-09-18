# Progressive publication in Codex

Use this path for a fresh prepared project with no visual effects. Plan once, generate the first effect alone, then generate up to two effects per continuation. Publish each effect in order while drafting the next batch. Call the AI Producer MCP tools already loaded in the current task. Never run `codex`, start an app server, create an ephemeral task, extract OAuth credentials, or change host configuration for publication.

## Initialize once

Read `list_workspace` once: require no staged files, retain its digest and confirmed remote paths. In the same initialization execution, fetch `render-engine/compositions/editing-script.json` with `get_workspace_file` and save its complete content locally without printing its word data. Keep the fetched document's source and tracks; do not invent a replacement. Write a base `index.html` with the full planned duration, no visual hosts, and continuous paired speaker/audio clips. Each pair uses the same `data-hf-id`, output starts and durations, with explicit IDs, sources, `data-media-start`, `data-track-index`, and `data-volume`. A deliberate rough cut can shorten the source; progressive effects cannot shorten that planned output.

Keep the checkpoint and drafts outside `render-engine/`. Initialize before authoring the first effect:

```sh
python3 "$AIP_SKILL/scripts/progressive_checkpoint.py" init \
  --workspace "$TASK_ROOT/render-engine" --state "$TASK_ROOT/.aip-progress.json" \
  --project-id "$PROJECT_ID" --duration "$PLANNED_DURATION" \
  --base-digest "$WORKSPACE_DIGEST" \
  --remote-file render-engine/public/source.mp4 \
  --remote-file render-engine/public/source.mp3
```

Pass every listed path as a repeated `--remote-file`. Initialization synchronizes the fetched EditingScript's AV clips and caption times to the base speaker cut. The helper includes that document in the first effect's upload automatically and validates it locally thereafter; no separate commit or model check is needed. In a completed initialization execution, load [publication_batch.js](../scripts/publication_batch.js) into host memory without printing its implementation; retain its source and these local paths for later executions. Keep only serializable initialization data in host memory; live publication state crosses executions through the atomic checkpoint file.

## Author a batch

Give each effect its own isolated draft directory, such as `$TASK_ROOT/drafts/2/` and `$TASK_ROOT/drafts/3/`. Each contains its cumulative `index.html`, exactly one new composition, and new dependencies at paths relative to the render-engine root. Its index preserves every earlier host and mounts only this additional effect. Derive it from the preceding draft or planned cumulative graph, not a publication workspace that another execution is updating. The two drafts may be authored together; do not place future composition files in the live publication workspace.

Generate one effect in the first batch and up to two thereafter. A final singleton is valid. Preserve the planned visual scope rather than adding, dropping, or splitting effects to fit batches. Keep full speaker/audio coverage and normal presenter framing at unfinished beats; add framing transitions only for mounted effects. Captions are not a batch step; add them after the last batch as the section below describes. Keep music changes outside these steps unless their dependencies are included and the speaker timeline stays unchanged.

## Publish and continue

During the existing initialization execution, read the loaded AI Producer tool metadata and retain the advertised JavaScript callable names for `sign_workspace_upload`, `commit_workspace`, and `wait_task` as `publicationToolNames.signUpload`, `.commitWorkspace`, and `.waitTask`. Use those exact names; do not derive namespaces from plugin or server IDs. Append this helper call to the execution that writes the draft files:

```javascript
const runBatch = eval(source)({
  tools, yieldControl: yield_control, onReady: text,
  skill: aipSkillPath, workspace: renderEnginePath, state: checkpointPath,
  signUpload: tools[publicationToolNames.signUpload],
  commitWorkspace: tools[publicationToolNames.commitWorkspace],
  waitTask: tools[publicationToolNames.waitTask],
});
text(await runBatch({
  afterEffect: 1,
  steps: [
    { draft: draft2Path, files: ["index.html", "compositions/effect-2.html"] },
    { draft: draft3Path, files: ["index.html", "compositions/effect-3.html"] },
  ],
  final: false,
}));
```

Use `afterEffect: 0` and one step for the first batch; the helper omits the previous-effect join automatically. Later batches name the preceding batch's final effect count, including while it is still publishing. Include every new dependency in its step's `files`; set `final: true` only on the batch containing the last planned effect. A single-effect project uses one final batch.

The helper prepares and publishes each step automatically: wait for the preceding accepted checkpoint, validate and install its isolated draft, sign the frozen files, upload, commit, and accept the exact task's successful terminal receipt. Its held waits stop after ten minutes or forty replies. Only one signing/upload/commit sequence is in flight. The first step can join across both effects of the preceding batch; subsequent steps use its accepted digest directly. Only the last step of a final batch closes authoring. Tool descriptions own service limits and refusals; a batch does not bypass commit limits.

After its first draft is prepared, a nonfinal batch emits `batch_publishing` and yields once while keeping publication awaited, so the model can write the next batch. An automatic host timeout before that marker means the prior batch is still being joined; resume that execution before authoring another batch. Otherwise continue authoring immediately, without model turns to poll or collect already-accepted receipts from earlier cells. The next checkpoint joins publication locally, and the final batch awaits completion and returns cumulative warning codes for delivery. No live receipt from cross-execution memory is needed. Without live yielded executions, await each batch serially. Never detach a promise that the host would discard.

The checkpoint preserves duration, speaker/audio timing, earlier effects and file hashes, exact accepted paths, and the receipt digest. Draft validation failures leave the live workspace unchanged. Other failures stop later effects at the last confirmed local checkpoint. After a commit request, a timeout or lost receipt can leave its remote outcome unknown; do not claim rollback. Report the uncertainty without replaying mutations, adopting another writer's digest, or restarting automatically. Static checks preserve the composition contract, not visual quality. No extra task, heartbeat, transcript read, `finish_project`, export, or playback inspection is needed.

## Captions after the last batch

The caption layer is not a batch step: its build needs the committed root, and the service stages its files, so the helper cannot hash them. After the final batch's receipt is accepted, call the caption build (the [dynamic caption skill](../../aip-dynamic-caption/SKILL.md) owns the pick when it is listed; the [composition contract](../../aip-composition/SKILL.md) owns the host div), then publish it with one ordinary commit: mount the returned `host_div` in `index.html` as written, run preflight declaring the result's paths as `--remote-file` (a declared composition the host cannot read is reported as `composition_not_locally_inspectable` and is a warning), sign and upload `index.html`, and commit with `expected_files` naming `index.html` and the result's `files` entries exactly as returned, with `authoring: false`. The caption files stay staged until that commit; a commit that leaves them out reports them in `retained_staged`.
