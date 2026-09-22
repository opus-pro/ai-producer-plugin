---
name: aip
description: "Create an editable AI Producer preview from user footage, or act on a pasted @aip reference line from the Motion library (a motion-asset or omni-preset card) by placing it at its time. Settle the rough cut, fine cut and finishes rounds first when the request leaves them open. Use whenever a user attaches, names, or links a video and wants it cut, captioned, given motion graphics or music, restyled, or exported, in any language (剪视频 / 剪辑 / 加字幕 / 做动效 / 配乐 / 导出成片), when they hand over extra images or clips to place in the video (素材 / 插入图片 / 插一段视频), and for any follow-up on an existing project. Deliver the editable project link by default, export only on explicit request, and stop without inspecting the preview or output video."
---

# AI Producer preview

Create one editable AI Producer preview from the user's footage and creative brief. Shape the edit around the user's intent, the footage, and its audience.

## What to settle before you cut

The rough cut, the fine cut and the finishes decide the edit. Settle all three before you start editing, then edit without coming back for more.

Preparing the project is not editing, and it waits for no answer. In the turn the footage arrives, start it before you ask anything: mint the upload target with `sign_upload`, PUT the bytes, then call `start_transcribe_project`. Only then read the saved default and put up the first round. Ingesting and transcribing the source is the long part of the run and no answer in the rounds changes what it does, so a card raised first buys nothing and charges the user the whole wait. The three rounds are asked while preparation runs, and because the project exists by the time an answer comes back, each one is written down where it is given. One thing holds preparation back, and only this: the user asking to talk the edit through before anything is spent. That is an instruction, so tell them what preparing costs, settle what they want to settle, and start preparation when they say to go ahead.

Preparation spends, so whatever you say when you start it carries its price: the message that raises the first round, or your first reply when their opening settles every round and no card goes up. The price is read from `get_pricing` and never quoted from memory, and it reaches the user in plain words, as what getting their video ready costs.

Ask only for what the user has not already told you. Read their opening message against the rounds below; a round whose answer follows from what they wrote is settled, and you do not put it to them. Ask the rounds that are still open, in the order they are listed, one at a time. Every round settled - from their words or from their answers - is the signal to start production. Nothing else gates the work: there is no mode to pick and no feature list to shop.

### Start from the saved default

At the start of every new project, before the first round, read `get_editing_preset`.

- It returns a preset: put those settings to the user in plain words and ask them to confirm or change anything, in cards built from the same components the rounds use, each picker carrying the stored value as its `selected`. A text component takes no prefill - a card renders its field empty whatever you send - so a stored `editing_preference` is quoted back in your own message and the empty field is where a change goes. A card holds at most six server components and a full preset is five, so one card carries the whole of it, in round order, and you ask for the confirmation once at the end rather than after each setting. Confirmed as it stands, you edit with it and ask nothing further, and you write the confirmed values down with `record_choices` under the same card ids an answer would have used, so the project's own record says the rounds are settled and no later turn asks them again. Changed, you edit with the changed values and then ask, in one question, whether that becomes their new default; yes is `save_editing_preset` with the full set of values you are about to edit with.
- It returns nothing: run the rounds.

Read it fresh on every project rather than remembering it between them. The user can change these settings away from the conversation, and this is the only place that change shows.


### The rounds

Each round is one card: call `present_choices` with that round's components, end your turn, and wait. Preparation is already under way by the first card, so `record_choices` has a project to write to and each answer lands as it arrives. A card needs no project behind it, so in the exceptional case where a round is raised before one exists - preparation refused, or the user answering a round you have not reached - the answer is carried and written down as soon as the project is created. When the user answers - on the card or in their own words - write it down with `record_choices` under that round's card id, then raise the next round - unless that round names something of its own that comes first. The latest recording for a card wins, so a user who changes their mind is recorded again, not argued with. `get_project` carries `choices`, what is answered, and `pending_choices`, what is not, in round order; a turn that picks up a conversation already in progress reads those two rather than guessing. A card's title and note are sentences the user reads, so they follow Talk to the user and name no card, component or tool.

| Round | Card id | Components | What you write down |
| --- | --- | --- | --- |
| Rough cut | `roughcut` | `rough_cut_boldness` | the value alone |
| Fine cut | `branding` | `editing_preference_example`, `editing_preference` | `<component id>=<value>`, one per answer they gave |
| Finishes | `finishing` | `caption_style`, `bgm_enabled`, `sfx_enabled` | the caption style's value alone, and the two toggles as `bgm_enabled=on`, `sfx_enabled=off` |

