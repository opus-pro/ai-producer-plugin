---
name: aip-framing
description: "Frame the speaker for an AI Producer project. Read once before authoring the root layout: pick the canvas first, then who owns the frame for each beat (the speaker, the footage, or the canvas), which seat shapes and positions that canvas allows, the geometry a speaker frame keeps, and the root-timeline mechanism that moves the speaker."
---

# Framing for an AIP project

Framing decides who owns the frame for each beat: the speaker, the footage, or the canvas. It is one decision per beat, made from the canvas, the transcript, and the footage, and it is yours. How anything looks (color, corners, shadows, type) is the visual style's; this page owns the choice and the geometry it must keep. The [composition contract](../aip-composition/SKILL.md) owns what the editor and the export read.

## What you decide

1. **The canvas, first.** Read it from the brief's platform: 1080x1920 for Reels, TikTok, and Shorts; 1080x1080 for square feed posts; otherwise the source aspect, usually 1920x1080. The canvas decides which seat shapes and positions exist (tables below); a layout drawn for one canvas is not reused on another. Reframe the speaker to fill the canvas rather than letterboxing the source.
2. **The register, per beat.** One of the four in the first table. No register is home base: across a video, seat, overlay, and full cover should appear with roughly even odds, and a plan that leans on one throughout reads as a tic. Content fit outranks balance; a run whose beats all need the speaker keeps them, but each pick is a fresh decision, never a default inherited from the previous beat.
3. **The framing, per moment; its rect, once per framing.** Each seated framing declares its shape, position, and resting rect once. Beats that share that framing keep it, and a different moment may take a different framing; two or three seat framings across a video is normal, and one seat held for every seated beat reads as a template. What never happens is re-deriving a rect inside a run to fit a long line or a wider figure: a payload that does not fit the band needs a different framing, not a nudged seat.
4. **The windows.** A register that shows the speaker is legal only over a window where the speaker is on camera. When the source cuts away to something the creator chose to show, let it play raw rather than covering it.
5. **The caption hide windows.** When a beat's payload fills the caption band, pass those windows as `hide_intervals` to the caption call; the [captions skill](../aip-captions/SKILL.md) owns that call.

## Registers

| Choose when the beat | register | Rotate away when |
| --- | --- | --- |
| The speaker carries the argument live: transitions, summaries, conditions, emotion, rebuttals, the closing call to action; removing them would read as a cut away | `speaker` (full frame, optionally with a zoom) | a graphic, an interface, or source text needs to be read |
| An example, comparison, process, or object explanation where the speaker should stay present while the payload is drawn around them | `seat` (the speaker moved into a declared shape at a declared position; shapes and positions below) | the speaker is off camera in this window; the payload needs the whole canvas |
| The footage carries the beat and a short note sharpens it: a term labelled as it is spoken, a figure drawn beside the speaker, the opening hook title | `overlay` (footage stays full-bleed and sharp; one payload group at a time) | the text runs past one line, would cross the face, or needs a dimmed backdrop |
| The payload is self-standing and deserves the whole page: a full-scale figure, a photo moment, dense source text, one oversized statement | `full-cover` (the canvas owns the frame; the speaker is covered) | it would hold longer than the sentence it illustrates; return to the speaker after it |

## Seat shapes

Every seat is one of these shapes at one of the positions its canvas allows. Name the shape and the position in the plan; the numbers follow.

| shape | what it is | choose when |
| --- | --- | --- |
| `card` | a rounded window clear of the frame's edges, an object resting on the ground | the default; examples, comparisons, processes; a payload that reads as a card next to a card |
| `stratum` | the speaker flush to one or more frame edges, a layer of the page rather than an object on it | the payload wants the full width or height above or beside a grounded speaker |
| `circle` | an equal-sided window with `border-radius: 50%`, the head centered in it | a light or personal register; the payload owns the page and the speaker is a presence, not a picture |
| `aperture` | an opaque ground with a hole cut in it; the live speaker shows through the hole | the ground is the design and the speaker is a detail in it; the hole sits on the head, so its position comes from the measured face, never from the layout grid |

