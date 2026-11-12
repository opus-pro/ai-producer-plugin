---
name: aip-reference-style
description: "Copy a reference video's captions, motion graphics and transitions onto the user's own AI Producer edit. Use when the user supplies a reference video file, a link to one on Instagram, TikTok or YouTube, images of a style, or picks or names one of the preset reference styles, here or on the AI Producer web page, and wants their footage edited in that style, in any language."
---

# Edit in a reference video's style

A reference sets three things in the user's edit: the captions, the motion graphics (titles, text overlays, stickers, cards, animated graphics, and camera treatments such as punch-ins, shakes and flashes), and the transitions between beats. Everything else follows the [AI Producer skill](../aip/SKILL.md). Its [aesthetic rules](../aip/references/aesthetic-rules.md) hold here as over every fine cut: the reference decides how things look, move and cut, and the rules decide what the edit shows, how much of it and whether it reads, with floors the reference keeps. You copy the reference's style, never its content.

## Get the reference

What getting, reading and matching a reference need on this computer, from downloads to the tools that read it, is in [tools.md](references/tools.md): read it before you get the reference.

- A video file the user gave you is the reference as it is. Images the user gave you are a reference of stills: copy them into one new directory in the project's working folder, in the order given.
- A link to a post on Instagram, TikTok or YouTube: get it as soon as you have it, while the user's footage is still being prepared, with `start_link_download` and the link, download what it answers, and from then on it is a video file the user gave you. Never download the post any other way, such as with a downloader you find installed.
- A preset: read it with `get_reference_preset` and its `preset_id`. A preset the user names or describes is matched by its name and look in `list_reference_presets`, which is also what you show, by name and look, a user who asks which presets there are. Its unpacked `folder` is what [reference_frames.py](scripts/reference_frames.py) writes for the preset's video, with its `caption-kit/` already made when the preset shows captions and its style pack when it was built with one, so you do not run the script for it, and a preset has no video to download or open. When the call answers that no presets are published, or that the preset is unknown or withdrawn, tell the user in one sentence and ask for a reference video, a link or images instead.
- A directory that holds `reference-index.json` is a reference already read, such as a preset's unpacked folder or the folder of one an earlier edit read: use it as it is, without running the script on it.
- A request sent from the AI Producer web page carries its reference in `get_web_assignment`'s answer: a `preset` with its `preset_id` and `catalogue_version`, both passed to `get_reference_preset`; a `link`, fetched as above; or a `video` or `images`, each file with a `download_url`, reading the assignment again for fresh links, used as a video file or a reference of stills. Start on the reference as soon as the assignment says it is ready, without waiting for the footage.
- When `start_link_download` cannot get the post, tell the user in one sentence what its refusal's `error` says and what to send instead. `link_unsupported`: only Instagram, TikTok and YouTube links work, so ask for one of those or the file; `link_download_busy`: say when they can try again from `retry_after_seconds`, and that the file works now. `link_download_unavailable` is a passing problem on AI Producer's side, not the post's: call it once more with the same link, and only when that answers the same ask for the file. Where the `error` names nothing to send, ask for the video file.

Start the user's own footage first, as the AI Producer skill says, so it uploads and prepares while you get and read the reference. Open the project's progress page as soon as `project_id` returns, before the reference is read, as that skill's progress section for this host says: the reading takes a while, and the user watches the project from the start.

## Read the reference

