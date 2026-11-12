---
name: aip
description: "Create or update an editable AI Producer video. Use when someone provides footage or an existing project and asks AI Producer to cut or edit it, add captions or subtitles, motion graphics or animated effects, background music, or inserted images or video clips, restyle, export the finished video, or adapt a named Motion Library template, in any language. Cut a new project with fixed settings instead of asking about them, and copy the captions, motion graphics and transitions of a reference video the user supplies."
---

# AI Producer preview

Create one editable AI Producer preview from the user's footage and creative brief.

## Working folder

Every project, a new one or a change to an existing one, keeps the files you make on this computer in a working folder of its own. At its start, before you download or write anything for it, read [this computer's reference](references/environment.md) once and make that folder as it says; never write to a fixed path or reuse a folder you did not create for this project unless the user hands it to you. Check a page on this computer only as its [local checks](references/environment.md#checks-on-this-computer) say.

**Which project.** Act only on the project this request is about. `list_projects` is for finding that project, as when the user asks to continue their last one or a start ended with no answer; never read an unrelated project to borrow a file from it.

## Targeted changes to an existing project

When the request targets an existing AI Producer project, begin from its current saved edit and make only the requested change. Do not upload the source again, restart project preparation, or change its settings unless the user asks.

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

### Ask for a reference

A new project whose opening request gives no reference gets one question about a reference, the only question a new project asks: the user may not know that AI Producer can copy a video's style, and this is where they learn it. A request gives a reference when it carries a video or images the user offers as one, a link to a post, or a preset named or picked. Do not ask on a request sent from the AI Producer web page, whose web assignment already holds the user's choice with or without a reference; on a change to an existing project; when the user said they want no reference or no particular style; or in ChatGPT.

Ask in the message that says the run has started, and end the turn with it, in the user's language, as a plain numbered list, never a card or a question tool, because the answers are pasted text and attached files:

1. Pick a style preset in the panel beside this chat and paste what its Recreate button copies.
2. Paste a link to an Instagram, YouTube or TikTok post.
3. Send a reference video or images.
4. Skip, and AI Producer edits in its own style.

That message still names the settings and carries the price of preparation, as above.

Right before you send it, once `start_transcribe_project` has returned, call `get_view_url` without `project_id` and `list_reference_presets`. Offer the first option only when the first answers with a link and the second lists at least one preset; a refusal (`presets_view_not_available` means the account is not offered the presets yet), an error, or an empty list leaves it out and renumbers the rest. With both, show the presets as [the presets page](references/host.md#the-presets-page) says for this host, as the turn's last calls before the question: the presets appear together with the options that explain them, never during the upload, when nothing in the conversation says what they are for. The user answers with a preset's id or name, or pastes what its Recreate button copies.

Send the question as the last message of the turn, with the project link, and end the turn. Nothing else runs before the answer, the rough cut included: a question asked while the work goes on is easily missed, and the user then meets an edit their pick should have shaped. While the question is open the presets stay beside the conversation; open the project's progress page only after the answer, before any other work.

Read the answer. A pasted Recreate prompt names a preset by its id and catalogue version: read it with `get_reference_preset`, passing both, and when that version is no longer offered, read the id alone. A preset the user names is matched in `list_reference_presets`. A link, a video or images are the reference. Only an explicit skip or decline means no reference, and the fine cut then follows the creative direction. A reply about something else, such as a question about the price, a change to a setting or a problem with the upload, is answered as usual and keeps the choice open: never repeat the question, and end that turn too, with one line saying the pick is still open. Once the reference is settled, write the rough cut and then everything the reference shapes: reading a reference, captions, motion graphics, transitions and the reframes that carry its cutting rhythm.

### Rough cut

`off` means keep the original cut: no filler word, retake, false start or pause is removed. `off` is not a boldness and never travels on to anything that takes one. The other three - `conservative`, `balanced`, `aggressive` - say how far the clean-up goes. You make this cut yourself by writing the speaker clips, so its scope is yours to keep: on their own, these levels remove only filler words, verbatim restarts, abandoned false starts, failed retakes, and dead-air pauses. A fluent, complete sentence is content at every level, even when it seems less important, repetitive, or off topic; dropping it needs editorial scope from the user, and a scripted read with no disfluencies is left whole under cleanup alone. Without a requested duration, highlights, short version, or named removal, the speaker clips cover the rest of the source in order. Cut to the rough-cut setting and to the user's requested scope and duration, preserving the speaker's intended meaning. For a rough-cut-only or targeted speech-cleanup request, skip visual research and default visual treatments unless they are also requested. When revising the rough cut of an existing project, start from its current saved state: preserve choices outside the requested rough-cut change, and update affected captions, visuals, and audio timing to follow the revised cut. When the request includes both rough cut and fine cut, settle the content cut before finalizing timed treatments, then complete both.

For a requested duration, highlights, or short version, read [duration](references/duration.md) before you select the speech.

### Fine cut

The fine cut is yours to design under the [creative direction](#creative-direction) below, and it is never a question: do not ask how the user wants the footage edited, offer worked examples of a style, or ask for a described look. The user's own words outrank that direction wherever they speak to the fine cut - in any message, or the saved default's `editing_preference` - and the direction fills everything they left unsaid. A picture the user hands over to set the look is a reference of stills, as below; use it without asking for one.

Every fine cut, with a reference or without one, keeps the [aesthetic rules](references/aesthetic-rules.md); when the rules, the user's words, a reference and the direction disagree, they say which wins.

A reference video is the one input the direction yields to. When the user gives you a video, a link to one, images of a style, or a preset reference style, and wants their footage edited in its style, read the [reference style skill](../aip-reference-style/SKILL.md) before you plan the fine cut, and follow it for the captions, motion graphics and transitions.

### Captions, sound effects and music

**Captions.** You write them as caption moments, as the [dynamic caption skill](../aip-dynamic-caption/SKILL.md) says, in its plain look unless a reference or the user's words describe another; a saved default that names a caption pattern means captions on, in that plain look. Never call `build_captions`. `no-caption` is the saved default's word for captions off: write no caption moments. For an existing captioned project the user wants without captions, remove only its caption hosts - caption moments, or a `narrator-captions` host the service built - preserve transcript and editor artifacts, then commit the changed root with `commit_workspace`.

**Background music.** Off unless the user or the saved default turns it on; on is the instruction to call `add_music` afterwards. Off declines a new music run; it does not strip a bed already mixed into the cut, so do not offer to take music away with it.

**Sound effects.** On unless the user or the saved default turns them off: place sound effects from the library on this project. Read the library with `list_sound_effects` and choose every sound from what it lists. Never call `add_sound_effects`; when no listed sound fits a moment, leave that moment without one. Design each effect from the motion it accompanies, read off the finished cut's timeline and the compositions you wrote, in milliseconds on that timeline, never the source's:
- A single instant - a cut, an emphasized word, an element landing - takes one sound that meets the instant the motion lands or resolves, not the instant its element appears.
- A run of discrete actions - items dropping in one by one, a list filling, repeated clicks, coins raining down - takes a short sound on its first action and one on its last, never one on every beat; a run of three or four actions may instead take one on every other action. A sound with several hits covers a run only when its `hits_ms` fall on the actions' beats, and then it is the run's one effect; never lay a long sound with many hits over a run whose beats it misses.
- A motion that builds to a result - a line drawing, a counter climbing, a slow reveal - takes a long sound that carries the whole build, such as a riser, whoosh or texture ending where the result lands, with a short sound that names the result placed on that instant.

Line up every sound that marks an instant, the ones on a run's actions and the one on a result included, with `anchor: first_hit`, and a riser or whoosh that carries a build with `anchor: peak`, the moment it lands. A sound shorter than its motion is still the right sound when its content fits: let it mark the instant the motion resolves, or carry the span with a long sound under it, rather than trading it for a worse match.

Effects punctuate the cut; they are not a bed under it. A few chosen sounds read as design, and one on every motion reads as noise and buries the voice, so many motions you build take no sound. Before you place the set, check it on the finished cut's timeline against these limits, and when more motions qualify than the limits allow, keep the strongest moments and drop the rest. A user who asks for more or fewer effects sets the count and spacing instead; the weight and palette rules still hold:
- Budget: no more effects than the cut's length in seconds divided by 2.5, about 10 to 12 in a 30 s video, and fewer when the cut is calm. A long sound and the short one on the result it builds to count as one effect.
- Weight: a heavy, signature sound - a boom, an impact, a big whoosh or riser - goes only on the hero moments: the opening hook, the key turn, and the ending. Every other moment takes a lighter sound, such as a click, tick, pop or soft swish, or none. A motion graphic takes at most one signature sound.
- Spacing: separate effects start at least 600 ms apart. Sounds closer than that are one designed hit of at most two layers - two sounds starting together, or a long sound landing on its result's hit - and count as one effect; otherwise drop one of them.
- Silence: every 10 s of the cut holds at least one stretch of 3 s or more where no effect starts. No effect plays over the words of a key spoken line - the hook's claim, the turn, the takeaway - so a signature sound on a hero moment sits in the pause beside its line; elsewhere, when a motion falls near a pause between phrases, put its sound in the pause.
- Palette: draw every effect from 2 or 3 sound families for the whole video, the same few sounds returning, not a different sound for each hit. Choose families that fit the edit's style: the reference's pace and graphics when there is one, since its own sound is never used, and the creative direction otherwise.
- Tone: most sound names carry a tone word: Warm, Deep, Sub, Bright, Crisp or Airy. Bright, Crisp and Airy sounds in quick succession tire the ear, so within a run of actions, or wherever effects start less than 1.5 s apart, a sound with a tone word is Warm, Deep or Sub; a Bright, Crisp or Airy sound goes only on a single accent with no other effect within 1.5 s of it.

Effects mark what happens on screen or in the words, not every sentence; a caption appearing is not a motion to mark. Place them once the cut and its timed treatments are settled, in one `place_sound_effects` call that carries every hit and `replace: true`, so a project that already has effects is not given a second set. When a later edit moves the cut, list again and place the whole set again the same way. Leave `replace` out only to add a sound to the ones already there, as when a call placed some hits and refused others: send each refused one again, corrected, with a new `idempotency_key` and the `project_revision` that call returned. A call that placed none (`nothing_placed`) changed nothing, so send the corrected set again with `replace: true`.

## A request from the AI Producer web page

A request that names a web assignment hands you, through `get_web_assignment`, what the user chose on the web page. Read [the web page request](references/web-assignment.md) first and follow it, also when the assignment cannot be read.

## Source supporting visuals

Once preparation has started, plan in the creative direction below and research supporting material in the initial plan. This research runs on every new edit: real imagery is part of the default, never an alternative to motion graphics. Identify transcript beats that need real products, organizations, interfaces, devices, places, people, or event imagery or footage. Use suitable supplied assets first; respect requests to avoid external sources.

- When the user supplied B-roll, review it as [supplied B-roll](references/supplied-broll.md) says before deciding coverage.
- A-roll follows the settled speech cut; fit B-roll to it without recutting speech to accommodate an asset's length. Trim irrelevant head or tail, adjust coverage over related speech, choose another excerpt, or return to the presenter when a clip does not fit. Let useful matches and continuity decide coverage, without a fixed clip count or coverage quota. Keep a concise local mapping of speech beats, source in/out times, and cut placements.
- For missing material, search the Web yourself for images and video clips, whichever shows the beat better: a clip when the beat is an action, a place or a process, an image when it is one thing to look at. Open official or primary source pages first, press kits and media rooms among them, then libraries whose pages give a direct file link and its license: Openverse and Wikimedia Commons for images, Wikimedia Commons, Pexels, Pixabay and the Internet Archive for video. Keep only licenses that allow commercial reuse and modification - no NC or ND terms - and record each file's source page, author, and license locally so the user can credit them. Never take a clip from a platform's player such as YouTube, Instagram or TikTok. Search in batches by beat: one batch covering every beat that needs real imagery, plus at most one follow-up batch for unresolved beats.
- Trim a clip to the stretch you use and convert it to H.264 `.mp4` no larger than the canvas before staging it. An export handles only so many distinct video files: when a run of beats needs footage from many files with no speaker beat between them, join the excerpts locally into one reel file and reference that. A download the host refuses moves on to the next candidate, and then to an authored graphic. Before authoring, inspect a downsized image sheet or representative source frames for subject match, usable detail, and crop suitability. Replace unsuitable candidates within the research limit.
- Use accepted assets in relevant beats with framing or motion that explains the speech. Unless the user names a trigger or a count, use each image or single-shot clip once at its best-fitting beat. A long video with multiple relevant moments can supply several distinct excerpts across the edit; do not restrict the source file to one use or repeat the same excerpt by default. A stated trigger such as "whenever X is mentioned" applies at every matching beat. Apply the [on-screen text rules](#on-screen-text) to visible labels.

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

When an AI Producer creation/preparation tool returns `project_id`, open the project's progress page for the user as [the host reference](references/host.md) says for this host: at once, or, while a new project's [reference question](#ask-for-a-reference) is unanswered, right after the answer. Every project link the user gets is `page_url`, written for this host as that reference says.

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
- Sourced B-roll or images carry the source label the aesthetic rules' material section sets. Authored graphics carry no provenance labels, "illustration" disclaimers, or explanatory footnotes.
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

After the final requested graph is accepted, deliver the durable project link (`page_url`, retrieved if missing and written for this host as [the host reference](references/host.md) says) in the final reply, then stop unless an export was explicitly requested. Give the user that link in the same reply that says the run has started, not only at the hand-back: the project exists and is watchable from the moment it is created, and a run is long. A view-ticket url is never that link - it is single-use and signs whoever opens it into your own account, so it does not go to the user. Translate refusals and material warnings under the user-facing language contract; do not repeat internal codes or mechanisms. Do not claim visual quality, audio synchronization, or export compatibility. Close by handing final confirmation to the user: state what was applied, then ask them to confirm the result on the project page, already open beside the conversation where this host shows it, otherwise at the link in this reply. Word this as a completed delivery waiting on the user's review.