A cutout (the speaker's silhouette standing on the ground) needs matted footage the service does not provide on this path; do not attempt it with a rectangle.

## Positions by canvas

The canvas decides where a seat may sit. A left or right column is a landscape layout; a portrait seat stays horizontally centered with its payload above it.

| canvas | seats that fit | do not use |
| --- | --- | --- |
| portrait 9:16 (1080x1920) | `card` low-centered with the payload above (the default), `card` mid-centered at full width with payload above and below, `stratum` as a bottom band flush to three edges, `circle` low-centered, `aperture` centered on the head | left or right columns: under 40% of the width the head reads tiny and the band beside it is too narrow for a payload; corner circles below 30% of the width |
| square 1:1 (1080x1080) | `card` low-centered or upper-centered, `stratum` as a bottom or top band, `circle` low-centered or in a lower corner at 30% to 36% of the width, `aperture` centered | side columns; stacked seats taller than half the frame |
| landscape 16:9 (1920x1080) | `card` as a left or right column at 30% to 40% of the width with the payload beside it, `stratum` as a side column flush to three edges, `circle` in a lower corner at 22% to 28% of the height, `aperture` on the head, `card` centered with the payload split to both sides | low-centered cards with the payload above: the band is a thin strip; visuals-above/presenter-below stacks that crop the head to a band |

Overlay forms follow the same rule: a headline sits in the lower third on every canvas; an annotation beside the face needs the width of a landscape or square frame, and on portrait it sits above or below the face instead.

## Geometry a speaker frame keeps

- **One speaker identity.** The speaker is the root track-0 video; a layout change moves that element and never adds a second copy of the footage inside a composition. A static duplicate inside a moment is a picture of the speaker, not a frame, and on cut media it drifts from the audible one.
- **The head stays whole.** Crown to jaw with room to breathe: a seat that cuts the forehead or shaves the chin has failed at its one job. When the head cannot fit, deepen the seat; never choose which edge to sever.
- **Center the head, measured, not guessed.** `object-position` comes from where the face sits in this footage: read it from representative source frames (input-media analysis is allowed) and keep it per speaker clip on cut media. `50% 50%` is a guess that crops a high-framed head at the crown; a narrow column crops harder, so measure again for each shape.
- **The seat is an object on a ground.** A seated beat's composition paints an opaque ground across the frame and leaves the seat region clear so the live speaker shows through; an aperture paints the ground over the speaker with the hole cut out. Nothing tucks under, overlaps into, or straddles the seat to buy room; content low in the band clears the seat's width as well as its top edge.
- **The payload lives in the band the seat leaves.** Judge fullness and dead space against that band, not the whole frame. Keep text and graphics at least 10% from the band's edges.
- **A seat arrives once per run of beats.** Adjacent beats that share a framing keep the seat where it is: it does not re-enter, re-settle, or re-announce itself; only the payload turns over. A new framing arrives at a beat boundary, either from the full frame or as a morph from the previous seat. An entry shorter than 0.35 s lands the speaker before the eye can follow; a monotonic ease (no back, elastic, or bounce) keeps the crop from overshooting the frame.
- **The overlay rides sharp footage.** The composition never pauses, scales, or reframes the source under an overlay; ink polarity reads the footage's tone where the text lands, with a plate, stroke, or shadow bed where the ground is mixed.
- **The full cover releases the frame.** Cover, then switch visuals or return to the speaker; the speaker underneath does not move during a full cover.

## The mechanism

- Every speaker move lives on the root paused timeline `finecut-root`, as tweens on every track-0 speaker clip (`#stage > video[data-track-index="0"]`), never inside a composition: a sub-composition cannot reach the root speaker at export, and a cut project stages one clip per kept span, so a single-id tween moves a hidden sibling while the visible clip stays put.
- One tween moves the box (`left`, `top`, `width`, `height`), the crop (`object-position` with `object-fit: cover`) and the corner radius together over the same interval; a circle is the same tween with equal sides and `borderRadius: "50%"`; an aperture moves the speaker behind the ground's hole with the same tween. A matching tween returns to full frame before the next speaker beat. The code recipe is the composition contract's [continuous speaker transition](../aip-composition/references/pip-transition.md); it stays the single source for that snippet.
- Root tween times are the beats' own `data-start` values written into the tween positions, so a moment moved later in the editor does not move its seat with it: when you retime a moment, retime its framing tweens in the same edit.
- Root zooms on a `speaker` beat are root tweens on the same clips (`scale` about a `transform-origin` on the head), released before the next framing tween begins; a zoom never lands inside a seat.
