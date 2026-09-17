---
name: aip
description: "Create an editable AI Producer preview from user footage. Deliver the editable project link by default, export only on explicit request, and stop without inspecting the preview or output video."
---

# AI Producer preview

Create one editable AI Producer preview from the user's footage and creative brief. Shape the edit around the user's intent, the footage, and its audience.

## Rough cut

For rough-cut-only or targeted speech-cleanup requests, follow the user's requested scope and duration while preserving the speaker's intended meaning. Skip visual research and default visual treatments unless they are also requested.

When revising the rough cut of an existing project, start from its current saved state. Preserve choices outside the requested rough-cut change, and update affected captions, visuals, and audio timing to follow the revised cut.

When the request includes both rough cut and fine cut, settle the content cut before finalizing timed treatments, then complete both. Pause for rough-cut review only when the user asks for it.

## Source supporting visuals

For footage-only or brief requests, apply the default editorial taste and research supporting material in the initial plan. Identify transcript beats that need real products, interfaces, devices, places, or event imagery. Use suitable supplied assets first; respect requests to avoid external sources.

- For missing material, search the Web and open official or primary source pages to find images or clips. An empty `find_broll` result requires this lookup before falling back to diagrams. Use one batch of up to three targeted queries, plus at most one such follow-up batch for unresolved material.
- Batch page reads and downloads. Before authoring, inspect a downsized image sheet or representative source frames for subject match, usable detail, and crop suitability. Replace unsuitable candidates within the research limit.
- Use accepted assets in relevant beats with framing or motion that explains the speech. Unless the user names a trigger or a count, use each supplied asset once, at the single beat it fits best; a stated trigger such as "whenever X is mentioned" applies at every matching beat. Record source URLs locally and label illustrative material where it could be mistaken for the speaker's demonstration. If lookup is unavailable or the limit yields no usable material, use a meaningful diagram and disclose the gap at delivery.

## Delivery boundary

Deliver the editable project link by default. Treat "finished video" or "final cut" as a completed preview, not an explicit MP4 request. Export only when the user explicitly requests an MP4, rendered video file, or export. For an authorized export, wait for completion and return its link without opening, playing, sampling, or analyzing the output.

Do not inspect the generated preview or MP4, including browser playback, screenshots, contact sheets, frame extraction, audio analysis, or delegated inspection. Do not start a post-delivery review, repair, or aesthetic iteration. This stopping condition applies whether the deliverable is a preview or an explicitly requested export. Input-media analysis, including retrieved source assets, and local static contract checks before submission remain allowed.

Use only this package's [AI Producer composition contract](../aip-composition/SKILL.md) and [workspace reference](references/workspace.md) for integration. Read the workspace reference once before source upload or export, the composition contract once before authoring, and the [framing skill](../aip-framing/SKILL.md) once before deciding the speaker's frame for each beat; load the linked PIP example only when needed, and the [captions skill](../aip-captions/SKILL.md) only when the brief asks for captions. Do not search global HyperFrames or media-use skills, backend source, or repository documentation to make this video. Resolve these links relative to the skill actually loaded, never a remembered versioned cache path. If that path is stale, use the host's installed-plugin listing once to find the enabled package and its version.

## Talk to the user

Treat every commentary, confirmation, progress update, warning, refusal, and final reply as user-facing product copy. Match the user's language. Lead with the user's current state: what is ready, what is still happening, and what they need to do next. Keep routine progress concise.

Do not narrate implementation policy or expose skill names, tool names, IDs, tasks, digests, graphs, checkpoints, commits, upload signing, provider or runtime checks, internal files, or status codes. Keep those details inside tool calls and local logs. Translate a necessary limitation into its effect on the user's project and the next available step.

Plain language must remain accurate. Say that a project is ready only after the corresponding operation succeeds. For a refusal or failure, explain what could not be completed, how it affects the project, and what can happen next. Do not repeat a non-actionable internal warning unless it materially changes what the user should expect.

## Show progress in Codex

In Codex, as soon as an AI Producer creation/preparation tool returns `project_id`, call `get_view_url`, then `open_in_codex` with `target: {type: "browser", url: <exact returned url>}` and `placement: "right"`, omitting `threadId`. Open during preparation; retain the exact `agent_page_url` for reopening in that browser, and `page_url` for the hand-back. The exchange URL is single-use: do not fetch it separately or include it in messages or files.

Opening is a status-only handoff to the user, not inspection. Use no external browser or computer-use action that returns page content. Keep the tab for live updates without reopening, refreshing, polling, playing, or inspecting it.

`queued` means pending. Retry an explicit failure at most once with the same tool, obtaining a fresh exchange URL only if the first may have been consumed. If unavailable or still failing, report it and continue editing; never claim the page opened.

## Default editorial taste

Plan each new talking-head edit from its supplied media and publishing brief. User instructions override matching defaults; keep the rest. Preserve established choices in follow-up edits unless the user requests changes.

