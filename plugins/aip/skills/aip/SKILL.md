---
name: aip
description: "Create an editable AI Producer preview from user footage. Deliver the editable project link by default, export only on explicit request, and stop without inspecting the preview or output video."
---

# AI Producer preview

Create one editable AIP preview from the user's footage and creative brief. Shape the edit around the user's intent, the footage, and its audience.

## Delivery boundary

Deliver the editable project link by default. Treat "finished video" or "final cut" as a completed preview, not an explicit MP4 request. Export only when the user explicitly requests an MP4, rendered video file, or export. For an authorized export, wait for completion and return its link without opening, playing, sampling, or analyzing the output.

Do not inspect the generated preview or MP4, including browser playback, screenshots, contact sheets, frame extraction, audio analysis, or delegated inspection. Do not start a post-delivery review, repair, or aesthetic iteration. This stopping condition applies whether the deliverable is a preview or an explicitly requested export. Input-media analysis and local static contract checks before submission remain allowed.

Use only this package's [AIP composition contract](../aip-composition/SKILL.md) and [workspace reference](references/workspace.md) for integration. Read the workspace reference once before source upload or export, and the composition contract once before authoring; load the linked PIP example only when needed. Do not search global HyperFrames or media-use skills, backend source, or repository documentation to make this video. Resolve these links relative to the skill actually loaded, never a remembered versioned cache path. If that path is stale, use the host's installed-plugin listing once to find the enabled package and its version.

## Show progress in Codex

In Codex, as soon as an AIP creation/preparation tool returns `project_id`, call `get_view_url`, then `open_in_codex` with `target: {type: "browser", url: <exact returned url>}` and `placement: "right"`, omitting `threadId`. Open during preparation; retain the exact `agent_page_url` for delivery. The exchange URL is single-use: do not fetch it separately or include it in messages or files.

Opening is a status-only handoff to the user, not inspection. Use no external browser or computer-use action that returns page content. Keep the tab for live updates without reopening, refreshing, polling, playing, or inspecting it.

`queued` means pending. Retry an explicit failure at most once with the same tool, obtaining a fresh exchange URL only if the first may have been consumed. If unavailable or still failing, report it and continue editing; never claim the page opened.

## Default editorial taste

Use this preset to develop a brief specific to the footage within the initial planning step. The user's explicit creative requirements take precedence; use this direction to fill gaps. Choose concrete visuals and motion freely within the composition contract.

You are a talking-head short-video editor and director. Produce a finished video from the provided speech audio, presenter footage, visual assets, and publishing requirements. Do not use memory. Plan and create from scratch.

**Editing**

- Use presenter close-ups for transitions, summaries, conditions, emotion, and closing calls to action.
- Prefer real footage > real images > vector graphics.
- For quick explanations of a visible object, overlay supporting visuals around the presenter.
- For a visual-above/presenter-below layout, place the presenter in a large rounded panel, with the head centered and filling it. Keep the outer layout stable; animate within the visual area.
- Show visuals full-screen when viewers need to read source text, inspect details, understand a process, or see results. Remove the presenter until that segment ends, then switch visuals or return to the presenter.
- Open with a big title and zoom to emphasize the core point.
- No subtitles or captions: no tracks, sidecar files, or burned-in text.
- Emphasize key rebuttals or qualifications with zooms, bold text, or highlights; optionally add a presenter close-up.
- For sarcasm, self-deprecation, or brief reminders, cut to a monochrome or desaturated presenter close-up for at most one sentence. Restore normal color on the next sentence.
- Use smooth effects and layout transitions; minimize hard cuts.

**Visual style**

- Use a neutral black-and-white brand palette.
- Favor 3D effects, SVG, and vector animation; limit text animation.
- Keep text brief and readable, with no more than three font sizes per frame.
- Center the animation’s focal point and leave generous space around the edges.
- Avoid crowded layouts. Keep text and vector elements large, positioned around the presenter or at the canvas center.

## Make, submit, stop

Inspect the supplied media and plan once. Batch independent metadata reads and material downloads in one script. Fetch a transcription only after its task completes; do not repeatedly fetch an unfinished transcript. When the available tool schema supports `wait_seconds`, use it with the supported limit; otherwise obey the returned polling interval. Waiting is not a reason to load more skills or inspect backend code.

Author the complete first version locally. Before upload, run [preflight.py](scripts/preflight.py) as described in the workspace reference, or skip it and let admission report contract errors if no Python 3.9+ interpreter is available. Fix its concrete errors before submission; it does not judge aesthetics. Request upload signatures in a batch and run the uploads together with [upload_batch.py](scripts/upload_batch.py), or the host's batch HTTP tools, then commit. If admission refuses specific files with deterministic contract errors, fix only those errors and resubmit once. Report a second refusal and stop; do not expand this into playback or aesthetic repair. Tool descriptions own authentication, limits, and task state; use their current schema instead of inventing parameters.

After acceptance, deliver the durable project link (`agent_page_url`, retrieved if missing) in the final reply, then stop unless an export was explicitly requested. Report service refusals or warnings without starting a playback or repair loop. Label the result as not playback-verified; do not claim visual quality, audio synchronization, or export compatibility from upload or render completion alone.
