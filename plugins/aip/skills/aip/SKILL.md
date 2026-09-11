---
name: aip
description: "Create an editable AI Producer preview from user footage. Deliver the editable project link by default, export only on explicit request, and stop without inspecting the preview or output video."
---

# AI Producer preview

Create one editable AIP preview from the user's footage and creative brief. Shape the edit around the user's intent, the footage, and its audience.

## Source supporting visuals

For footage-only or brief requests, apply the default editorial taste and research supporting material in the initial plan. Identify transcript beats that need real products, interfaces, devices, places, or event imagery. Use suitable supplied assets first; respect requests to avoid external sources.

- For missing material, search the Web and open official or primary source pages to find images or clips. An empty `find_broll` result requires this lookup before falling back to diagrams. Use one batch of up to three targeted queries, plus at most one such follow-up batch for unresolved material.
- Batch page reads and downloads. Before authoring, inspect a downsized image sheet or representative source frames for subject match, usable detail, and crop suitability. Replace unsuitable candidates within the research limit.
- Use accepted assets in relevant beats with framing or motion that explains the speech. Record source URLs locally and label illustrative material where it could be mistaken for the speaker's demonstration. If lookup is unavailable or the limit yields no usable material, use a meaningful diagram and disclose the gap at delivery.

## Delivery boundary

Deliver the editable project link by default. Treat "finished video" or "final cut" as a completed preview, not an explicit MP4 request. Export only when the user explicitly requests an MP4, rendered video file, or export. For an authorized export, wait for completion and return its link without opening, playing, sampling, or analyzing the output.

Do not inspect the generated preview or MP4, including browser playback, screenshots, contact sheets, frame extraction, audio analysis, or delegated inspection. Do not start a post-delivery review, repair, or aesthetic iteration. This stopping condition applies whether the deliverable is a preview or an explicitly requested export. Input-media analysis, including retrieved source assets, and local static contract checks before submission remain allowed.

Use only this package's [AIP composition contract](../aip-composition/SKILL.md) and [workspace reference](references/workspace.md) for integration. Read the workspace reference once before source upload or export, and the composition contract once before authoring; load the linked PIP example only when needed. Do not search global HyperFrames or media-use skills, backend source, or repository documentation to make this video. Resolve these links relative to the skill actually loaded, never a remembered versioned cache path. If that path is stale, use the host's installed-plugin listing once to find the enabled package and its version.

## Show progress in Codex

In Codex, as soon as an AIP creation/preparation tool returns `project_id`, call `get_view_url`, then `open_in_codex` with `target: {type: "browser", url: <exact returned url>}` and `placement: "right"`, omitting `threadId`. Open during preparation; retain the exact `agent_page_url` for reopening in that browser, and `page_url` for the hand-back. The exchange URL is single-use: do not fetch it separately or include it in messages or files.

Opening is a status-only handoff to the user, not inspection. Use no external browser or computer-use action that returns page content. Keep the tab for live updates without reopening, refreshing, polling, playing, or inspecting it.

`queued` means pending. Retry an explicit failure at most once with the same tool, obtaining a fresh exchange URL only if the first may have been consumed. If unavailable or still failing, report it and continue editing; never claim the page opened.

## Default editorial taste

Plan each new talking-head edit from its supplied media and publishing brief. User instructions override matching defaults; keep the rest. Preserve established choices in follow-up edits unless the user requests changes.

### Editing

- Honor the requested runtime; preserve the speaker's argument, qualifications, and payoff.
- Open with a large title and zoom to emphasize the core point.
- Use presenter close-ups for transitions, summaries, conditions, emotion, and closing calls to action. Emphasize rebuttals and qualifications with zooms or visual highlights.
- For concrete subjects, prefer relevant real footage, then images, then vectors. Overlay quick object explanations around the presenter.
- Prefer visuals above/presenter below for examples, comparisons, and processes. Use a large rounded presenter panel with the head centered and filling it. Keep the outer layout stable; animate within the visual area.
- Use full-screen visuals when source text or visual detail needs the whole canvas. Then switch visuals or return to the presenter.
- Omit speech subtitles, caption tracks, caption sidecars, and burned-in captions. Reserve text overlays on the presenter for the opening hook; elsewhere, use only short labels within explanatory visuals. Use transcription for planning and timing.
- For sarcasm, self-deprecation, or brief reminders, use a monochrome or desaturated presenter close-up for at most one sentence, then restore color.
- Use smooth effects and layout transitions; minimize hard cuts.

### Visual style

- Use Apple keynote-style graphics; preserve source-media colors unless a specific treatment is intended.
- Explain abstract relationships, mechanisms, and processes with 3D, SVG, or vector animation; limit text animation.
- Use large, readable text, only essential words, and at most three font sizes per frame. Shorten copy to keep type large.
- Center the focal point within each visual area. Keep all text and graphics at least 10% from its edges throughout the animation; simplify content to keep them large.
- For text-heavy source visuals, prioritize readability over the default split layout. Crop and enlarge the relevant detail, or use full-screen visuals. Omit extra headings, duplicate labels, and nested frames; retain necessary illustrative-source labeling.

## Make, submit, stop

Inspect the supplied media and plan once. Batch independent metadata reads and material downloads in one script. Fetch a transcription only after its task completes; do not repeatedly fetch an unfinished transcript. When the available tool schema supports `wait_seconds`, use it with the supported limit; otherwise obey the returned polling interval. Waiting is not a reason to load more skills or inspect backend code.

Author the complete first version locally. Before upload, run [preflight.py](scripts/preflight.py) as described in the workspace reference, or skip it and let admission report contract errors if no Python 3.9+ interpreter is available. Fix its concrete errors before submission; it does not judge aesthetics. Request upload signatures in a batch and run the uploads together with [upload_batch.py](scripts/upload_batch.py), or the host's batch HTTP tools, then commit. If admission refuses specific files with deterministic contract errors, fix only those errors and resubmit once. Report a second refusal and stop; do not expand this into playback or aesthetic repair. Tool descriptions own authentication, limits, and task state; use their current schema instead of inventing parameters.

After acceptance, deliver the durable project link (`page_url`, retrieved if missing) in the final reply, then stop unless an export was explicitly requested. Report service refusals or warnings without starting a playback or repair loop. Label the result as not playback-verified; do not claim visual quality, audio synchronization, or export compatibility from upload or render completion alone.