**Rough cut.** `off` means keep the original cut: no filler word, retake, false start or pause is removed. `off` is not a boldness and never travels on to anything that takes one. The other three - `conservative`, `balanced`, `aggressive` - say how far the clean-up goes. You make this cut yourself by writing the speaker clips, so its scope is yours to keep: every level removes only filler words, verbatim restarts, abandoned false starts, failed retakes, and dead-air pauses. A fluent, complete sentence is content at every level, even when it seems less important, repetitive, or off topic; dropping it is an editorial cut the user has not asked for, and a scripted read with no disfluencies is left whole. Without a requested duration or a named removal, the speaker clips cover the rest of the source in order. Cut to the settled value and to the user's requested scope and duration, preserving the speaker's intended meaning. For a rough-cut-only or targeted speech-cleanup request, skip visual research and default visual treatments unless they are also requested. When revising the rough cut of an existing project, start from its current saved state: preserve choices outside the requested rough-cut change, and update affected captions, visuals, and audio timing to follow the revised cut. When the request includes both rough cut and fine cut, settle the content cut before finalizing timed treatments, then complete both. Pause for rough-cut review only when the user asks for it.

**Fine cut.** This round asks how the user wants the footage edited: one worked example to start from, and their own words beside it. Both answers reach no tool. They are recorded, and applying them is yours - they are the direction you design the cut under. `editing_preference_example` offers `more-broll-image`, `more-motion-graphics` and `custom`; `custom` is the user saying the examples do not fit, so it carries nothing on its own and the words in `editing_preference` are the answer. `custom` with nothing typed is therefore not an answer: ask for their words before you record it, or the round reads as settled while holding no direction at all. An example on its own is a complete answer, and so is nothing at all - a user who wants neither is not blocked, so record what they did give and design the cut yourself.

The reference image is not on this card, because a card collects one line of text and an image is a file. So the card's note says nothing about a picture, and the ask is a message of its own. Look back over what the user has already sent. When they handed a picture over, put it into the project with `sign_workspace_upload` and write `reference_image=<path>` into the same `record_choices` call as the two answers, and ask them for nothing. When they sent none, record the two answers on their own, and then, before the finishes round goes up, ask them for the picture in plain words - your own sentence, not a card and not a line inside the note: whether they want to send a reference image to set the styling, and that answering "skip", or anything else, carries on without one. End the turn there and wait for the reply. An image comes back: upload it with `sign_workspace_upload` and record `branding` a second time - the two answers you already wrote down and `reference_image=<path>` beside them, because a recording replaces the whole entry for a card and an answer left out of the second call is gone - then raise the finishes round. "skip" or any other reply: raise the finishes round. Ask once for the whole project, and never a second time - not after a skip, and not when a turn picking the conversation back up finds `reference_image` already recorded under `branding` or the fine cut already behind it in `choices`. A user with no image to give is not blocked by the round.

**Finishes.** `caption_style` offers `no-caption` ("No captions") and eight caption patterns. Write the chosen token unprefixed, including `no-caption`, while the two toggles carry their component ids: `on` on its own identifies no question. A pattern goes to the caption skill without picking again. An omitted `caption_style` stays Auto: let the caption skill choose the pattern, rather than treating it as `no-caption`. Recording replaces the whole entry for a card, so write every finishing answer you hold each time you record one, or the ones you leave out are gone.

`no-caption` is a card answer, not a caption pattern: skip `build_captions` and omit the `narrator-captions` host from `render-engine/index.html`. For an existing captioned project, remove only that host, preserve transcript and editor artifacts, then upload the changed root and `commit_workspace`. Recording the answer alone does not change the edit. Store `no-caption` unchanged when the user saves it as their default.

`bgm_enabled=on` is the instruction to call `add_music` afterwards, and `off` is the instruction not to. `off` declines a new music run; it does not strip a bed already mixed into the cut, so do not offer to take music away with it. `on` is an answer, not a payload: it is not a value `add_music` takes, and that call's own inputs are stated where it states them. Music spends, and `get_pricing` is what says how much - never quote an amount from memory.

`sfx_enabled` reaches no tool, and it is not a switch you can throw. Sound effects arrive by two routes and no third: the step inside an `add_music` call given a `direction`, which plans them and bills them, and which a call supplying its own `sections` skips entirely; or sounds you place in the composition yourself. Recording an answer makes neither route happen. So say which one is actually going to happen for this cut, and never let `sfx_enabled=on` read as a promise the recording itself keeps, or `off` as a guarantee that a music run will land none.

