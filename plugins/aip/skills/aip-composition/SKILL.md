---
name: aip-composition
description: "AIP-specific composition and editor contract. Read when using the AI Producer plugin to author its HTML workspace; not the general HyperFrames creation workflow."
---

# HyperFrames for an AIP project

<!-- SPDX-License-Identifier: Apache-2.0 -->

Copyright 2026 HeyGen, Inc. Modifications Copyright 2026 OpusClip. Modified by OpusClip for AIP; see [source attribution, license, and changes](../../THIRD_PARTY_NOTICES.md).

HTML is the video: a composition is an HTML element with `data-*` timing attributes and one paused GSAP timeline the player drives. AIP's editor plays your HTML with its own player, and the export renders it with AIP's own pinned HyperFrames; they are two programs with separate playback and editing contracts. This page is the interface those two read, nothing more. What to draw, how it moves, where captions sit and what a moment looks like are your decisions.

## What AIP accepts

- The project lives under `render-engine/`: `index.html`, `compositions/*.html`, and assets under `public/`. AIP stages `public/source.mp4` (the recording) and `public/source.mp3` (its audio) and puts GSAP at `public/vendor/gsap.min.js`; load GSAP from that path.
- The accepted files and upload limits are described in the [AIP workspace format](../aip/references/workspace.md). Scripts from outside the project are refused, so a composition's logic is inline.
- A user's image is staged at `public/images/<name>` and a user's clip at `public/videos/<stem>.mp4`, `<name>` being the filename reduced to ASCII letters, digits, `-`, `_` and `.` (a space becomes `-`, anything else is dropped), because other characters change the URL the browser asks for. The hand-back check confirms every file a composition references through `src` or `href` is in the tree; a file referenced any other way (`data-pip-src`, a CSS `url(...)`) is not seen by it, so stage it in the same upload batch as the composition and confirm it in the listing after the commit.

## What the editor recognises in index.html

- The root: `<div id="stage" data-composition-id="finecut-root" data-start="0" data-duration="<total s>" data-width="W" data-height="H">`. Place this root directly in the document body, not inside a `<template>`. The id is fixed: the editor seeks the root timeline as `window.__timelines["finecut-root"]`, so a root zoom or transition lives on that timeline, and the root creates the registry before any composition registers:

```html
<script>
  window.__timelines = window.__timelines || {};
  const rootTl = gsap.timeline({ paused: true });
  ...root tweens, e.g. on #speaker...
  window.__timelines["finecut-root"] = rootTl;
</script>
```

