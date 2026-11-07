# Text treatments

Mechanisms for text that is more than type: given a material, broken apart, printed as a pattern, or set in an irregular mark. Each keeps the words as DOM text the user can retype, under the [composition contract](../SKILL.md). These are ways to build a look, not looks to reach for: build the one the reference shows, from its frames, and name its mechanism first, since the right numbers on the wrong mechanism never converge.

## A material that follows the surface

Chrome, gold, glass and polished plastic take their colour from which way the surface faces, not from how high it sits: a face turned up mirrors the sky, a face turned down mirrors the ground, and the horizon between them is a sharp dark line. A gradient across the text, stacked strokes, or diffuse lighting colour it by height and come out as flat grey metal.

Build it as one SVG filter on the text, as a chain:

1. A height map: dilate the glyphs with `feMorphology` to the tube's width, then blur with `feGaussianBlur` so the stroke rounds from edge to centre.
2. Normals: two `feConvolveMatrix` Sobel kernels over the height map, one for each axis.
3. The reflection: an environment strip staged as an image (`public/images/<name>`), read with `feImage`, and moved by the normals with `feDisplacementMap`, so each point takes the colour of the direction it faces. Its bands, sky, horizon and ground, are what makes it read as the reference's metal.
4. Finish: multiply in any fine lines that follow the strokes, add a highlight, clip to the dilated glyphs, and draw the dark rim and the depth on one side as offsets of the glyph alpha.

The filter's dilation, blur, displacement and offsets are multiples of the type size, so one filter serves every size. One environment strip gives one horizon; a heavier, irregular reflection takes a second strip or a second chain. Give the filter an id unique to its composition, and take any tween of `filter` on a wrapper, as the contract says.

## Pieces of one word

A word that cracks, shatters or tears is several copies of the whole word stacked in one place, each showing one piece through `clip-path: polygon(...)` and moving around its own centre. The polygons, directions and spins come from a seeded generator, such as `seed = seed * 16807 % 2147483647`, never `Math.random`, so a seek lands on the same frame. An edge colour on the pieces is an offset `text-shadow`.

The pieces drift with one tween across their span; a glitch over them is a few frames on a channel of their own, such as `xPercent` and `yPercent`, on the beats the reference jumps on. Random polygons overlap and leave gaps rather than tiling the word exactly, and the pieces have no motion blur.

## A pattern inside the letters

Halftone, a texture, or a picture inside the letters is a copy of the text whose `mask-image` shows only the pattern, such as a `radial-gradient` dot repeated by `mask-size`, over a darker or blurred copy that fills between the dots. A glow is several `text-shadow` layers, from tight to wide.

## An irregular mark

Ink, smoke, a torn edge or a hand-painted swash is a plain SVG shape run through `feTurbulence` with a fixed `seed`, then `feDisplacementMap`, then `feGaussianBlur`. It moves by tweening the shape or its wrapper; the noise itself stays still.
