---
name: aip-framing
description: "Frame the speaker for an AI Producer project. Read once before authoring the root layout: pick the canvas first, then who owns the frame for each beat (the speaker, the footage, or the canvas), and for each of the three layouts (seat, overlay, and full cover) the forms it offers, where that canvas lets it sit, what it keeps, and how it is built, with the speaker measured, not guessed."
---

# Framing for an AI Producer project

Framing decides, per beat, who owns the frame (the speaker, the footage, or the canvas), from the canvas, the transcript, and the footage. How anything looks (color, corners, shadows, type) is the visual style's; this page owns each layout's forms and the geometry it must keep.

Apply the user's brief and the [AI Producer text rules](../aip/SKILL.md#on-screen-text) before choosing a form that contains text: the forms below describe geometry, and their label, headline, and statement examples do not authorize extra copy.

## What you decide

1. **The canvas, first.** A project whose canvas is 4:5 (a 4:5 source) is 1080x1350 whatever platform the brief names. Otherwise read it from the brief's platform: 1080x1920 for Reels, TikTok, and Shorts; 1080x1080 for square feed posts; otherwise the source aspect, usually 1920x1080. The canvas decides which forms and positions each layout has (tables below); a layout drawn for one canvas is not reused on another.
2. **The register, per beat.** One of the four in the table below.
3. **The form, per moment.** Seat, overlay, and full cover each offer a short menu of forms in their chapters below. Name the register and the form in the plan.
4. **The measurement, before you place.** Call `frame_speaker` with every window you will seat, overlay, cut out, or reframe, in as few calls as the limit allows: each window's `start` and `end` on the cut, a `slug`, `matte` (true only for a cutout), and the `slot` the speaker will occupy (the seat's rect, a circle's side twice, an aperture's hole, or the canvas for an overlay, a full-frame reframe, and a cutout). Read the task with `get_task`. Each window in its `result.windows` carries `presence` (skip a seat or an overlay where `seat_ok` is false and a cutout where `matte_ok` is false), `face` and `head` as source fractions, and for the slot `object_position` (paste its `css` onto the seat's `data-pip-src` view, or onto the root clip for a full-frame reframe), `head_in_slot`, and `fits`. `fits.height` false means the slot is too wide for the source's aspect at that height, so `object-fit: cover` draws the head at the slot's width: narrow the slot at the same height (the head shrinks with it) or give it at least `fits.min_slot_height`, and measure the revised slot before placing it. If `min_slot_height` did not fall, the slot is height-bound and only deepening helps; a slot narrowed until `fits.width` turns false has gone too far. Never deepen the crop instead. For a canvas slot, `head_in_slot` is the head's box on the canvas, the area an overlay keeps clear. A cutout window takes and returns more, as the [cutout reference](references/cutout.md) says. The call is free; spread more windows than one call takes across calls, every `slug` unique across them, and read each call's task.
5. **The windows.** A register that shows the speaker is legal only over a window where the speaker is on camera. When the source cuts away to something the creator chose to show, let it play raw rather than covering it.
6. **The caption band, per moment.** Captions stay on during a visual moment: the moment gives way to the band, not the reverse. Place the cues that play during each moment where its layout chapter's `Where the caption sits` puts the band, as the [dynamic caption skill](../aip-dynamic-caption/SKILL.md) says, in a dark type only over a ground the composition painted light; that skill names the moments no cue plays under. Each cue takes its own position, so one video holds a PIP and a full cover at once.

## Registers

| register | what it is |
| --- | --- |
| `speaker` | the root speaker at full frame, optionally with a zoom or filter effect host |
| `seat` | the speaker moved into a declared shape at a declared position on an opaque ground, with the payload drawn in the band the seat leaves; forms and positions in its chapter |
| `overlay` | the footage stays full-bleed and sharp, and one payload group at a time rides it in the area the measured head leaves clear |
| `full-cover` | the canvas owns the frame: one opaque ground across the whole page carries the payload, and the speaker is covered but still heard |

## Video assets

A video asset the speech puts on screen is seated in one of two layouts. Both are seats and keep everything a seat keeps.

- PIP: the asset is the ground, and the speaker is a small inset placed clear of the asset's important subjects, action, and text.
- Top/bottom split: the asset above, the speaker in a low-centered `card` below it. The asset may run the full width; the card keeps its side margins, because with portrait footage a full-width speaker panel draws the head at full source scale and crops a close-up.
- The asset keeps its aspect ratio and its important content; panel proportions and inset placement adjust to it.
- The caption band sits between the asset and the speaker panel, as under any portrait seat (`Where the caption sits under a seat`); the panel starts below the band.

## Seat

Each seated framing declares its shape, position, and resting rect once; beats that share it keep it, and a different moment may declare another. Never re-derive a rect inside a run to fit a long line or a wider figure: a payload that does not fit the band needs a different framing, not a nudged seat.

### Seat forms

Every seat is one of these shapes at one of the positions its canvas allows. Name the shape and the position in the plan; the numbers follow.

| shape | what it is |
| --- | --- |
| `card` | a rounded window clear of the frame's edges, an object resting on the ground |
| `stratum` | the speaker flush to one or more frame edges, a layer of the page rather than an object on it |
| `circle` | an equal-sided window with `border-radius: 50%`, the head centered in it |
| `aperture` | an opaque ground with a hole cut in it; the live speaker shows through the hole, which sits on the head, so its position comes from the measured face, never from the layout grid |
| `cutout` | the pop: the room recedes into a full-width card and the speaker, cut free of it, stands proud of the card; the headroom above the head hosts the payload; the [cutout reference](references/cutout.md) owns its measurement and build |

### Seat positions by canvas

The canvas decides where a seat may sit. A left or right column is a landscape layout; a portrait seat stays horizontally centered and clear of both side edges, with its payload above it, except for video-asset PIP and the cutout, whose full-width card is measured by `frame_speaker` and owned by its reference.

| canvas | seats that fit | do not use |
| --- | --- | --- |
| portrait 9:16 (1080x1920) | `card` low-centered at about 78% of the width with the payload above, `card` mid-centered at the same width with payload above and below, `circle` low-centered, `aperture` centered on the head | a full-width `card` or `stratum` speaker window (the cutout's card is the one exception: its silhouette stands above the card, measured): with portrait footage a seat as wide as the canvas draws the head at full source scale, so a close-up head needs more than half the canvas or loses its crown and chin; a left or right column at any width: the band beside it is too narrow for a payload and the head reads small, so a portrait payload sits above or below the seat; corner circles below 30% of the width |
| portrait 4:5 (1080x1350) | the portrait 9:16 seats at about 70% of their 9:16 height: `card` low-centered at about 78% of the width with the payload above, `circle` low-centered, `aperture` centered on the head | everything portrait 9:16 rules out; a seat with payload both above and below it, which leaves the band no room on the shorter frame |
| square 1:1 (1080x1080) | `card` low-centered or upper-centered, `stratum` as a bottom or top band, `circle` low-centered or in a lower corner at 30% to 36% of the width, `aperture` centered | side columns; stacked seats taller than half the frame |
| landscape 16:9 (1920x1080) | `card` as a left or right column at 30% to 40% of the width with the payload beside it, `stratum` as a side column flush to three edges, `circle` in a lower corner at 22% to 28% of the height, `aperture` on the head, `card` centered with the payload split to both sides | low-centered cards with the payload above: the band is a thin strip; visuals-above/presenter-below stacks that crop the head to a band |

### Where the caption sits under a seat

Look at the seat the speaker actually occupies, not the source frame: measure the head in the seat, then give the band its own region outside the seat and outside the payload. The whole-video caption never shrinks into the seat, and a seat that cannot leave the band its head intact takes another framing (narrow it, or change register). The pixel rows below are the 1080x1920 and 1920x1080 zoning the design settled on, and the 4:5 rows are the portrait ones scaled to 1350 tall; a cue is centred on the percent of the frame height each row gives.

| canvas | the band | the payload | the seat |
| --- | --- | --- | --- |
| portrait 9:16 | between the payload and the seat, about y 920 to 1110, centred at 53% | above the band, about y 265 to 770 | below the band, from about y 1240 (a `card` about 780x460) |
| portrait 4:5 | between the payload and the seat, about y 650 to 780, centred at 53% | above the band, about y 185 to 540 | below the band, from about y 870 (a `card` about 780x320) |
| landscape 16:9 | the bottom band, about y 800 to 890, centred at 78%, one row | beside the seat, ending above y 700 | a side column ending above y 700 |

### What a seat keeps

- **One audible speaker.** The root track-0 video and its paired audio remain the canonical speaker. An editable seated moment uses one muted `data-pip-src` view inside its composition while an opaque ground hides the root picture; it never adds audio or a second independently playing source. This ownership view moves and disappears with the moment, and the editor maps it through the cut.
- **The head stays whole.** Crown to jaw with room to breathe; a seat never cuts the forehead or shaves the chin. When the head cannot fit, narrow or deepen the seat; never choose which edge to sever. The view fills its seat at cover scale and no further: a scale on the view draws the head larger than the measurement saw.
- **Center the head, measured, not guessed.** Paste the `frame_speaker` result's `object_position` for that window and slot, as returned, onto the view that shows the speaker; `50% 50%` is a guess that crops a high-framed head at the crown. Every shape gets its own slot in the call, and on cut media every speaker clip its own window.
- **The seat is an object on a ground.** A seated beat paints an opaque ground across the frame and places the moment-owned speaker view in its seat (an aperture clips that view to the measured hole); nothing tucks under, overlaps into, or straddles the seat to buy room, and content low in the band clears the seat's width as well as its top edge. Video-asset PIP is the exception: its ground is the asset (`Video assets` above).
- **A seat arrives once per run of beats.** Adjacent beats that share a framing keep the seat where it is: it does not re-enter, re-settle, or re-announce itself; only the payload turns over. A new framing arrives at a beat boundary, either from the full frame or as a morph from the previous seat.

### How a seat is built

- Every `seat` move owned by a visual moment lives inside that moment's paused child timeline, wired as the composition contract's [editable speaker PIP](../aip-composition/references/pip-transition.md) shows.
- Animate the frame's box (`left`, `top`, `width`, `height`), crop (`object-position` with `object-fit: cover`) and corner radius together over the same interval.
- Never couple an independently editable host to absolute-time speaker geometry on `finecut-root`: the editor moves and deletes the host and its child content as one unit, but never rewrites unrelated GSAP tweens at the old global time.

## Overlay

The footage owns the frame and one payload rides it. The root speaker keeps playing full-bleed and sharp underneath, and the moment draws only what the payload needs: no page, no wash, no copy of the source.

### Overlay forms

Every overlay is one of these forms. Name the form and where it sits in the plan.

| form | what it is |
| --- | --- |
| `annotation` | drawn graphics, a short label, or an image placed in the area clear of the head |
| `headline` | the phrase just spoken, drawn big as the beat's whole payload; no caption plays under it, because the captions would otherwise repeat the line |

### Overlay positions by canvas

The measured head decides where an overlay may sit: the payload stays outside `head_in_slot` for that window, with room to breathe around it.

| canvas | overlays that fit | do not use |
| --- | --- | --- |
| portrait 9:16 (1080x1920) | `headline` in the lower third, or above the head where the head box leaves real headroom; `annotation` in the band above or below the head at full width | anything beside the face: the flank is too narrow to read, so a portrait overlay sits above or below the head |
| portrait 4:5 (1080x1350) | as portrait 9:16 | as portrait 9:16 |
| square 1:1 (1080x1080) | `headline` in the lower third; `annotation` beside the head on the flank the head box leaves open, or below the head | payloads on both flanks at once; a payload that crosses the head box |
| landscape 16:9 (1920x1080) | `headline` in the lower third or on the open flank; `annotation` beside the head on the flank an off-center face leaves open | a band above the head: it is a thin strip; a payload that crosses the head box |

### Where the caption sits under an overlay

The head, the payload, and the band avoid one another. The footage stays full-bleed; the payload takes the empty region outside the head box, and the band takes another band of its own, so the payload can animate without the caption following it. Only avoiding the face is not enough: the band must not cross the payload's key change, and the payload must not enter the band as it moves. When only one empty region exists, shrink or move the payload, or change to a seat or a full cover; the caption never follows the face word by word.

| canvas | the band | the payload |
| --- | --- | --- |
| portrait 9:16 | the lower third, about y 1340 to 1530, centred at 75% | below the head, about y 860 to 1250 |
| portrait 4:5 | the lower third, about y 940 to 1075, centred at 75% | below the head, about y 605 to 880 |
| landscape 16:9 | the bottom band, about y 800 to 890, centred at 78%, one row | the open flank, ending above y 620 |

### What an overlay keeps

- **The overlay rides sharp footage.** The composition never pauses, scales, or reframes the source under an overlay.
- **The head stays clear.** Measure the overlay's window with the canvas as its `slot`, and keep every text, plate, and image outside the returned `head_in_slot`; only a thin connector line may reach past it toward what it points at. On a reframed canvas the box holds while the root clip carries the same result's `object_position`. The box is the unzoomed frame's: under a zoom effect in the overlay's window, clear the box at the zoom's largest scale there, each edge pushed away from the zoom's origin by that scale, or end the zoom before the overlay starts.
- **Payloads take turns.** An overlay holds one payload group at a time; the next arrives only as the previous yields.

### How an overlay is built

- An overlay is an ordinary visual moment whose composition stays transparent: no `background` on the composition root or on any full-frame wrapper, the payload inside one positioned wrapper, and its entrance and exit on the moment's own paused child timeline. The composition contract's [editable speaker PIP](../aip-composition/references/pip-transition.md) example minus its ground and its speaker view is an overlay.
- It embeds no video: no `data-pip-src` view and no copy of the source, because the root speaker underneath is the picture. Leave the root speaker's geometry to the root timeline.

## Full cover

The canvas owns the frame. The moment paints one opaque ground across the whole canvas and everything sits on it; nobody is seated, and the root speaker keeps playing underneath, unseen and still heard.

### Full-cover forms

Every full cover is one of these forms. Name the form in the plan.

| form | what it is |
| --- | --- |
| `figure` | a drawn diagram, chart, or mechanism at full scale |
| `scene` | an immersive 3D object or space - a Three.js scene or a CSS 3D stage - that carries the idea itself at full scale, with the camera moving through or around it |
| `photo` | a real image staged on the ground as content; a video asset is seated as `Video assets` above says, not covered |
| `statement` | one oversized line, a few words at the largest size the page allows |
| `source-text` | a crop of dense source material, enlarged until the relevant detail reads |

### Full-cover positions by canvas

The canvas decides how a page is laid out.

| canvas | pages that fit | do not use |
| --- | --- | --- |
| portrait 9:16 (1080x1920) | one centered focal element, or a vertical stack of two: the figure above and its one-line label below | side-by-side columns: each is too narrow to read |
| portrait 4:5 (1080x1350) | one centered focal element, or a vertical stack of two: the figure above and its one-line label below | side-by-side columns: each is too narrow to read |
| square 1:1 (1080x1080) | one centered focal element, or a stack of two rows | columns narrower than half the frame; more than two rows |
| landscape 16:9 (1920x1080) | one centered focal element, or two columns side by side: a figure and its label, a before and an after | a vertical stack of three or more rows: each is a thin strip |

### Where the caption sits on a full cover

Settle the band first, then compose the payload in the space it leaves: the animation recentres, scales, and moves inside that space, and the band must not cross an arrow's end, a compared result, a value, or a legend through the whole entry and exit. Check the frames where the speaker shows briefly at the switch on the composition's own page before publishing, never in the generated preview. Only where the ground under the band is one this composition painted light (a pale panel, a light style the brief asked for) give the cues there a type colour that contrasts with that ground (`#0a0c12` on a pale ground); the default black canvas keeps the white type, so a dark type is a per-moment call, never a full-cover default, and never over footage or a photo, which move under the words. A `statement` hides the captions, and so does a `source-text` or `photo` whose relevant detail must occupy the band and cannot move up.

| canvas | the band | the payload |
| --- | --- | --- |
| portrait 9:16 | about y 1340 to 1530, centred at 75% | recentred above the band, about y 360 to 1060 |
| portrait 4:5 | about y 940 to 1075, centred at 75% | recentred above the band, about y 255 to 745 |
| landscape 16:9 | the bottom band, about y 800 to 890, centred at 78%, one row | above the band, about y 160 to 630 |

### What a full cover keeps

- **One ground, wholly owned.** The composition paints one opaque ground across the whole canvas, and everything sits on it. An image is staged on the ground as content, never stretched into the ground itself.
- **Nobody is seated.** No `data-pip-src` view, no window onto the speaker, and no copy of the source. The cutout is the one exception, and it is a seat form with its own [reference](references/cutout.md).
- **The speaker underneath does not move.** The root speaker keeps its geometry for the whole cover; a zoom effect ends before the cover starts.

### How a full cover is built

- A full cover is an ordinary visual moment whose composition root paints the opaque ground (`position: absolute; inset: 0` with a solid `background`), with the payload's entrance and exit on the moment's own paused child timeline. The composition contract's [editable speaker PIP](../aip-composition/references/pip-transition.md) example minus its speaker view is a full cover.
- Reference every image through `src` so the hand-back check sees it.

## The speaker beat

- A zoom, filter or motion on a `speaker` beat is an effect host (see the [composition contract](../aip-composition/SKILL.md)); the service's engine applies it to every active track-0 speaker clip (`#stage > video[data-track-index="0"]`). End it before the next seated moment; an effect never lands inside a seat.
