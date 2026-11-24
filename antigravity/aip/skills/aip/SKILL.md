---
name: aip
description: "Create or update an editable AI Producer video. Use when someone provides footage or an existing project and asks AI Producer to cut or edit it, add captions or subtitles, motion graphics or animated effects, background music, or inserted images or video clips, export the finished video, or adapt a named Motion Library template, in any language. Cut a new project with fixed settings instead of asking about them, and copy the captions, motion graphics and transitions of a reference video the user supplies."
---

# AI Producer preview

Create one editable AI Producer preview from the user's footage and creative brief.

## Working folder

Every project, a new one or a change to an existing one, keeps the files you make on this computer in a working folder of its own. At its start, before you download or write anything for it, read [this computer's reference](references/environment.md) once and make that folder as it says; never write to a fixed path or reuse a folder you did not create for this project unless the user hands it to you. Check a page on this computer only as its [local checks](references/environment.md#checks-on-this-computer) say.

**Which project.** Act only on the project this request is about. `list_projects` is for finding that project, as when the user asks to continue their last one or a start ended with no answer; never read an unrelated project to borrow a file from it.

## Targeted changes to an existing project

When the request targets an existing AI Producer project, begin from its current saved edit and make only the requested change. Do not upload the source again, restart project preparation, or change its settings unless the user asks. A change that touches captions, sound effects or music, or moves the cut, follows [their rules](references/new-project.md#captions-sound-effects-and-music): read them once first.

A natural request to use or adapt a Motion Library template, together with its `Project` and `Template` context line, is an existing-project change. Read the [Motion Library handoff](references/handoff.md) once and follow it before the new-project flow below. A line that starts with `@aip` in place of that context line follows [legacy `@aip` lines](references/legacy-aip-line.md) instead.

## Settings for a new project

A new project is cut with fixed settings, and you never ask about them: do not put the rough cut, captions, music or sound effects to the user, draw a card or widget for them, or call `present_choices` or `record_choices`, even when those tools are offered. The user's own words outrank these settings, in the opening message or any later one; the saved default fills what they leave unsaid; the table fills the rest.

| Setting | Default |
| --- | --- |
| Rough cut | `balanced` |
| Captions | on, in the plain look the [dynamic caption skill](../aip-dynamic-caption/SKILL.md) gives them |
| Sound effects | on, from the library |
| Background music | off |

At the start of every new project, read `get_editing_preset`. A preset it returns replaces the default of every setting it stores, and a stored `editing_preference` is the user's own words about the fine cut. Read it fresh on every project rather than remembering it, because the user changes it on the web settings page and only this read shows that; the default is theirs to set there, never through you: the server has a `save_editing_preset` tool, but it is not yours to call.

In the message that says the run has started, name the settings you are cutting with in one plain sentence, so the user knows they can change any of them.

Preparing the project waits for nothing. In the turn the footage arrives, mint the upload target with `sign_upload` and start the PUT so that it runs on without holding you, as [the footage upload](references/environment.md#the-footage-upload) says. While the bytes move, read the saved default and the price. The moment the PUT finishes, call `start_transcribe_project`: ingesting and transcribing the source is the long part of the run, so it starts as soon as the bytes are in. A failed or interrupted PUT is sent again to the same target until it expires, and signed again after that. Two things hold preparation back, and only these. A conversation with no computer behind it, which Known issues below covers: nothing is signed there, and the project starts from the attachment instead. That is the ChatGPT Chat path; Cursor without command or file access pauses for that access instead, as Known issues says. And the user asking to talk the edit through before anything is spent: that is an instruction, so tell them what preparing costs, settle what they want to settle, and start preparation when they say to go ahead.

Whether preparation can charge this user is for `get_pricing` to say, never memory: read it before you start, without a project since none exists yet. Preparation is free only when its row is in the `free` band or the billing detail says nothing reaches this user's wallet; a row with a `per_unit` price can charge, including one a daily quota may cover first. When it can charge, whatever you say when you start preparation carries the price: your first reply on the project. The price reaches the user in plain words, as what getting their video ready costs, and when a daily quota may cover it first, say so. When it is free, that message says nothing about money, not even that it is free: no zero amount, no credits, no note about free usage or a limited time, because a price the user never asked about, read out when nothing is charged, only confuses them. A user who asks what something costs, or asks to talk the edit through before anything is spent, is answered from `get_pricing` either way, free included. A free usage status or refusal the service reports later is passed on as it reads.

The settings run without a question, so their prices reach the user the same way, in the sentence that names them. Read the row of each setting whose tool you will call - sound effects, music when it is on - from the same `get_pricing` read; captions are yours to write and carry nothing about money. A setting whose row can charge carries its price, or its ceiling where the row gives one, in that sentence, worded as what that part of the edit costs, so a user who would rather not pay for it can turn it off before it runs. Its tool is not called before that message is sent.

Before the message that says the run has started, read [a new project's reference question and finishes](references/new-project.md) once: when and how to ask the user for a reference, and how captions, sound effects and music are made.

### Rough cut

`off` means keep the original cut: no filler word, retake, false start or pause is removed. `off` is not a boldness and never travels on to anything that takes one. The other three - `conservative`, `balanced`, `aggressive` - say how far the clean-up goes. You make this cut yourself by writing the speaker clips, so its scope is yours to keep: on their own, these levels remove only filler words, verbatim restarts, abandoned false starts, failed retakes, and dead-air pauses. A fluent, complete sentence is content at every level, even when it seems less important, repetitive, or off topic; dropping it needs editorial scope from the user, and a scripted read with no disfluencies is left whole under cleanup alone. Without a requested duration, highlights, short version, or named removal, the speaker clips cover the rest of the source in order. Cut to the rough-cut setting and to the user's requested scope and duration, preserving the speaker's intended meaning. For a rough-cut-only or targeted speech-cleanup request, skip visual research and default visual treatments unless they are also requested. When revising the rough cut of an existing project, start from its current saved state: preserve choices outside the requested rough-cut change, and update affected captions, visuals, and audio timing to follow the revised cut. When the request includes both rough cut and fine cut, settle the content cut before finalizing timed treatments, then complete both.

For a requested duration, highlights, or short version, read [duration](references/duration.md) before you select the speech.

### Fine cut

The fine cut is yours to design under the [creative direction](#creative-direction) below, and it is never a question: do not ask how the user wants the footage edited, offer worked examples of a style, or ask for a described look. The user's own words outrank that direction wherever they speak to the fine cut - in any message, or the saved default's `editing_preference` - and the direction fills everything they left unsaid. A picture the user hands over to set the look is a reference of stills, as below; use it without asking for one.

Every fine cut, with a reference or without one, keeps the [aesthetic rules](references/aesthetic-rules.md); when the rules, the user's words, a reference and the direction disagree, they say which wins.

A reference video is the one input the direction yields to. When the user gives you a video, a link to one, images of a style, or a preset reference style, and wants their footage edited in its style, read the [reference style skill](../aip-reference-style/SKILL.md) before you plan the fine cut, and follow it for the captions, motion graphics and transitions.

## A request from the AI Producer web page

A request that names a web assignment hands you, through `get_web_assignment`, what the user chose on the web page. Read [the web page request](references/web-assignment.md) first and follow it, also when the assignment cannot be read.

## Source supporting visuals

Every new edit researches real supporting imagery once preparation has started, in the initial plan: read [supporting visuals](references/supporting-visuals.md) once and follow it.

## Delivery boundary

Deliver the editable project link by default. Treat "finished video" or "final cut" as a completed preview, not an explicit MP4 request. Export only when the user explicitly requests an MP4, rendered video file, or export. For an authorized export, wait for completion and return its link.

Each time you hand the project back, the first delivery and every later edit, call `finish_project` once after the last commit is accepted, before any export and before the reply that hands it back. Until then the project page shows the edit as still in progress and keeps its editor locked, so the user cannot review the cut or adjust it by hand. Finishing does not export, freeze, or charge for the project. A project made in the AI Producer web app takes no `finish_project` and refuses it; for one, the final commit's `authoring: false` is what ends that status.

Do not inspect the generated preview or MP4, including browser playback, screenshots, contact sheets, frame extraction, audio analysis, or delegated inspection. Do not start a post-delivery review, repair, or aesthetic iteration. This stopping condition applies whether the deliverable is a preview or an explicitly requested export. Input-media analysis, including retrieved source assets, local static contract checks before submission, and the [reference style skill](../aip-reference-style/SKILL.md)'s local caption matching remain allowed.

Use only this package's [AI Producer composition contract](../aip-composition/SKILL.md) and [workspace reference](references/workspace.md) for integration. Read the workspace reference once before source upload or export, [publication](references/publish.md) once before your first commit, the [aesthetic rules](references/aesthetic-rules.md) once before planning the fine cut, the composition contract once before authoring, and the [framing skill](../aip-framing/SKILL.md) once before deciding the speaker's frame for each beat; load the linked PIP example only when needed, and read the [dynamic caption skill](../aip-dynamic-caption/SKILL.md) once before writing captions when it is listed. Do not search global HyperFrames or media-use skills, backend source, or repository documentation to make this video. Resolve these links relative to the skill actually loaded, never a remembered versioned cache path; when that path is stale, [the installed package](references/environment.md#the-installed-package) says how to find it.

## Talk to the user

Treat every commentary, confirmation, progress update, warning, refusal, and final reply as user-facing product copy. Match the user's language. Lead with the user's current state: what is ready, what is still happening, and what they need to do next. Say that a project is ready only after the corresponding operation succeeds. Keep routine progress concise.

Call the product AI Producer in everything the user reads, and never name the environment it runs against, the endpoint, the server, this plugin, or any part inside it.

Do not narrate implementation policy or expose skill names, tool names, IDs, tasks, digests, graphs, checkpoints, commits, upload signing, provider or runtime checks, internal files, or status codes. Keep those details inside tool calls and local logs. Translate a necessary limitation into its effect on the user's project and the next available step.

## Feedback about AI Producer

When `send_feedback` is among your tools, read [feedback](references/feedback.md) before you reply to a user who asks you to tell the team something, voices a reaction to AI Producer itself, asks for something AI Producer refuses or has no way to do, or asks for the same change a third time.

## Known issues

**The host reports that the MCP server requires OAuth reauthentication, or this plugin's tools are absent from the tool list with nothing else offered to explain it.** Follow [sign-in repair](references/host.md#sign-in-repair) before anything else; a condition the host reports of its own, such as the service being unreachable, is not this.

**The conversation has no computer behind it** (ChatGPT Chat): never sign an upload or start editing there; read [what works without a computer](references/environment.md#a-conversation-with-no-computer) before you reply.

**Cursor cannot run commands or edit files in this chat:** sign no upload and start no project until the user turns that access on, as [Cursor without command or file access](references/environment.md#cursor-without-command-or-file-access) says.

## Progress and the project link

When an AI Producer creation/preparation tool returns `project_id`, open the project's progress page for the user as [the host reference](references/host.md) says for this host: at once, or, while a new project's [reference question](references/new-project.md#ask-for-a-reference) is unanswered, right after the answer. Every project link the user gets is `page_url`, written for this host as that reference says.

## Creative direction

The user's own words and the [settings for a new project](#settings-for-a-new-project) outrank everything below, and a reference video the user supplies outranks it for captions, motion graphics and transitions, as the [reference style skill](../aip-reference-style/SKILL.md) says. This direction is the default for everything else in the fine cut, inside the [aesthetic rules](references/aesthetic-rules.md): they own the rules they state, and where a line below sets a number past one of their floors, the floor holds.

Plan each new talking-head edit from its supplied media and publishing brief. Nothing listed or unlisted among your skills blocks the user's request: a listed skill sets a default and the method for it; an unlisted one only drops that default, so a treatment the user asks for is still delivered with the tools the service exposes.

Fine-cut the video like a high-performing social media creator: deep-fried, brainrot pacing, every trick in the book. Prioritize frequent, high-quality B-roll and visually striking 3D motion graphics throughout the video. Make dynamic layout and camera changes, and make each one mean something, especially when the speaker explains data. Create full-screen 3D motion graphic moments that visualize the ideas the speaker says, with animated 3D objects, immersive compositions, and cinematic B-roll. Keep the motion graphics constant and legible, in one palette pulled from the source video: sample representative frames and build the ground, accent, and type colors from the footage's own dominant hues - wardrobe, set, light - saturating one of them for the accent.

### Editing

- Open on massive extra-bold text behind the presenter, as wide as the aesthetic rules' safe area allows, every word whole and readable. Never shrink, shift, or split-screen the presenter to fit the text.
- Presenter close-ups and punch-ins for emphasis, each a zoom effect host, sized and held as the aesthetic rules' punch-in section says; the rules' meaning tier says which lines take a punch-in, a monochrome aside or another treatment.
- Punchline, reveal, or a hard-hitting number: an impact shake motion host of at most 0.45 s on the beat, landing with the slam or number it punctuates; a hard section change: a white flash motion host of at most 0.35 s. At most one shake or flash in any 20 s, a shake and a flash on the same hit counting as one, and never over ordinary sentences. A motion host's offset, scale, and rotation move only the full-frame speaker video, so they are invisible while a seat or full cover hides it: place a shake, whip, or push on a speaker beat, and land an impact inside a moment on that moment's own wrapper instead. A flash's color overlay covers the whole frame and reads anywhere.
- Show the specific change the speaker describes; demonstrate with real footage or assets when available.
- Turn the screen over often, at the rhythm the aesthetic rules set. Short, dense moments beat long, sparse ones.
- Abstract ideas are animated and real things shown as real imagery, as the aesthetic rules' material section says. Where 2D and 3D show a concept equally accurately and obviously, take 3D: a Three.js scene under the composition skill's code-drawn rules, or DOM elements given real depth with CSS 3D. Stage real imagery with depth or camera motion.
- Choose each moment's layout from the measured frame, not a fixed order. When the measured head leaves a clear band, as in a medium or wide shot, an **Overlay** keeps the speaker on screen. When it does not, as in a close-up that fills most of the frame, alternate **Full cover** moments for ideas, data, and B-roll with **Seat** moments that keep the speaker in a shape beside the payload.
- Return to the full-frame speaker between moments, where its zooms, filters, and camera treatments carry the beat.
- Smooth effects and layout transitions. A hard cut between layouts is a last resort; the aesthetic rules' jump-cut reframes, and a reference that cuts hard, keep their hard cuts.

### Visuals

- Every visual animates with purpose from entry to exit; each motion reveals a step, relationship, or change. Transitions and camera moves don't count.
- No titles, headings, or decorative copy beyond the opening text. Labels inside a diagram are fine. If a beat has no visual without its copy, show the presenter.
- Center the focal point. Keep text and graphics inside the aesthetic rules' safe area throughout the animation.
- Keep graphics large: one idea each, no repetition, no extra layers.

### On-screen text

These rules govern extra authored copy; spoken captions are governed by the caption skill.

- Authored vectors, diagrams, and animations default to no secondary text. Keep core values and units attached to the quantities they depict. Add an object, category, or relationship label only when its absence creates a specific ambiguity that the visual and simultaneous speech do not resolve. Omit labels that merely name a recognizable object or restate what the visual and speech already convey.
- Sourced B-roll or images carry no source label, license notice, or credit overlay unless the aesthetic rules' material section calls for one. Authored graphics carry no provenance labels, "illustration" disclaimers, or explanatory footnotes.
- Before publishing each effect, apply a deletion test to its local composition source: if removing an extra label preserves the meaning in the context of the speech, remove it.

### A video with no speech

When `start_transcribe_project` or `get_project` carries `speechless_source`, the video has no spoken words - only music or other sound, or no audio track - so it has no transcript. Its `instruction` is the contract for the edit; this skill adds only:

- The aesthetic rules hold, and what they time to speech - the first beat within the first sentence, an element arriving with its word, a beat boundary between words, the meaning tier's triggers - is timed to the picture and the music's beats instead, with more visual moments where the aesthetic rules' rhythm needs them (the picture's own changes of shot count as beats).
- Tell the user once, in plain words, that the settings the instruction rules out do not apply to this video, whether they came from the defaults, the saved default or the user's words.
- The user's own words about the video include the saved default's `editing_preference`. Direction above that is about the speaker, speech or captions does not apply; its palette, motion and layout rules do.

## Make, submit, stop

Inspect the supplied media and plan once. When the user ties a visual to an on-screen cue such as a gesture, a prop, or an action, locate that moment from representative source frames as well as the transcript. Batch independent metadata reads and material downloads in one script.

Plan the whole edit locally. When the current schema exposes `authoring`, set it to `true` on a new project's creation/preparation request or an existing project's first `sign_workspace_upload` request and on any intermediate commit, and `false` on the final commit. This uses existing calls only; never add a provider call, model subtask, heartbeat, or polling round for status.

Publish as [publication](references/publish.md) says: every host commits the complete graph, and it covers what to do when a step fails.

Pass `skills_receipt: "aip-file-5791ab75ae69"` on every `commit_workspace`, exactly as written here: it tells AI Producer which copy of these skills the edit followed, and changes nothing about the commit.

After the final requested graph is accepted, deliver the durable project link (`page_url`, retrieved if missing and written for this host as [the host reference](references/host.md) says) in the final reply, then stop unless an export was explicitly requested. Give the user that link in the same reply that says the run has started, not only at the hand-back: the project exists and is watchable from the moment it is created, and a run is long. A view-ticket url is never that link - it is single-use and signs whoever opens it into your own account, so it does not go to the user. Translate refusals and material warnings under the user-facing language contract; do not repeat internal codes or mechanisms. Do not claim visual quality, audio synchronization, or export compatibility. Close by handing final confirmation to the user: state what was applied, then ask them to confirm the result on the project page, already open beside the conversation where this host shows it, otherwise at the link in this reply. Word this as a completed delivery waiting on the user's review.
