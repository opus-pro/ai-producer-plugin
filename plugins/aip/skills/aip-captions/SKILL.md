---
name: aip-captions
description: "Pick the caption style for an AI Producer project. Read when the brief asks for captions or subtitles: how to choose one of the eight subtitle patterns from the video's content, which knobs the host controls, and the one call that has the service build the caption layer."
---

# Captions for an AIP project

The caption layer is one composition, `compositions/narrator_captions.html`, with `compositions/transcript-src.json` beside it. The service builds both from a subtitle pattern you pick and the project's transcript; you do not write caption HTML, CSS, or word data. Your job is the pick and its few knobs, made from what you know about the video.

## What you decide

1. **The pattern.** One per video, from the table below. Read the transcript at `get_transcript` with `detail: segments` (a tenth of the bytes) for register and pace, and look at the source for brightness, contrast, where the face sits, and whether a brand accent exists. Those are the inputs the table keys on.
2. **Emphasis words** (optional). At most one per phrase: the payload word a viewer should feel land. Take `word_id` values from `get_transcript` with `detail: words`. Every pattern has a designed treatment for an emphasis word; a phrase without one renders in the quiet register. Leave the list out and the service picks them with one caption-plan call.
3. **Position** (optional). Leave `position` out unless the brief places the captions; the service then uses the pattern's default. If you set it, it is the band's vertical anchor as a percent of frame height: 50 is mid-frame, 80 is the lowest the text-safe zone allows, and the service clamps anything past that, tighter for a pattern whose block grows downward. `placement` is `adaptive` (default: the band moves off the speaker where the project's person samples exist; the task result's `placement` says whether it did) or `fixed`. Horizontal composition is part of each pattern's design and is not a knob; change the pattern to change it.
4. **Hide windows** (optional). `hide_intervals` is a list of `{start, end}` seconds where the band stays hidden, typically your visual moments' windows when a moment fills the caption band. Empty keeps captions on for the whole video.

## The call

Call `build_captions` with `project_id`, `caption_style` (the pattern), and any of `position`, `placement`, `hide_intervals`, `emphasis_word_ids`. It returns a task; read it with `get_task` (its `poll_args` say when). The finished task's `result` names the two files the service staged (`staged`), the pattern and position it baked, the emphasis it used as `word_id` values, and `host_div`, the one element for `index.html`:

```html
<div
  class="visual-host clip"
  data-composition-id="narrator-captions"
  data-composition-src="compositions/narrator_captions.html"
  data-start="0"
  data-duration="<total s>"
  data-track-index="<n>"
  data-width="W"
  data-height="H"
></div>
```

Place `host_div` as written (its duration and canvas come from the root you committed; placeholders mean commit the root first) inside the root, last, on its own track, then upload your tree and `commit_workspace` as usual: the staged caption files promote with your round, and the editor finds the running caption by the `.caption-band` element inside that host. Do not write `compositions/narrator_captions.html` or `compositions/transcript-src.json` yourself; a file you stage at either path replaces the service's. Hand back the editor link; there is no local inspection step. One `build_captions` run is one flat charge, whether or not you named the emphasis words.

## Patterns

| Choose when the video is                                                                                                                      | pattern             | Rotate away when                                                                       |
| --------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- | -------------------------------------------------------------------------------------- |
| A tutorial or a punchy talking head where each sentence should feel hand-cut; face outside the 50-73% band                                    | `blur-ladder`       | captions should be a quiet legibility layer; the footage is busy                       |
| A piece where the running caption is the design itself; darkish source; face outside the 50-68% band                                          | `editorial-stack`   | captions should stay quiet under the speaker or under visual moments                   |
| A dark speaker cut against bright b-roll, where the caption should read as grade rather than overlay; real tonal contrast in the caption band | `inverted-stack`    | flat mid-tone footage                                                                  |
| **The default**: every sentence wants a visible payoff beat; a brand accent exists (the only pattern that colors caption type)                | `lead-in-flare`     | delivery so fast that a big tail every sentence lags the voice                         |
| Dense, fast, or information-heavy; captions should stay uniform under the speaker                                                             | `pace-adaptive`     | a punchier per-word emphasis or a calmer whole-line read fits better                   |
| Creator confessional, story-time, a scrappy hand-made brand register                                                                          | `scribble-subtitle` | a formal or corporate register; dense small on-screen text                             |
| Short imperative narration, step-throughs, hype delivery, where the caption is a beat                                                         | `solo-word-punch`   | reflective or information-dense narration                                              |
| Vlogs, hot takes, sticker energy, loud and playful; a real brand accent                                                                       | `tilt-slam`         | a formal or corporate register; dense small on-screen text; captions should stay quiet |

One pattern per video. The pick is yours; the pattern's typography, motion, and layout are the service's.

## Local test period (remove before contributing)

While `build_captions` is not on this server's tool list: do everything above up to the call, then end the caption step by stating the exact call you would have made, with `caption_style`, the emphasis `word_id` values with their text, `position`, `placement`, and `hide_intervals`, and one sentence on why that pattern fits this video. Continue the rest of the project without a caption layer.
