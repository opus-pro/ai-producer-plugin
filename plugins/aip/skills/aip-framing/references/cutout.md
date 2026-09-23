# The cutout pop

The cutout is the one seat form that carries its own footage. Read this once before choosing it; the [framing skill](../SKILL.md) owns the other seat forms and the geometry every seat keeps.

## What it is

The pop: the room recedes into a full-width card and the speaker, cut free of it, stands proud of the card with the head crossing its top edge between the eye line and the neck; the headroom above the head hosts the payload.

It needs `matte: true` in the `frame_speaker` call, a window the speaker is on camera for, and at least 3 s for the recede and the payload to read; not a window whose `shot_cuts` is true.

A cutout is the one shape that carries two layers of footage inside the moment: the alpha webm `frame_speaker` staged, over a `public/source.mp4` view of the same window, wired as the last section says. The pop is the cutout's one form: a silhouette parked in front of a headline with nothing receding is an overlay wearing a matte, not a cutout.

## Measure it

Name the cutout's window in the `frame_speaker` call with `matte: true` and the canvas as its `slot`; a cutout always names its slot, since its pop geometry is derived for it. A cutout window also takes `headroom_px`: write the payload first, then pass the y where it ends inside the slot (its top margin included; the canvas y, since a cutout's slot is the canvas), and the pair sinks only far enough for the payload to clear the head, never so far that the jaw leaves the frame; omitted, the head sinks to a default target that assumes a tall chip-and-label stack, which leaves a short payload floating over empty ground. A cutout window also carries `cutout`, the whole geometry of the pop (or `null` when the matte measured no head band: seat that beat instead of guessing a pop): `sink_px` and `card_clip_top_px` go into the wrapper's tween and the source layer's clip-path (the clip rides inside the sunk wrapper, so its edge is stage-local); `head_top_px`, `head_bottom_px`, `payload` (`headroom` or `flank`) and `content_bottom_px` are canvas positions after the sink, where the payload lives; `headroom.fits` false means the ask passed what the pop can grant (half the slot, or the sink that keeps the jaw in frame) and was answered at `headroom.max_px`, so shrink the payload to end above that; `max_px` 0 means no payload fits above this head, so seat the beat instead. The last section says where each number goes.

## Where the payload sits

| canvas | the payload |
| --- | --- |
| portrait 9:16 (1080x1920) | in the headroom above the head |
| square 1:1 (1080x1080) | beside the head above the card edge |
| landscape 16:9 (1920x1080) | beside the head above the card edge, on the flank the head leaves open |

## What it keeps

- **The cutout is pixel-locked to its own footage.** The alpha webm and a `public/source.mp4` layer of the same window sit inside one wrapper at identical full-frame geometry: same rect, same `object-fit` and the same `object-position` from the result, native scale. The wrapper is the only element that moves, and it moves once: the sink, `y` from 0 to `cutout.sink_px`, which exists only to make room for the payload; it is sized from the `headroom_px` you passed, so a head already clear of the payload does not move, and nothing sinks for empty ground. Neither video is ever tweened alone, scaled, or given its own entrance; any drift exposes the room's real speaker beside the silhouette as a doubled edge. The card is nothing but the source layer's `clip-path`, `inset(0)` becoming `inset(<cutout.card_clip_top_px>px 0 0 0 round <r> <r> 0 0)` (stage-local: the wrapper's sink carries it to the canvas), and the silhouette's clip matches the card's sides and stays open at the top so the head crosses the edge. Nothing is drawn around the card: no rim, border, or outline, because the card is the live room and a frame around it reads as an empty box. Frame one is the raw full-frame speaker, the seamless join from the shot before; the sink and both clips move on one ease over about 0.9 s (0.6 s on a short beat); then the payload reveals, wholly above `cutout.content_bottom_px` (in the headroom above the head on a portrait canvas; beside the head above the card edge on a square or landscape canvas, on the flank `head_in_slot.left` and `right` leave open), and the card and silhouette hold dead still until the beat ends.
- **A cutout window is the moment's window, inside one take.** Ask `frame_speaker` for exactly the beat's `start` and `end`; the webm is cut to that window and its `data-media-start` is 0, so a window that differs from the host div plays the wrong footage. A window that crosses a cut is refused; split the beat at the cut, and read `presence.matte_ok` before you commit to a cutout, since an unmeasured or off-camera window is refused too.

## How it is built

- A `cutout` beat is a full-cover moment: its composition paints an opaque ground over the root speaker, hosts the payload in the headroom, and embeds two `data-pip-src` videos of the same window inside one wrapper on its own child timeline: `public/source.mp4` beneath with `data-media-start` at the source seconds of the beat's start, and `public/speaker_<slug>.webm` above with `data-media-start="0"`; both carry the host's `data-start` and `data-duration` and no `src`, as the [composition contract](../../aip-composition/SKILL.md) writes a PIP. The wrapper's sink, the card's clip edge, and the payload's floor are the result's `cutout.sink_px`, `cutout.card_clip_top_px`, and `cutout.content_bottom_px`, pasted as returned. Stage the webm's `files` entry from the `frame_speaker` result in the commit's `expected_files`, and reference the file in the same batch as the composition, since the hand-back check does not follow `data-pip-src`.
