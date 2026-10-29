# Aesthetic rules

These rules hold over every fine cut, with a reference or without one. They decide what the edit shows, how much of it, and whether it reads, and they set a few numeric floors. How things move and cut - effects, curves, speeds, transitions, cutting techniques, palette, type and the caption look - comes from the reference, as the [reference style skill](../../aip-reference-style/SKILL.md) says, and without a reference from the [creative direction](../SKILL.md#creative-direction). Where a reference or the creative direction sets a number past a floor here, take the floor and keep everything else.

When rules disagree, decide in this order:

1. Every word whole and readable (section 3.2). Nothing outranks it, the user's words included.
2. The user's own words.
3. The rest of these rules.
4. The reference; without one, the creative direction.
5. Your own judgment.

## Terms

- **Speaker shot**: the speaker is the subject of the frame, with or without an overlay on it.
- **Showcase shot**: the subject is not the speaker: B-roll, a motion graphic, a 3D scene, full-screen text, or a seat that keeps the speaker small beside the payload.
- **Beat**: a change of picture the viewer clearly notices: a new showcase shot, a layout change, or a camera treatment such as a punch-in or a monochrome aside. Small motion inside one picture, such as a line fading in or an icon floating, is not a beat.
- **Jump cut**: a cut where the rough cut joins two pieces of one continuous shot.
- **Real thing** and **concept**: see section 1.

## 1. Material: real things as real imagery, concepts as animation

Decide, sentence by sentence, which kind of thing the sentence shows.

**Real things** exist and can be filmed or captured: a logo, a product, a person, a place, a news event, a software interface.

- Use the real material the [research](../SKILL.md#source-supporting-visuals) found, B-roll or images. Present it the way the reference presents material of the same kind: its container, frame and entrance. Where the reference shows no such example, show the material as it is, with one short source label: the outlet or site, and a date when timing matters. Authored graphics and logos carry no source label.
- Keep material undistorted and sharp: hold its aspect ratio, and never show it larger than 1.5x its own pixel size. Leave out material that carries a watermark, someone else's captions, or another platform's player or feed around it; an interface the speaker talks about is the subject, not that frame.
- Material whose orientation differs from the canvas never sits on black bars: place it in the reference's container for that kind of material, or crop it to its subject.
- An interface screenshot or screen recording pushes in on the part the speaker is talking about, until the interface's text reaches body size (section 3.2).

Why: viewers believe what they can see, so real material is the argument. A stretched, blurred or watermarked one argues against the speaker.

**Concepts** are mechanisms, scale, data, processes, logical breakdowns, causes, and anything else the speaker cannot point at. Animate them. Make the animation accurate, obvious and lean first, then choose 2D or 3D:

- **Accurate**: the relationships drawn (size, ratio, order, direction of cause) match what the speaker says. "Tripled" means the new bar is three times the height of the old one. Accurate means the relationship is right, not that every unit is drawn.
- **Obvious**: a viewer reads what the picture says at a glance, without narration.
- **Lean**: the fewest elements that make the idea clear. Show a quantity with one strong element: a big number, a counter running up, a stack of cards with visible thickness, a long bar. Once repeated elements are too many to count at a glance, about ten, switch to one of these. "A hundred takes" is a thick stack of cards and a counter running to 100, not a hundred avatars.
- **Once**: say each piece of information one way. When the caption already says "over seven hundred people", the picture shows that scale one way, a big number or an abstract figure, never both.
- **2D or 3D, whichever is more accurate and more obvious**:
  - 2D motion graphics suit flat structure: steps, comparisons, charts, chains of argument. Use 2D whenever the viewer compares values, because perspective distorts lengths and areas.
  - 3D suits content that is spatial by nature: scale, hierarchy, internal structure, spatial relationships. Build a Three.js scene under the [composition contract](../../aip-composition/SKILL.md)'s code-drawn rules, or give DOM elements real depth with CSS 3D (`perspective`, `translateZ`, `rotateX/Y`).
- In 2D or 3D, text faces the camera.

Why: a concept has no footage to film, so the animation exists to make the viewer understand it. 2D or 3D is only the means.

When a sentence names both a real thing and a concept, show the one that carries the sentence's new information: the word the caption would emphasize, usually the object or the number, not the subject already on screen.

## 2. Rhythm: short and dense

- Keep the rhythm the reference or the creative direction sets, but no two neighboring beats are more than 6 s apart.
- Without a reference, showcase shots cover at least 70% of the runtime. With a reference, keep its balance between speaker and showcase shots, but never below 50%. Speaker shots join the showcase shots and keep the speaker present.
- When there is a lot to show, split it into consecutive showcase shots of 2 to 4 s each; no single picture holds for 10 s.
- Two neighboring showcase shots never look the same: change the layout, the arrangement or the kind of material.

Why: attention drains second by second, and steady visual change is what holds it.

### 2.1 Opening and ending

- The first frame is the cover: feeds and some platforms show it as the thumbnail. It shows the speaker or real content, never a blank or single-color plate, and the first beat lands within the first sentence.
- The edit ends within 0.5 s of the last word. Its last frame is a settled picture, never an element halfway through its entrance and never an empty plate.

Why: a blank first frame is a blank cover, and a tail after the last word is dead air the viewer scrolls past.

### 2.2 Picture follows speech

- An element arrives with the word that names it: at most 0.3 s before that word starts, never after it. A list fills item by item as the speaker names each one.
- Inside a showcase shot, nothing shows before the speaker reaches it: a keyword stays hidden until its turn.
- A beat boundary falls between words, at a phrase or sentence boundary where there is one, never inside a word.
- When the speaker moves on to the next topic, the previous topic's picture leaves at that sentence boundary.

Why: a picture that runs ahead spoils the line, and one that lags behind reads as a mistake.

### 2.3 Jump cuts

At every jump cut, the framing on the two sides differs - full frame against 1.3x or more on the face, or a recomposition toward one side - unless a showcase shot covers the cut. Each reframe is a zoom effect host with no ramp in or out, and no two framings in a row match.

Why: with the same framing on both sides, the speaker's head jumps and the edit reads as broken; a change of framing reads as deliberate.

## 3. Layout and text: one thing per screen

### 3.1 When it does not fit, cut content, not size

When a layout cannot hold its content, try in order:

1. Remove secondary elements and keep only the one that supports this sentence.
2. Split it across several beats.
3. Simplify the graphic itself: fewer nodes, shorter text.

Layout scale and type size stay as they are.

### 3.2 Text whole and readable

- **Whole**: every character stays inside the safe area from its entrance to its exit, including the largest moment of any scale, bounce or emphasis. The safe area keeps clear, as a share of the canvas:

  | Canvas | Left | Right | Top | Bottom |
  | --- | --- | --- | --- | --- |
  | Portrait | 8% of the width | 12% of the width, for the platform's buttons | 10% of the height | 20% of the height, for the platform's caption bar |
  | Landscape or square | 8% of the width | 8% of the width | 8% of the height | 8% of the height |

- **Size by tier**: body text is at least 4% of the canvas's short side (44 px on a 1080-wide canvas), and a headline is a tier larger. The tier sets the size, and once set it never shrinks for one line.
- **Let layout break the lines**: set the text box's `max-width` to the safe area's width and let the text wrap. A manual break (`<br>`, or `white-space: nowrap` on each line) guesses how many characters fit without knowing the face's real widths, and it is the usual cause of overflow.
- **When it does not fit**, in order: break the lines differently (an emphasized word alone on its line works best), cut words, move the rest to the next beat. Text the user gives word for word is never cut: it only breaks differently, a long token such as a link or a product name wrapping anywhere (`overflow-wrap: anywhere`), or moves on to the next beat. A headline, where the reference or the user calls for one, takes at most 3 lines per beat.
- **Real text**: every piece of on-screen text is real, readable content. Where text belongs, write the text; never a block, a line or a blur standing in for it.
- **Contrast**: every word reads against the picture it actually sits on. How text stands out - an outline, a shadow, a plate, or nothing - is the reference's: do what it does for the same kind of text. Where that look does not read over the user's footage, first move the text to a calmer part of the frame, and add a treatment only when no position works, taken from what the reference already uses where it can. Check it over a frame of the user's footage, as the reference style skill's caption matching does in its last step.
- **Time to read**: authored text, as opposed to captions, stays on screen for at least 1 s, and for at least one second per six Chinese characters or three English words.
- **Still while read**: once text has entered, it holds or drifts slowly. Bobbing, wobbling and looping motion is for graphics, never for words.

Why: text that is cut off, too small or unreadable against its picture fails at its one job, and no style is worth that. A rule that always added a shadow put one on a reference that had none, so readability is the floor and the treatment stays the look's.

### 3.3 One focus at a time

- One thing enters at a time: elements that arrive together enter one after another, in reading order.
- Text and graphics stay off the speaker's face, as the [framing skill](../../aip-framing/SKILL.md) measures it for an overlay.
- The same kind of information keeps one style and one place across the edit: every number in one style, every source label in one position. The edit uses at most two type families, the reference's where it shows them.

Why: the eye goes to motion, and two things moving at once split it. A style that changes from beat to beat makes the viewer learn the screen again.

### 3.4 A logo with text owns its beat

A logo that carries text, a wordmark or a mark set with a name, is itself a set of words: the same kind of element as a caption.

- In the beat where it appears, the logo is the only text on screen: the captions show no cue for that stretch and no other label shows. Such a beat usually lasts 1 to 2 s.
- When content follows the logo, such as a feature list or selling points, make it two beats: the logo alone first, then the content, with the captions back in the content beat.

Why: a logo and a caption are both words. Together, two faces and two weights compete for one glance, and the viewer cannot tell the brand from what the speaker is saying.

## 4. Punch-in

- Its scale, speed and curve follow the reference, but the scale is never below 1.3x.
- Center it on the face: after the push, the eyes and mouth stay in frame, while the top of the head may leave it.
- Hold it for at least a phrase, and return at a sentence boundary.
- This rule covers a push made for emphasis, hard or fast. A slow continuous push or pull over B-roll (Ken Burns) is exempt.

Why: below 1.3x the viewer does not read the push as deliberate camera language; it looks like a shake or a bad cut. A push that snaps straight back reads as a glitch.

## 5. Motion craft

- Every element has an entrance and an exit. The exit finishes before its beat ends, or the cut itself is the exit.
- An exit is quicker than its entrance.
- Moves and scales ease, never linear, unless the reference moves linearly.
- A still image never sits still: it carries a slow push, pull or drift for as long as it is on screen. No showcase shot is fully still for more than 2 s.

Why: a viewer never notices these until they are missing, and without them the edit reads as unfinished.

## 6. Effects by tier

Every treatment the edit adds belongs to one of three tiers, and its tier decides when it may be added.

**Tier 1, craft**: treatments the viewer does not read as effects but misses when they are absent: the reframes at jump cuts (section 2.3), staggered entrances (section 3.3), exits before the cut, eased moves and moving stills (section 5). They are always on, with curves and durations from the reference where it shows them.

**Tier 2, meaning**: treatments a line of speech calls for, each with a trigger you can find in the transcript. Where the reference has its own treatment for the same kind of line, use the reference's. Where it has none, use the default below, in the reference's palette, type and curves. Each one runs only on its trigger, and the same one never runs on two beats in a row.

| Trigger in the transcript | Default treatment |
| --- | --- |
| The word a sentence turns on: a verdict, a number, a "but" | A punch-in on the speaker, under section 4 |
| Sarcasm, self-deprecation, or a short aside | A monochrome aside: on the same speaker shot, a `grayscale(1)` filter effect host and a punch-in over the same words, from the sentence's first word to its last by the transcript's times, after which color and framing return |
| A quantity that is the point of the sentence | The number counts up to its value in one strong element (section 1) |
| An announced count, such as "three reasons" | Each item carries its index (1/3, 2/3, 3/3) in the same place |
| A quote from a named person or source | A quote card with the words and who said them; the captions show no cue while it is up, since it draws the phrase |
| The speaker points at part of an interface | A push in on that part (section 1) |

Why: a meaning treatment tells the viewer how to take a line. A monochrome push, for example, marks the line as stepping outside the talk, and the viewer hears the change of tone at once.

**Tier 3, signature**: treatments a viewer recognizes as a style: a flash, a shake, a whip, a glitch, a light leak, film grain, an RGB split, a speed ramp. These rules never add one. The reference or the user brings them; without a reference, the creative direction decides.

Why: a default that could add them put flashes and shakes on a reference that only cuts hard, and most strong references cut hard at nearly every boundary.
