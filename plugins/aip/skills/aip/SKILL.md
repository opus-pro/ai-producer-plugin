---
name: aip
description: "Create an editable AI Producer preview from user footage. Deliver the editable project link by default, export only on explicit request, and stop without inspecting the preview or output video."
---

# AI Producer preview

Create one editable AIP preview from the user's footage and creative brief. Let the brief determine the visual style, pacing, media choices, and composition; this skill supplies integration and delivery boundaries.

## Delivery boundary

Deliver the editable project link by default. Treat "finished video" or "final cut" as a completed preview, not an explicit MP4 request. Export only when the user explicitly requests an MP4, rendered video file, or export. For an authorized export, wait for completion and return its link without opening, playing, sampling, or analyzing the output.

Do not inspect the generated preview or MP4, including browser playback, screenshots, contact sheets, frame extraction, audio analysis, or delegated inspection. Do not start a post-delivery review, repair, or aesthetic iteration. This stopping condition applies whether the deliverable is a preview or an explicitly requested export. Input-media analysis and local static contract checks before submission remain allowed.

Use only this package's [AIP composition contract](../aip-composition/SKILL.md) and [workspace reference](references/workspace.md) for integration. Read them once before authoring; load the linked PIP example only when needed. Do not search global HyperFrames or media-use skills, backend source, or repository documentation to make this video. Resolve these links relative to the skill actually loaded, never a remembered versioned cache path. If that path is stale, use the host's installed-plugin listing once to find the enabled package and its version.

## Make, submit, stop

Inspect the supplied media and plan once. Batch independent metadata reads and material downloads in one script. Fetch a transcription only after its task completes; do not repeatedly fetch an unfinished transcript. When the available tool schema supports `wait_seconds`, use it with the supported limit; otherwise obey the returned polling interval. Waiting is not a reason to load more skills or inspect backend code.

Author the complete first version locally. Before upload, run [preflight.py](scripts/preflight.py) as described in the workspace reference. Fix its concrete errors before submission; it does not judge aesthetics. Request upload signatures in a batch and run the uploads together with [upload_batch.py](scripts/upload_batch.py), then commit once. Report a refused commit and stop rather than entering an automatic re-author/commit loop. Tool descriptions own authentication, limits, and task state; use their current schema instead of inventing parameters.

After acceptance, retrieve and deliver the project link, then stop unless an export was explicitly requested. Report service refusals or warnings without starting a playback or repair loop. Label the result as not playback-verified; do not claim visual quality, audio synchronization, or export compatibility from upload or render completion alone.
