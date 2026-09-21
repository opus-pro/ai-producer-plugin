---
name: aip-framing
description: "Frame the speaker for an AI Producer project. Read once before authoring the root layout: pick the canvas first, then who owns the frame for each beat (the speaker, the footage, or the canvas), and for each of the three layouts (seat, overlay, and full cover) the forms it offers, where that canvas lets it sit, what it keeps, and how it is built, with the speaker measured, not guessed."
---

# Framing for an AI Producer project

Framing decides who owns the frame for each beat: the speaker, the footage, or the canvas. It is one decision per beat, made from the canvas, the transcript, and the footage, and it is yours. How anything looks (color, corners, shadows, type) is the visual style's; this page owns the choice and the geometry it must keep. The [composition contract](../aip-composition/SKILL.md) owns what the editor and the export read.

Apply the user's brief and the [AI Producer text rules](../aip/SKILL.md#on-screen-text) before choosing a form that contains text. The forms below describe geometry; their label, headline, and statement examples do not authorize extra copy.

## What you decide

1. **The canvas, first.** Read it from the brief's platform: 1080x1920 for Reels, TikTok, and Shorts; 1080x1080 for square feed posts; otherwise the source aspect, usually 1920x1080. The canvas decides which forms and positions each layout has (tables below); a layout drawn for one canvas is not reused on another. Reframe the speaker to fill the canvas rather than letterboxing the source.
2. **The register, per beat.** One of the four in the first table. No register is home base: across a video, seat, overlay, and full cover should appear with roughly even odds, and a plan that leans on one throughout reads as a tic. Content fit outranks balance; a run whose beats all need the speaker keeps them, but each pick is a fresh decision, never a default inherited from the previous beat.
3. **The form, per moment.** Seat, overlay, and full cover each offer a short menu of forms in their chapters below. Name the register and the form in the plan; a different moment may take a different form, and one form held for every beat of its register reads as a template.
4. **The measurement, before you place.** Call `frame_speaker` with every window you will seat, overlay, cut out, or reframe, in as few calls as the limit allows: each window's `start` and `end` on the cut, a `slug`, `matte` (true only for a cutout), and the `slot` the speaker will occupy (the seat's rect, a circle's side twice, an aperture's hole, or the canvas for an overlay, a full-frame reframe, and a cutout). Read the task with `get_task`. Each window in its `result.windows` carries `presence` (skip a seat or an overlay where `seat_ok` is false and a cutout where `matte_ok` is false), `face` and `head` as source fractions, and for the slot `object_position` (paste its `css` onto the seat's `data-pip-src` view, or onto the root clip for a full-frame reframe), `head_in_slot`, and `fits`. When `fits.height` is false, give the slot at least `fits.min_slot_height`; never deepen the crop instead. For a canvas slot, `head_in_slot` is the head's box on the canvas, the area an overlay keeps clear. A cutout window takes and returns more; the [cutout reference](references/cutout.md) owns those fields. The call is free and takes at most 8 windows, with matte windows totalling at most 60 s a call; when the plan has more, split the windows across calls, keep every `slug` unique across them, and read each call's task.
5. **The windows.** A register that shows the speaker is legal only over a window where the speaker is on camera. When the source cuts away to something the creator chose to show, let it play raw rather than covering it.
6. **The caption hide windows.** When a beat's payload fills the caption band, or is a `headline` overlay of the spoken phrase, pass those windows as `hide_intervals` to the caption call; the [dynamic caption skill](../aip-dynamic-caption/SKILL.md) owns that call.

## Registers

| Choose when the beat | register | Rotate away when |
| --- | --- | --- |
| The speaker carries the argument live: transitions, summaries, conditions, emotion, rebuttals, the closing call to action; removing them would read as a cut away | `speaker` (full frame, optionally with a zoom) | a graphic, an interface, or source text needs to be read |
| An example, comparison, process, or object explanation where the speaker should stay present while the payload is drawn around them | `seat` (the speaker moved into a declared shape at a declared position; forms and positions in its chapter) | the speaker is off camera in this window; the payload needs the whole canvas |
| The footage carries the beat and a short note sharpens it: a term labelled as it is spoken, a figure drawn beside the speaker, the opening hook title | `overlay` (footage stays full-bleed and sharp; one payload group at a time) | the text runs past one line, would cross the face, or needs a dimmed backdrop |
| The payload is self-standing and deserves the whole page: a full-scale figure, a photo moment, dense source text, one oversized statement | `full-cover` (the canvas owns the frame; the speaker is covered) | it would hold longer than the sentence it illustrates; return to the speaker after it |

## Video asset defaults

For a portrait canvas, choose the first-draft layout from the video's displayed aspect ratio. These defaults take precedence over register variety and general seat placement; user choices and content readability come first.

- Portrait video: use PIP, with the asset as the main picture and the speaker in a small inset that avoids important subjects, action, and text.
- Landscape video: use a top/bottom split, with the asset above and the speaker in a bottom `stratum`, starting at half the canvas each. Use adjoining panels without floating-card margins.
- Preserve the asset's aspect ratio and important content; adjust panel proportions or inset placement as needed. Avoid redundant titles, frames, and empty margins.

## The three layouts

Seat, overlay, and full cover are written the same way below: what it is, its forms, where each canvas lets it sit, what it keeps, and how it is built. A `speaker` beat needs none of this: it is the root speaker at full frame, and its zoom stays on the root timeline.

## Seat

The speaker moves into a declared shape at a declared position on an opaque ground, and the payload is drawn in the band the seat leaves. Each seated framing declares its shape, position, and resting rect once. Beats that share that framing keep it, and a different moment may take a different framing; two or three seat framings across a video is normal, and one seat held for every seated beat reads as a template. What never happens is re-deriving a rect inside a run to fit a long line or a wider figure: a payload that does not fit the band needs a different framing, not a nudged seat.

### Seat forms

Every seat is one of these shapes at one of the positions its canvas allows. Name the shape and the position in the plan; the numbers follow.

| shape | what it is | choose when |
| --- | --- | --- |
| `card` | a rounded window clear of the frame's edges, an object resting on the ground | the default; examples, comparisons, processes; a payload that reads as a card next to a card |
| `stratum` | the speaker flush to one or more frame edges, a layer of the page rather than an object on it | the payload wants the full width or height above or beside a grounded speaker |
| `circle` | an equal-sided window with `border-radius: 50%`, the head centered in it | a light or personal register; the payload owns the page and the speaker is a presence, not a picture |
| `aperture` | an opaque ground with a hole cut in it; the live speaker shows through the hole | the ground is the design and the speaker is a detail in it; the hole sits on the head, so its position comes from the measured face, never from the layout grid |
| `cutout` | the pop: the room recedes into a full-width card and the speaker, cut free of it, stands proud of the card; the headroom above the head hosts the payload | one beat a video at most, on the strongest line, where the silhouette itself is the design; read the [cutout reference](references/cutout.md) before choosing it |

### Seat positions by canvas

The canvas decides where a seat may sit. A left or right column is a landscape layout; a portrait seat stays horizontally centered with its payload above it except for video-asset PIP.

| canvas | seats that fit | do not use |
| --- | --- | --- |
| portrait 9:16 (1080x1920) | `card` low-centered with the payload above (the default), `card` mid-centered at full width with payload above and below, `stratum` as a bottom band flush to three edges, `circle` low-centered, `aperture` centered on the head | a left or right column at any width: the band beside it is too narrow for a payload and the head reads small, so a portrait payload sits above or below the seat; corner circles below 30% of the width |
| square 1:1 (1080x1080) | `card` low-centered or upper-centered, `stratum` as a bottom or top band, `circle` low-centered or in a lower corner at 30% to 36% of the width, `aperture` centered | side columns; stacked seats taller than half the frame |
| landscape 16:9 (1920x1080) | `card` as a left or right column at 30% to 40% of the width with the payload beside it, `stratum` as a side column flush to three edges, `circle` in a lower corner at 22% to 28% of the height, `aperture` on the head, `card` centered with the payload split to both sides | low-centered cards with the payload above: the band is a thin strip; visuals-above/presenter-below stacks that crop the head to a band |

### What a seat keeps

- **One audible speaker.** The root track-0 video and its paired audio remain the canonical speaker. An editable seated moment uses one muted `data-pip-src` view inside its composition while an opaque ground hides the root picture; it never adds audio or a second independently playing source. This ownership view moves and disappears with the moment, and the editor maps it through the cut.
- **The head stays whole.** Crown to jaw with room to breathe: a seat that cuts the forehead or shaves the chin has failed at its one job. When the head cannot fit, deepen the seat; never choose which edge to sever.
- **Center the head, measured, not guessed.** `object-position` is the `frame_speaker` result's `object_position` for that window and slot, pasted as returned onto the view that shows the speaker: it centers the measured face and holds the crown, jaw and cheeks inside the slot. `50% 50%` is a guess that crops a high-framed head at the crown; a narrow column crops harder, so every shape gets its own slot in the call, and on cut media every speaker clip its own window.
- **The seat is an object on a ground.** For video-asset PIP, the asset fills the ground behind the speaker inset while its important content stays visible. Other seated beats paint an opaque ground across the frame and place the moment-owned speaker view in its seat; an aperture clips that view to the measured hole. In those layouts, nothing tucks under, overlaps into, or straddles the seat to buy room; content low in the band clears the seat's width as well as its top edge.
- **A separate payload lives in the band the seat leaves.** When the layout reserves a payload band, judge fullness and dead space against that band, not the whole frame. Keep text and graphics at least 10% from the band's edges.
- **A seat arrives once per run of beats.** Adjacent beats that share a framing keep the seat where it is: it does not re-enter, re-settle, or re-announce itself; only the payload turns over. A new framing arrives at a beat boundary, either from the full frame or as a morph from the previous seat. An entry shorter than 0.35 s lands the speaker before the eye can follow; a monotonic ease (no back, elastic, or bounce) keeps the crop from overshooting the frame.

### How a seat is built

- Every `seat` move owned by a visual moment lives inside that moment's paused child timeline. Put a muted `data-pip-src="public/source.mp4"` video in a `.speaker-pip-frame`, keep its global start and duration aligned with the host, and set its media start to the source time at the host's anchor. The composition contract's [editable speaker PIP](../aip-composition/references/pip-transition.md) is the single source for the snippet.
- Animate the frame's box (`left`, `top`, `width`, `height`), crop (`object-position` with `object-fit: cover`) and corner radius together over the same interval. A circle uses equal sides and `borderRadius: "50%"`; an aperture clips the same moment-owned view to its measured hole. The opaque composition ground hides the unchanged root picture.
- Never couple an independently editable host to absolute-time speaker geometry on `finecut-root`. The editor moves and deletes the host and its child content as one unit, but it does not discover or rewrite unrelated GSAP tweens at the old global time.

## Overlay

The footage owns the frame and one payload rides it. The root speaker keeps playing full-bleed and sharp underneath, and the moment draws only what the payload needs: no page, no wash, no copy of the source. An element that needs a dimmed backdrop or more than one line of text is a full cover or a seat instead.

### Overlay forms

Every overlay is one of these forms. Name the form and where it sits in the plan.

| form | what it is | choose when |
| --- | --- | --- |
| `annotation` | drawn graphics, a short label, or an image placed in the area clear of the head, each element bedded on a plate, stroke, or shadow so it survives arbitrary footage | a term labelled as it is spoken, a figure or an object drawn beside the speaker, a quick object explanation around the presenter |
| `headline` | the phrase just spoken, drawn big as the beat's whole payload, with one accent: one lifted word, or one drawn mark riding the line, never both | the opening hook title; the one line a beat turns on; not a line that needs two sentences (that is two beats), and never a second reading line beside the captions |

### Overlay positions by canvas

The measured head decides where an overlay may sit: the payload stays outside `head_in_slot` for that window, with room to breathe around it.

| canvas | overlays that fit | do not use |
| --- | --- | --- |
| portrait 9:16 (1080x1920) | `headline` in the lower third (the default), or above the head only when the head box leaves real headroom; `annotation` in the band above or below the head at full width | anything beside the face: the flank is too narrow to read, so a portrait overlay sits above or below the head |
| square 1:1 (1080x1080) | `headline` in the lower third; `annotation` beside the head on the flank the head box leaves open, or below the head | payloads on both flanks at once; a payload that crosses the head box |
| landscape 16:9 (1920x1080) | `headline` in the lower third or on the open flank; `annotation` beside the head on the flank an off-center face leaves open | a band above the head: it is a thin strip; a payload that crosses the head box |

### What an overlay keeps

- **The overlay rides sharp footage.** The composition never pauses, scales, or reframes the source under an overlay; ink polarity reads the footage's tone where the text lands, with a plate, stroke, or shadow bed where the ground is mixed.
- **The head stays clear.** Name the overlay's window in the `frame_speaker` call with the canvas as its `slot`, and keep every text, plate, and image outside the returned `head_in_slot`; a thin connector line may reach past it toward what it points at. On a reframed canvas the box holds while the root clip carries the same result's `object_position`. The box describes the unzoomed frame: when a root zoom runs during the overlay's window, clear the box as it stands at the zoom's largest scale in that window, each edge pushed away from the zoom's origin by that scale, or end the zoom before the overlay starts.
- **Payloads take turns.** An overlay holds one payload group at a time; the next arrives only as the previous yields. Competing groups on screen together read as clutter over the footage.
- **The payload keeps its margins.** Keep text and graphics at least 10% from the canvas edges, and shorten the copy rather than shrinking the type.

### How an overlay is built

- An overlay is an ordinary visual moment whose composition stays transparent: no `background` on the composition root or on any full-frame wrapper, the payload inside one positioned wrapper, and its entrance and exit on the moment's own paused child timeline. The composition contract's [editable speaker PIP](../aip-composition/references/pip-transition.md) example minus its ground and its speaker view is an overlay.
- It embeds no video: no `data-pip-src` view and no copy of the source, because the root speaker underneath is the picture. Leave the root speaker's geometry to the root timeline.
- Pass the window as `hide_intervals` to the caption call when the payload lands in the caption band, and for every `headline` wherever it sits: the captions would otherwise repeat the phrase the headline draws.

## Full cover

The canvas owns the frame. The moment paints one opaque ground across the whole canvas and everything sits on it; nobody is seated, and the root speaker keeps playing underneath, unseen and still heard. A full cover is for a payload that stands on its own, and a beat that wants the speaker present is a seat instead.

### Full-cover forms

Every full cover is one of these forms. Name the form in the plan.

| form | what it is | choose when |
| --- | --- | --- |
| `figure` | a drawn diagram, chart, or mechanism at full scale | a relationship, a process, or a number that needs the whole page to read |
| `photo` | a real image staged on the ground as content, with at most one short label; a video asset follows the video asset defaults above instead | a product, a place, an interface, or an event the speech names and a real asset shows |
| `statement` | one oversized line, a few words at the largest size the page allows | the single claim the video turns on |
| `source-text` | a crop of dense source material, enlarged until the relevant detail reads, without extra headings or nested frames | a quote, a document, or a screen of text the speaker refers to |

### Full-cover positions by canvas

The canvas decides how a page is laid out. Center the focal point, and simplify the content to keep it large.

| canvas | pages that fit | do not use |
| --- | --- | --- |
| portrait 9:16 (1080x1920) | one centered focal element, or a vertical stack of two: the figure above and its one-line label below | side-by-side columns: each is too narrow to read |
| square 1:1 (1080x1080) | one centered focal element, or a stack of two rows | columns narrower than half the frame; more than two rows |
| landscape 16:9 (1920x1080) | one centered focal element, or two columns side by side: a figure and its label, a before and an after | a vertical stack of three or more rows: each is a thin strip |

### What a full cover keeps

- **One ground, wholly owned.** The composition paints one opaque ground across the whole canvas, and everything sits on it. An image is staged on the ground as content, never stretched into the ground itself.
- **Nobody is seated.** No `data-pip-src` view, no window onto the speaker, and no copy of the source. The cutout is the one exception, and it is a seat form with its own [reference](references/cutout.md).
- **The full cover releases the frame.** Cover, then switch visuals or return to the speaker; the speaker underneath does not move during a full cover. It holds no longer than the sentence it illustrates.
- **The payload keeps its margins.** Keep text and graphics at least 10% from the canvas edges, and use at most three font sizes on the page.

### How a full cover is built

- A full cover is an ordinary visual moment whose composition root paints the opaque ground (`position: absolute; inset: 0` with a solid `background`), with the payload's entrance and exit on the moment's own paused child timeline. The composition contract's [editable speaker PIP](../aip-composition/references/pip-transition.md) example minus its speaker view is a full cover.
- It embeds no speaker view. The root speaker and its audio keep playing underneath at their ordinary geometry; release a root zoom before the full cover starts.
- When the payload fills the caption band, pass the window as `hide_intervals` to the caption call. Reference every image through `src` so the hand-back check sees it.

## The speaker beat

- Root zooms on a `speaker` beat that is not owned by a visual moment may remain root tweens on every active track-0 speaker clip (`#stage > video[data-track-index="0"]`). Release that camera treatment before the next seated moment; a root zoom never lands inside a seat.
