# Continuous speaker transitions

<!-- SPDX-License-Identifier: Apache-2.0 -->

Copyright 2026 HeyGen, Inc. Modifications Copyright 2026 OpusClip. Modified by OpusClip for AIP; see [source attribution, license, and changes](../../../THIRD_PARTY_NOTICES.md).

This candidate recipe is scoped to an uncut project with one root speaker video and no editor camera overrides. Use it only when that condition holds and the brief calls for a continuous full-screen/PIP transition. For cut media, do not copy the single-ID selector: each active speaker clip needs coordinated geometry, which this recipe does not implement. Choose the layout and timing from the brief; these numbers are illustrative, not an editorial preset.

Keep the speaker and its visible frame under one transition owner. On the root paused `finecut-root` timeline, tween the speaker's box (left, top, width, height), crop (`object-position` with `object-fit: cover`) and corner radius over the same interval. Keep the single root speaker video; do not add a second decoder or change its source for a layout change. A full-frame static matte that appears with a child scene can make an otherwise animated speaker look like a hard cut.

```js
const full = { left: 0, top: 0, width: 360, height: 640,
  borderRadius: 0, objectPosition: '50% 50%' };
const pip = { left: 24, top: 340, width: 312, height: 276,
  borderRadius: 30, objectPosition: '50% 28%' };
rootTl.fromTo('#speaker', full, {
  ...pip, duration: 0.6, ease: 'power2.inOut', immediateRender: false
}, 1);
rootTl.to('#speaker', { ...full, duration: 0.6, ease: 'power2.inOut' }, 4);
```

Place material animation inside its editable composition, with its host active throughout the transition. Animate the content, never the timed host's display or visibility. Root and child timelines use their respective global/local clocks; align their intervals explicitly. Do not move the root speaker into a child composition to obtain a crop.

This geometry recipe is verified in a standalone synthetic DOM/GSAP fixture with forward/backward seeks. It is not proof of live AIP editor acceptance or export compatibility. The fixture's material card is deliberately inline to isolate geometry; production material must use the normal editable composition contract. AIP can apply speaker camera edits and adopt the speaker ID onto a different clip after cuts; reusing this recipe on cut media requires testing those interactions. Check whether editor styles or camera operations override the same properties before choosing box tweens. Do not claim the root transition retimes automatically when an independently editable effect is moved. Do not use an export attempt as part of the user's preview-only task.