### Keep it as the default

Once the last round is recorded, ask - in one question, not a card - whether to keep these answers as their default for the videos they make next. Yes is `save_editing_preset` with the values just settled: `rough_cut_boldness`, `caption_style`, `bgm_enabled`, `sfx_enabled`, and `editing_preference` if they gave one. The reference image is not stored: its path was signed for the project it was uploaded to and means nothing on the next one. The two toggles are stored in the same `on` / `off` spelling the card carries. No stores nothing, and the next project asks the rounds again. Ask once, either way: a user who declines is not asked again on this project.

Not every install has the cards. When `present_choices` is not among your tools, the rounds are still asked, in plain text: each still-open round as one question of its own, in the user's language, offering the same options by name and in the order the table above lists them, one round per turn. Each round's options are named where that round is explained above, with one exception: the eight caption styles are not, so read them from the [dynamic caption skill](../aip-dynamic-caption/SKILL.md) before you ask the finishes round - with no card, the server is not the one offering them, and a style you invent is not one the caption layer can be built with. Write nothing down - `record_choices` is absent with it, and so are the preset tools, so skip the saved-default read and skip the question about keeping the answers as a default - and carry the settled answers in the conversation instead. Everything else stands: preparation starts first and on the same terms, the reference image is still asked for as its own question, and a round the user's opening already settles is still not put to them.

## Source supporting visuals

Once the rounds are settled, apply the default editorial taste and research supporting material in the initial plan. Identify transcript beats that need real products, interfaces, devices, places, or event imagery. Use suitable supplied assets first; respect requests to avoid external sources.