When the reference's folder holds `style/style.md`, it is already read into a [style pack](references/style-pack.md): read `style.md` and the visuals and templates it names first, and make no caption kit for it. A whole pack (its first line `Pack: whole`) is the entire reading: open nothing else of the folder unless `style.md` leaves a question open, which one contact sheet, strip or keyframe then answers. An edit's pack (`Pack: edit`) holds every caption treatment but only the graphics one earlier edit used, so read its contact sheets and transition pages as well, as [reading a reference](references/read-reference.md) says, for the graphics and transitions it does not hold. A whole pack whose `style.md` has a `## Hook` section carries the reference's hook matched already, which the edit follows as [A preset's hook](#a-presets-hook) says.

When the folder holds no style pack, read the reference, pick its caption kit and keep its pack as [reading a reference](references/read-reference.md) says.

## What to copy

- **Captions.** The reference's caption look, matched against the caption kit and written as caption moments as [Matching the captions](#matching-the-captions) says, with the [dynamic caption skill](../aip-dynamic-caption/SKILL.md)'s timing and mounting. A reference with no captions of its own still gets captions, in that skill's plain look, which you write yourself once the cut is final, with no kit and no subagent.
- **Motion graphics.** Each kind of treatment the reference uses, with its layout (overlay, seat, full cover, split), typography, palette, shapes and motion. Recreate each one as a composition under the [composition contract](../aip-composition/SKILL.md), filled with the user's own content: their words, their facts, their imagery. A graphic copies the reference's look, its type, palette, line, texture and motion, and never what it depicts: draw the thing the user's line is about, in that look, arranged as that thing needs, and make objects behave as real ones do. A hand, a body or a figure the reference drew holding, pointing at or reaching for its subject is part of what it depicts: draw the user's subject alone, carrying the motion the hand did, and draw a hand only when the user's line is about holding, giving or reaching, posed the way a hand holds that thing. A shape the reference drew for its own subject, such as an abstract wave or a dot sphere, is used only where the user's words have something it shows. A kind the style pack holds starts from its template, filled as the [style pack](references/style-pack.md) says.
- **Transitions.** How beats hand to each other: a hard cut, a punch-in, a flash, a whip or slide, a blur, a mask, and how text and graphics leave as the next beat arrives. Read each boundary's `kind` against its row, and look for what it cannot name, such as a slide, a mask or a punch-in. Use the transitions the reference uses, about as often as it does. A transition the reference does not show is not used: no flash, shake, whip or glitch it lacks, whatever the creative direction would otherwise add, and a reference that only cuts hard gets hard cuts.
- **Cutting rhythm.** How often the picture changes: `cuts_per_minute.whole` is the reference's rate. When the reference cuts between shots and the user's footage is one continuous shot, carry that rhythm with reframes of the speaker: at a sentence or phrase boundary, change hard to another framing - full frame, a tighter one at 1.3x or more on the face, a recomposition toward one side - as a zoom effect host with no ramp in or out, held for the stretch it frames. Count the visual moments' own changes toward the rate, and alternate framings so no two in a row match. A reframe never removes speech: what is said is the rough cut's alone.
- **Proportion.** Keep the reference's balance between the speaker on screen and showcase shots, within the floors the aesthetic rules' rhythm section sets. What fills a showcase shot is chosen from what the user says at that moment, never to use every treatment the reference has: a treatment goes where the user's content fits it, at most about as often and as long as the reference uses it, and where none fits, a graphic of the user's own subject in the reference's look, B-roll or researched imagery fills the shot. Its most striking element is not a reason to run it across the whole edit, and one it shows once stays a one-off.

A reference of stills shows the captions, the motion graphics, the palette and the layout, but no transitions, cutting rhythm, motion or timing. Copy what the stills show, in about the balance between speaker and graphics they show, and the AI Producer skill's creative direction decides the rest.

Leave the reference's content out:

- its brands, logos, people, product screens, screenshots and words;
- anything that belongs to the platform or the recording rather than the edit: play buttons, progress bars, usernames, watermarks, the platform's own captions and stickers, a cursor or a recording frame.

When a treatment carries a kind of material the user's footage lacks, such as a screen recording or a product shot, find the user's own equivalent through the AI Producer skill's visual research or author it, or give that treatment a different payload from the user's content.

The user's frame decides geometry. When the user's footage differs from the reference in orientation, framing or length, keep each treatment's character and place it with the [framing skill](../aip-framing/SKILL.md).

Where the reference and the AI Producer skill's creative direction disagree about captions, motion graphics or transitions, the reference wins. Everything the reference does not show, the direction still decides. The user's own words outrank both, and the aesthetic rules outrank the reference in the order they give.

## A preset's hook

When a whole pack's `style.md` has a `## Hook` section, read [the preset's hook](references/preset-hook.md) before you plan the user's opening: its hook was matched once, when the preset was built, so an edit copies it rather than matching it again. A reference without that section has its opening copied like the rest of it, as [What to copy](#what-to-copy) says.

## Working files

Keep the files you make while reading the reference and matching the captions in directories you create for them in the project's [working folder](../aip/SKILL.md#working-folder), the rows and report files included, and name them by their full paths. Redo or delete them as [tools.md](references/tools.md) says.

## Matching the captions

This section is for a reference that shows captions. Its captions are written as soon as the cut is final, which it is once the rough cut is written in your local `render-engine/` directory: graphics, framing and sound never move the words, and nothing needs publishing first. Run `caption_cues.py` on that directory then, as the dynamic caption skill says, and keep the rows it prints in a file.

When the style pack holds its caption treatments, they are matched already: write every caption moment yourself from the templates, as the [style pack](references/style-pack.md) says, with no subagent and no kit; stage the faces `style.md` names; then `compare` a page that mounts one of them over a frame of the user's footage, beside that frame, to see that it reads there and that a part that lets the picture through or blends still does over that picture, and publish. A reference whose pack holds no captions is matched against its caption kit as [reading a reference](references/read-reference.md#matching-the-captions) says.

[caption_compare.py](scripts/caption_compare.py) does the plumbing, run as `uv run --with fonttools python <the script> <command>`: `fonts <name>` lists the installed faces of a family, `specimen <out.png> <frame> --text "<words>" --crop X,Y,W,H --size <px> <family>` sets the words in every face of the family under that part of the frame, `extract <font file> <index> <out.ttf>` splits one face out of a collection, and `compare <out.png> <frame>=<page> --crop X,Y,W,H` renders a page at the frame's size beside the frame, cropped to that part at full resolution. Replace a page, an image or a caption moment you rebuild as [Working files](#working-files) says.

Each part of the caption, a line, an emphasized word or a fill, is its own [moment](../aip-composition/SKILL.md) host over the frame, each host its own layer as in the edit, and a part that blends with the picture carries its blend on its host, as the composition contract says. What matches on the page then goes into the edit unchanged but for its words and times.

The pages render locally with a headless browser, as [tools.md](references/tools.md) says. They are reference analysis before publication: they are never staged or uploaded, and they are not an inspection of the edit.

The captions' fonts are font files staged with them, since the export machine has none of this computer's fonts: a face installed here is staged from its own file, a collection such as `.ttc` split to the face the captions use, and only a face you cannot get as a file takes its closest open family. Whether a face's license allows staging it is reviewed outside the edit, so the captions never swap a face for an open family over its license. Their colour is drawn in CSS, never with the reference's own pixels.

## Tell the user

In the message that says the run has started, say in one or two plain sentences what you are taking from the reference - the caption look, the kinds of graphics, the way beats change - and that the content will be their own. Name no file, tool, frame count or window. A reference you could not get or read is said once, in the same plain words, with what the user can send instead.
