---
name: aip
description: "Create an editable AI Producer preview from user footage. In Codex, show progress in the in-app browser. Deliver the editable project link and export only on explicit request, without inspecting the preview or output video."
---

# AI Producer preview

Create one editable AIP preview from the user's footage and creative brief. Shape the edit around the user's intent, the footage, and its audience.

## Delivery boundary

Deliver the editable project link by default. Treat "finished video" or "final cut" as a completed preview, not an explicit MP4 request. Export only when the user explicitly requests an MP4, rendered video file, or export. For an authorized export, wait for completion and return its link without opening, playing, sampling, or analyzing the output.

Do not inspect the generated preview or MP4, including browser playback, screenshots, contact sheets, frame extraction, audio analysis, or delegated inspection. Do not start a post-delivery review, repair, or aesthetic iteration. This stopping condition applies whether the deliverable is a preview or an explicitly requested export. Input-media analysis and local static contract checks before submission remain allowed.

Opening the project page for the user as described below is required in Codex and is not playback inspection. Leave viewing and quality judgments to the user.

Use only this package's [AIP composition contract](../aip-composition/SKILL.md) and [workspace reference](references/workspace.md) for integration. Read them once before authoring; load the linked PIP example only when needed. Do not search global HyperFrames or media-use skills, backend source, or repository documentation to make this video. Resolve these links relative to the skill actually loaded, never a remembered versioned cache path. If that path is stale, use the host's installed-plugin listing once to find the enabled package and its version.

## Show progress in Codex

As soon as the AIP tool that creates or prepares the project returns `project_id`, call `get_view_url` and open its exact returned `url` in the current Codex task, while preparation is running. Follow that tool's current schema; do not wait for transcription, authoring, submission, or the final reply. The exchange URL authenticates this browser once; never fetch it with HTTP tools first or put it in messages or project files. Retain the returned durable `agent_page_url` for final delivery, preserving its origin and query parameters.

Use Codex's `open_in_codex` tool with `target: {type: "browser", url: <returned url>}` and `placement: "right"`; omit `threadId` to target the current task. This action must return only opening status, not page content. Do not substitute a computer-use browser action that returns a screenshot or DOM, an unspecified/default browser, an external browser, or an OS open command. A text link alone does not perform this step.

Use only the opening tool's acknowledgement to track this handoff. A queued open is pending, not a reason to open another tab. After an explicit failure, allow at most one recovery attempt with the same tool; obtain a fresh exchange URL only if the first may have been consumed. If the tool is unavailable or recovery fails, briefly report that limitation and continue the edit without claiming the page opened. Keep the project tab for live updates; do not reopen or refresh it after every stage, inspect its contents, or add browser polling. Successful submission does not require a second browser open.

## Default editorial taste

Use this preset to develop a brief specific to the footage within the initial planning step. The user's explicit creative requirements take precedence; use this direction to fill gaps. Choose concrete visuals and motion freely within the composition contract.

- Let the opening reveal what makes this footage worth watching. Pace around changes in thought, emotional turns, and the time an idea needs to land. Honor a requested runtime; otherwise trim repetition while preserving the argument, qualifications, and payoff rather than forcing a fixed length.
- Presenter presence carries emotion, conviction, qualifications, and personal connection. Give supporting visuals space according to what viewers need to inspect: a nearby object can clarify a brief reference; a shared frame can sustain an explanation; a full-screen view can make source text, detail, or a process legible. Return attention to the presenter when their delivery becomes the point.
- Real footage and images lend specificity and credibility to tangible subjects. Diagrams, vector animation, and 3D can reveal relationships, mechanisms, or transformations that footage cannot readily show. Choose the medium for the understanding it adds beyond a text paraphrase of the narration.
- Build a clear visual hierarchy with short labels, generous scale, and negative space. Within one continuing explanation, a stable outer composition lets viewers follow changes within it; let a new idea determine its own framing and visual treatment. When captions are used, integrate them into that hierarchy, giving speech and explanatory visuals room to be read.
- Let emphasis express the meaning of a beat. A closer frame or stronger typographic contrast can sharpen a rebuttal; a brief monochrome treatment can give an aside a distinct tone when it fits the speaker's humor. The intensity and duration should follow the performance.
- Motion can convey weight, texture, causality, and energy. Match it to the visual action and the spoken rhythm. Choose transitions for continuity or punctuation according to the change in thought. When sound is part of the user's brief and supported by the available tools, use it to reinforce those same actions and rhythms; this preset does not require adding sound.

## Make, submit, stop

Inspect the supplied media and plan once. Batch independent metadata reads and material downloads in one script. Fetch a transcription only after its task completes; do not repeatedly fetch an unfinished transcript. When the available tool schema supports `wait_seconds`, use it with the supported limit; otherwise obey the returned polling interval. Waiting is not a reason to load more skills or inspect backend code.

Author the complete first version locally. Before upload, run [preflight.py](scripts/preflight.py) as described in the workspace reference, or equivalent local static checks if Python 3.10+ is unavailable. Fix its concrete errors before submission; it does not judge aesthetics. Request upload signatures in a batch and run the uploads together with [upload_batch.py](scripts/upload_batch.py), or the host's batch HTTP tools, then commit. If admission refuses specific files with deterministic contract errors, fix only those errors and resubmit once. Report a second refusal and stop; do not expand this into playback or aesthetic repair. Tool descriptions own authentication, limits, and task state; use their current schema instead of inventing parameters.

After acceptance, deliver the durable project link retained above (or retrieve it if missing), then stop unless an export was explicitly requested. Include this link in the final reply even when the project is already open in Codex. Never deliver the single-use exchange URL. Report service refusals or warnings without starting a playback or repair loop. Label the result as not playback-verified; do not claim visual quality, audio synchronization, or export compatibility from upload or render completion alone.