- For missing material, search the Web and open official or primary source pages to find images or clips. An empty `find_broll` result requires this lookup before falling back to diagrams. Use one batch of up to three targeted queries, plus at most one such follow-up batch for unresolved material.
- Batch page reads and downloads. Before authoring, inspect a downsized image sheet or representative source frames for subject match, usable detail, and crop suitability. Replace unsuitable candidates within the research limit.
- Use accepted assets in relevant beats with framing or motion that explains the speech. Unless the user names a trigger or a count, use each supplied asset once, at the single beat it fits best; a stated trigger such as "whenever X is mentioned" applies at every matching beat. Record source URLs locally; apply the [on-screen text rules](#on-screen-text) to visible labels.

## Delivery boundary

Deliver the editable project link by default. Treat "finished video" or "final cut" as a completed preview, not an explicit MP4 request. Export only when the user explicitly requests an MP4, rendered video file, or export. For an authorized export, wait for completion and return its link without opening, playing, sampling, or analyzing the output.

Do not inspect the generated preview or MP4, including browser playback, screenshots, contact sheets, frame extraction, audio analysis, or delegated inspection. Do not start a post-delivery review, repair, or aesthetic iteration. This stopping condition applies whether the deliverable is a preview or an explicitly requested export. Input-media analysis, including retrieved source assets, and local static contract checks before submission remain allowed.

Use only this package's [AI Producer composition contract](../aip-composition/SKILL.md) and [workspace reference](references/workspace.md) for integration. Read the workspace reference once before source upload or export, the composition contract once before authoring, and the [framing skill](../aip-framing/SKILL.md) once before deciding the speaker's frame for each beat; load the linked PIP example only when needed, the [dynamic caption skill](../aip-dynamic-caption/SKILL.md) once before the caption layer when it is listed, and the [handoff reference](references/handoff.md) once when the request carries a pasted `@aip` reference line from the Motion library. Do not search global HyperFrames or media-use skills, backend source, or repository documentation to make this video. Resolve these links relative to the skill actually loaded, never a remembered versioned cache path. If that path is stale, use the host's installed-plugin listing once to find the enabled package and its version.

## Talk to the user

Treat every commentary, confirmation, progress update, warning, refusal, and final reply as user-facing product copy. Match the user's language. Lead with the user's current state: what is ready, what is still happening, and what they need to do next. Keep routine progress concise.

Call the product AI Producer in everything the user reads, and never name the environment it runs against, the endpoint, the server, this plugin, or any part inside it.

Do not narrate implementation policy or expose skill names, tool names, IDs, tasks, digests, graphs, checkpoints, commits, upload signing, provider or runtime checks, internal files, or status codes. Keep those details inside tool calls and local logs. Translate a necessary limitation into its effect on the user's project and the next available step.

Plain language must remain accurate. Say that a project is ready only after the corresponding operation succeeds. For a refusal or failure, explain what could not be completed, how it affects the project, and what can happen next. Do not repeat a non-actionable internal warning unless it materially changes what the user should expect.

## Known issues

**The host reports that the MCP server requires OAuth reauthentication, or this plugin's tools are absent from the tool list with nothing else offered to explain it.** This is the client validating the credential it stores locally, not a service fault. No request leaves the client, so no service error exists to read and nothing can be retried or repaired from inside the conversation. Signing in clears it, but the session that hit it does not reliably reload the tools, so do not wait for them and do not deliberate over whether to. When the host reports a condition of its own, such as the service being unreachable or a network failure, that is a different problem and signing in does not address it: report what it means for the user's project instead of running this flow.

Both steps belong to the user, in this order.

1. Ask the user to sign in once to the `ai-producer` server in their own client. In Claude Code this is `/mcp`, then `plugin:aip:ai-producer`, which is how that host namespaces the same connection. In Codex, on the desktop app as much as in the CLI, it is `codex mcp login ai-producer` run by the user in their own terminal: the desktop app carries no sign-in control of its own for a plugin's connection, and the commands you run reach no network, so this is not something you can do for them. Name the entry for the host they are on, because the user selects it by name, and keep everything around it in product language. Do not assemble an authorization link, do not advise reinstalling the plugin, and do not modify MCP configuration. None of these restores the connection, and each can cost the user a working install.
2. Then ask the user to start a new chat and resume the work there. The hosts differ: in Codex the user @-mentions this plugin, and in Claude Code the user simply makes the request again, which loads it. State exactly what carries over: an existing project keeps its footage and its edit behind its project link, while anything the failed connection prevented from reaching AI Producer has to be sent again.

A plugin update can require signing in once more. That is expected, and it happens once.

## Show progress in Codex

In Codex, as soon as an AI Producer creation/preparation tool returns `project_id`, call `get_view_url`, then `open_in_codex` with `target: {type: "browser", url: <exact returned url>}` and `placement: "right"`, omitting `threadId`. Open during preparation; retain the exact `agent_page_url` for reopening in that browser, and `page_url` for the hand-back. The exchange URL is single-use: do not fetch it separately or include it in messages or files.

Opening is a status-only handoff to the user, not inspection. Use no external browser or computer-use action that returns page content. Keep the tab for live updates without reopening, refreshing, polling, playing, or inspecting it.

`queued` means pending. Retry an explicit failure at most once with the same tool, obtaining a fresh exchange URL only if the first may have been consumed. If unavailable or still failing, report it and continue editing; never claim the page opened.

## Default editorial taste

A settled round is the user's own instruction, so it outranks every default below, and a default never fills a round that is still open. A footage-only or vague opening is not licence to skip the rounds: settle them first, then plan from these defaults for everything the rounds and the user left unsaid.

Plan each new talking-head edit from its supplied media and publishing brief. The user's request, in the brief or in a later edit, is the highest instruction: it overrides any default below, and nothing listed or unlisted among your skills blocks it. A listed skill sets a default and the method for it; an unlisted one only drops that default, so a treatment the user asks for is still delivered with the tools the service exposes. Keep the rest of the defaults. Preserve established choices in follow-up edits unless the user requests changes.

### Editing

- Open with a sharp punch-in and whoosh, then hold the framing. Place massive, extra-bold text behind the presenter, spanning 80-90% of the frame width, partially occluded by the head but still readable. Reveal words individually; split or wrap instead of shrinking. Use high-contrast text, preserve the original background, and animate only the text after the punch-in.
- Use presenter close-ups and zooms for emphasis.
- For concrete subjects, prefer relevant real footage, then images, then vectors.
- Show the specific change described by the speech. Use generic geometric shapes, expanding cards, or checkmarks only when they clarify that change; prefer a direct demonstration when suitable footage or assets are available.
- Captions are on by default while aip-dynamic-caption is listed, and they stay on during visual moments; the framing skill places the band for each layout. Apply the finishing round's choice.
- For sarcasm, self-deprecation, or brief reminders, use a monochrome or desaturated presenter close-up for at most one sentence, then restore color.
- Use smooth effects and layout transitions; minimize hard cuts.
- No background music.

### Visual style

- Use a pure black canvas with near-black foreground surfaces, fills only, no strokes; preserve source-media colors unless a specific treatment is intended.
- For abstract relationships, mechanisms, and processes, prefer 3D animation, then SVG or vector.
- Every visual must animate purposefully from entry to exit; each motion reveals a step, relationship, or change; transitions and camera moves don't count.
- No titles, headings, or decorative copy. If a beat has no meaningful visual without its copy, show the presenter, with captions only when enabled.
- Center the focal point within each visual area. Keep all graphics inset at least 10% from the edges throughout the animation; avoid dense repetition and unnecessary layers so graphics stay large.

### On-screen text

These rules govern extra authored copy; spoken captions remain a separate layer governed by the caption skill.

- Authored vectors, diagrams, and animations default to no secondary text. Keep core values and units attached to the quantities they depict. Add an object, category, or relationship label only when its absence creates a specific ambiguity that the visual and simultaneous speech do not resolve. Omit labels that merely name a recognizable object or restate what the visual and speech already convey.
- Sourced B-roll or images may carry one short source or example label, only when the material could be mistaken for the speaker's own footage or demonstration. Authored graphics carry no provenance labels, "illustration" disclaimers, or explanatory footnotes.
- Before publishing each effect, apply a deletion test to its local composition source: if removing an extra label preserves the meaning in the context of the speech, remove it. This is a source-text check before submission, not inspection of the generated preview.

## Make, submit, stop

Inspect the supplied media and plan once. When the user ties a visual to an on-screen cue such as a gesture, a prop, or an action, locate that moment from representative source frames as well as the transcript; this is input-media analysis, not output inspection. Batch independent metadata reads and material downloads in one script. Fetch a transcription only after its task completes; do not repeatedly fetch an unfinished transcript. When the available tool schema supports `wait_seconds`, use it with the supported limit; otherwise obey the returned polling interval. Waiting is not a reason to load more skills or inspect backend code.

Plan the whole edit locally. When the current schema exposes `authoring`, set it to `true` on a new project's creation/preparation request or an existing project's first `sign_workspace_upload` request. Set it to `true` on any intermediate commit and `false` on the final commit, so the service can retain and then close external-authoring status. This uses existing calls only; never add a provider call, model subtask, heartbeat, or polling round for status. Omit the field when the schema lacks it.

For a fresh project in Codex, use the [progressive checkpoint flow](references/progressive-publication.md). Plan the complete edit once. Publish the first effect as soon as it is ready. Then author the remaining effects in batches of up to two while the preceding batch publishes. Keep drafts isolated and let the helper publish each effect in order using the AI Producer MCP tools already loaded in the current task. Preserve the planned effects, timing, and transitions; batching controls scheduling only. Keep unfinished beats full-length with normal presenter framing, and publish without intentional delays. Do not launch another Codex CLI, app server, task, or model subtask. The last commit closes authoring status: the final batch of a caption-free edit, otherwise the caption commit that follows the last batch.

Run the batch helper in the execution that writes its drafts. It handles signing, uploading, committing, held waiting, and receipt acceptance without separate model coordination or receipt-collection turns. The final receipt includes earlier warnings. If the host cannot keep an execution alive while authoring continues, await each batch without claiming overlap. Other hosts, existing effect graphs, and zero-effect edits use ordinary complete-graph publication. Measure actual tokens and duration; overlapping work is not a cost or quality guarantee.

The progressive helper runs the local contract and timeline checks, freezes the hashes the current task supplies to `commit_workspace`, and advances only from that commit's accepted receipt. Use the plan it returns once; do not recompute its digest or expected files in the host. For ordinary publication, run [preflight.py](scripts/preflight.py) as described in the workspace reference, or skip it and let admission report contract errors if no Python 3.9+ interpreter is available; batch signatures and uploads with [upload_batch.py](scripts/upload_batch.py) or the host's batch HTTP tools, then commit with the current `base_digest`. Every commit remains all-or-nothing. A signing, upload, commit, task, or receipt failure leaves the current checkpoint closed without automatically retrying a mutation or adopting another writer's digest. Report it with the last successful effect count; do not restart the full sequence. Tool descriptions own authentication, limits, and task state.

After the final requested graph is accepted, deliver the durable project link (`page_url`, retrieved if missing) in the final reply, then stop unless an export was explicitly requested. Give the user that link in the same reply that says the run has started, not only at the hand-back: the project exists and is watchable from the moment it is created, and a run is long. A view-ticket url is never that link - it is single-use and signs whoever opens it into your own account, so it does not go to the user. Translate refusals and material warnings under the user-facing language contract; do not repeat internal codes or mechanisms. Do not claim visual quality, audio synchronization, or export compatibility. Close by handing final confirmation to the user: state what was applied, then ask them to confirm the result on the project page, already open beside the conversation in Codex, otherwise at the link in this reply. Word this as a completed delivery waiting on the user's review.