- The speaker: `<video id="speaker" class="clip" src="public/source.mp4" muted playsinline data-volume="0">` and `<audio id="speaker-audio" class="clip" src="public/source.mp3" data-volume="1">`. Keep unique media IDs. Speaker video is silent; the source audio is the audible leader. Generic extra `<audio class="clip">` tags are not AIP sound-effect tracks: AIP audio tracks require its editing document and derived `track-audio` elements. After a cut, use N video/audio pairs over the same two files. Each element has `class="clip speaker-clip"`, a unique `id`, and `data-start`, `data-duration`, `data-media-start`, and `data-track-index`. A pair shares its `data-hf-id` and timing; give each pair a distinct `data-hf-id`. Keep `speaker` and `speaker-audio` on the first pair. DOM order is output order on each speaker track, so write the spans in playback order with consecutive output starts.
- A visual moment: one `<div class="visual-host clip" data-composition-id="<id>" data-composition-src="compositions/<file>.html" data-start data-duration data-track-index data-width data-height>` per moment. The host div is the moment the editor shows and lets the user move; content written straight into the root is not a moment.
- Captions, when requested: a host div the same way, pointing at `compositions/narrator_captions.html`; inside it the editor reads the `.caption-band` element. The service builds that file and `compositions/_words.json` from the pattern you pick; the [AIP captions skill](../aip-captions/SKILL.md) owns the pick and the call. A request without captions does not need these files.
- A static duplicate speaker PIP can be represented inside a moment, but it is not a continuous full-frame/PIP transition or proof of export compatibility: `<video id="<unique>" data-pip-src="public/source.mp4" data-start="<the host's data-start>" data-duration="<the host's data-duration>" data-media-start="<source seconds at that start>" muted playsinline data-volume="0">`, with no `src`. The one exception to the timing table: a PIP's `data-start` is the host's global start, not 0, because the export re-anchors a speaker PIP on a cut project by setting its media offset to that value; the editor maps it through the cut itself.
- Footage other than the recording (a user clip, a stock clip): either a root clip in `index.html`, `<video id="<unique>" class="clip" data-track-index="<n>" src="public/videos/<stem>.mp4" data-start data-duration data-media-start muted playsinline data-volume="0">`, on a track of its own with the moment that frames it (a mask, a frame, a title) drawing over it, or the same tag inside the moment's composition, `<video id="<unique>" class="clip" src="public/videos/<stem>.mp4" data-start="<the host's data-start>" data-duration data-media-start muted playsinline data-volume="0">`, timed on the host's clock like a PIP. The root clip is what the user can move on the timeline; the nested one moves with its moment.
- An element the user should move and restyle as one object carries `data-aip-editable="<token>"` where the token is one of that element's own classes; the editor also treats `.list-item`, `.glass-card`, `.media-card`, `.speaker-pip-frame` and `.item-bar` as such objects. Anything else inside a moment is reachable only as text or image leaves.

For a continuous full-frame/PIP transition, keep one speaker identity and coordinate picture geometry with the window on the root timeline. The optional [PIP example](references/pip-transition.md) covers an uncut single-speaker project only; it is not a verified recipe for cut media or editor camera overrides. Independent effect hosts do not supply cross-scene interpolation automatically.

## A sub-composition file

```html
<template>
  <div data-composition-id="<id>" data-width="W" data-height="H">
    ...content, with its <style> and <script> inside the template...
    <script>
      const tl = gsap.timeline({ paused: true });
      ...
      window.__timelines["<id>"] = tl;
    </script>
  </div>
</template>
```

The inner div's `data-composition-id` equals the host's. Scope styles and element queries to the composition's content so multiple moments can coexist in the same document. Keep the composition root visible at its base pose; animate an inner wrapper or its children, not the composition root or host. The editor mounts only what is inside `<template>`, and the export mounts the template itself: a `<script>` written after `</template>` is not part of the moment in either, so write nothing after `</template>`; the file needs no mount script of its own. Timeline time 0 is the host's `data-start`, and the player seeks the timeline rather than playing it. Create and register the paused timeline synchronously after its DOM exists. Render-critical changes belong on that timeline, not in timers, requestAnimationFrame loops, playback callbacks, or CSS animations. Do not call `tl.play()` or start media playback yourself; the player owns the clock. Keep animation repeats finite and randomness seeded so a seek reaches a deterministic state. The host attributes own the duration and active window; do not add empty tweens to set duration or manually nest the child timeline into the root timeline.

## Timing attributes

| attribute | on | value |
| --- | --- | --- |
| `data-start` | every clip | seconds, relative to the parent composition (a PIP or footage clip inside a composition: the host's global start, see above) |
| `data-duration` | every clip | seconds, the clip's own length |
| `data-track-index` | every clip | integer; clips on one track cannot overlap |
| `data-media-start` | video and audio | offset into the source file, seconds |
| `data-volume` | registered media | playback gain, 0 to 1; does not enroll arbitrary audio in AIP mixing |
| `data-width`, `data-height` | compositions | the canvas, px |

## Preview acceptance

The [AIP skill](../aip/SKILL.md) owns delivery and the no-inspection stopping condition. Keep this contract separate from creative direction. A successful local animation sample or accepted upload does not establish AIP editor or export correctness.
