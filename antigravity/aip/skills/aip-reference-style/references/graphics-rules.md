# Graphics, full covers, and pre-commit checks

Read this before authoring any graphic, full cover, or commit in a reference style edit, as the [reference style skill](../SKILL.md) says.

## Motion graphics

- **Motion follows the reference.** Only what the reference shows moves: each graphic enters, holds and leaves as its counterpart in the reference does, what the reference holds still stays still, and no effect, push, drift, count-up, monochrome aside or lens effect it lacks is added; a lens effect it shows (fisheye, edge blur, colour fringing) is copied.
- **Named products, tools and brands.** A product, tool or brand the user names shows as itself (its captured screens, footage or official logo) or as a faithful recreation of its real interface (its real layout, font and colours), never a generic stand-in or icon, and no image of it shows a person other than the user; its screen changes on each step the user speaks. No number, count or chart the user did not say; a picture of an amount shows that amount.
- **Drawn-everything references.** Where the reference draws every real thing it shows, real things are drawn in code in its look, never traced or restyled from a photo; flags and logos come from their official files; people stay generic unless the topic is that public figure.
- **Continuity and phrase bounds.** A thing the user's lines return to comes back drawn the same way, in its new state; a graphic showing spoken words shows their whole phrase, or ends where its words end.
- **Lists, hero icons and calls to comment.** A list keeps the reference's hierarchy, a title over smaller rows, each row entering on its own word; where the words give no title, use another kind. A logo or hero icon is never smaller than the reference's size. A call to comment or type a word puts that word alone in its container, the verb outside.
- **Reference containers and palette turns.** A container the reference draws (a window with its title bar and dots, a card, a tile) is its look: put the user's product content inside it, captured or faithfully recreated with the real interface's own parts and realistic previews, never placeholder tiles, at the reference's size and painted fill (its ground, bars and panels) wherever the frame, the safe area and the text floor allow; never wrap a photo, a clip or a marketing image in it. Where the reference's palette turns over its runtime, the edit turns only at the user's matching turn, in that order.
- **2D by default, 3D only when shown.** Each graphic is built from the pack's template for its kind, or flat in 2D in the pack's palette, type and motion; depth (a 3D object, faked thickness, a perspective tilt) appears only where the reference's own graphic shows it, built as one piece whose every face keeps the outline's shape and corners.

## Full covers

A full cover replaces the speaker's frame for its beat. Build and check each one as these say:

- **Captions vs display labels.** Whether captions run on under a graphic follows the reference, over the caption skill's rule: where its captions run on under word graphics or full covers, the edit's do; where they stop, they stop, and a full cover the reference keeps clear shows the line's key words as a display label in the pack's card type (one to three words, sized and placed as the labels on the reference's full covers), never a caption-style sentence or captions stacked over it.
- **Frame fill.** Each full cover's subject fills about half the frame, checked on its middle frame at full size: a lone small icon on an empty ground is not a full cover.
- **Reveal coverage.** A reveal that opens into a full cover (a growing disc, a wipe, a mask) ends covering all four corners of the frame: when you move its origin, grow its end radius or size to reach the farthest corner, and check the first full frame of each full cover at its four corners, which show the full cover, never the footage under it.

## Before each commit

With a whole pack that carries `## Evidence`, compare each graphic once beside its evidence still (`caption_compare.py compare`) before committing, with a second round only if the render shows it broken. Check each full cover's fill on its middle frame and its four corners on its first full frame.

- **Full-size edge check.** Inspect each graphic's edges and corners on a full-size crop of its render, never a downscaled one: no seam, sliver, notch or jagged edge where faces or layers meet.
- **No clipped strokes.** Text painted through a clipped gradient or mask (`background-clip: text`, `mask-image`, `overflow: hidden`) is padded past its tallest and longest strokes (at least ascent plus descent); check tails ("gets", "fly", "every") in pack templates and edit compositions alike.
- **Page and layout check.** Check the page before committing (including `preflight.py` as the AI Producer skill says): no graphic under the speaker or hidden; each caption's band set from the chin across the frames that cue covers, never one sample frame; no text over the face or over other text, every element inside the frame with margins; every spoken word in a caption or a graphic showing it (as [Full covers](#full-covers) says), each cue on screen at least as long as the reference's shortest; a cut-out one clean matte, held props included, no pasted pieces or fringe; every graphic showing its content from its first frame.