### Editing

- Honor the requested runtime; preserve the speaker's argument, qualifications, and payoff.
- Match the canvas to a named platform: 1080x1920 for Instagram Reels, TikTok, and YouTube Shorts; 1080x1080 for square feed posts; otherwise keep the source aspect ratio. Reframe the presenter panel to fill the new canvas instead of letterboxing the source.
- Open with a large title and zoom to emphasize the core point.
- Use presenter close-ups for transitions, summaries, conditions, emotion, and closing calls to action. Emphasize rebuttals and qualifications with zooms or visual highlights.
- For concrete subjects, prefer relevant real footage, then images, then vectors. Overlay quick object explanations around the presenter.
- Reserve text overlays on the presenter for the opening hook; elsewhere, use only short labels within explanatory visuals. Use transcription for planning and timing.
- For sarcasm, self-deprecation, or brief reminders, use a monochrome or desaturated presenter close-up for at most one sentence, then restore color.
- Use smooth effects and layout transitions; minimize hard cuts.

### Visual style

- Use Apple keynote-style graphics; preserve source-media colors unless a specific treatment is intended.
- Explain abstract relationships, mechanisms, and processes with 3D, SVG, or vector animation; limit text animation.
- Use large, readable text, only essential words, and at most three font sizes per frame. Shorten copy to keep type large.
- Center the focal point within each visual area. Keep all text and graphics at least 10% from its edges throughout the animation; simplify content to keep them large.
- For text-heavy source visuals, prioritize readability over the default split layout. Crop and enlarge the relevant detail, or use full-screen visuals. Omit extra headings, duplicate labels, and nested frames; retain necessary illustrative-source labeling.

## Make, submit, stop

Inspect the supplied media and plan once. When the user ties a visual to an on-screen cue such as a gesture, a prop, or an action, locate that moment from representative source frames as well as the transcript; this is input-media analysis, not output inspection. Batch independent metadata reads and material downloads in one script. Fetch a transcription only after its task completes; do not repeatedly fetch an unfinished transcript. When the available tool schema supports `wait_seconds`, use it with the supported limit; otherwise obey the returned polling interval. Waiting is not a reason to load more skills or inspect backend code.

Plan the whole edit locally. When the current schema exposes `authoring`, set it to `true` on a new project's creation/preparation request or an existing project's first `sign_workspace_upload` request. Set it to `true` on any intermediate commit and `false` on the final commit, so the service can retain and then close external-authoring status. This uses existing calls only; never add a provider call, model subtask, heartbeat, or polling round for status. Omit the field when the schema lacks it.

For a fresh project in Codex, use the [progressive checkpoint flow](references/progressive-publication.md). Plan the complete edit once. Publish the first effect as soon as it is ready. Then author the remaining effects in batches of up to two while the preceding batch publishes. Keep drafts isolated and let the helper publish each effect in order using the AI Producer MCP tools already loaded in the current task. Preserve the planned effects, timing, and transitions; batching controls scheduling only. Keep unfinished beats full-length with normal presenter framing, and publish without intentional delays. Do not launch another Codex CLI, app server, task, or model subtask. The last effect closes authoring status.

Run the batch helper in the execution that writes its drafts. It handles signing, uploading, committing, held waiting, and receipt acceptance without separate model coordination or receipt-collection turns. The final receipt includes earlier warnings. If the host cannot keep an execution alive while authoring continues, await each batch without claiming overlap. Other hosts, existing effect graphs, and zero-effect edits use ordinary complete-graph publication. Measure actual tokens and duration; overlapping work is not a cost or quality guarantee.

The progressive helper runs the local contract and timeline checks, freezes the hashes the current task supplies to `commit_workspace`, and advances only from that commit's accepted receipt. Use the plan it returns once; do not recompute its digest or expected files in the host. For ordinary publication, run [preflight.py](scripts/preflight.py) as described in the workspace reference, or skip it and let admission report contract errors if no Python 3.9+ interpreter is available; batch signatures and uploads with [upload_batch.py](scripts/upload_batch.py) or the host's batch HTTP tools, then commit with the current `base_digest`. Every commit remains all-or-nothing. A signing, upload, commit, task, or receipt failure leaves the current checkpoint closed without automatically retrying a mutation or adopting another writer's digest. Report it with the last successful effect count; do not restart the full sequence. Tool descriptions own authentication, limits, and task state.

After the final requested graph is accepted, deliver the durable project link (`page_url`, retrieved if missing) in the final reply, then stop unless an export was explicitly requested. Translate refusals and material warnings under the user-facing language contract; do not repeat internal codes or mechanisms. Do not claim visual quality, audio synchronization, or export compatibility. Close by handing final confirmation to the user: state what was applied, then ask them to confirm the result on the project page, already open beside the conversation in Codex, otherwise at the link in this reply. Word this as a completed delivery waiting on the user's review.
