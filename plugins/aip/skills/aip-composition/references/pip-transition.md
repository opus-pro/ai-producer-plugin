# Editable speaker PIP transitions

<!-- SPDX-License-Identifier: Apache-2.0 -->

Copyright 2026 HeyGen, Inc. Modifications Copyright 2026 OpusClip. Modified by OpusClip for AIP; see [source attribution, license, and changes](../../../THIRD_PARTY_NOTICES.md).

A full-frame/PIP transition that belongs to an editable visual moment stays inside that moment, as the [composition contract](../SKILL.md) says.

The host in `index.html` carries the output window:

```html
<div class="visual-host clip"
  data-composition-id="example-pip"
  data-composition-src="compositions/example-pip.html"
  data-title="Speaker picture-in-picture"
  data-start="4.5" data-duration="6.5" data-track-index="3"
  data-width="1080" data-height="1920"></div>
```

```html
<template>
  <div data-composition-id="example-pip" data-width="1080" data-height="1920">
    <style>
      [data-composition-id="example-pip"] {
        position: absolute; inset: 0; overflow: hidden; background: #11151a;
      }
      [data-composition-id="example-pip"] .speaker-pip-frame {
        position: absolute; left: 0; top: 0;
        width: 1080px; height: 1920px; overflow: hidden; border-radius: 0;
      }
      [data-composition-id="example-pip"] .speaker-pip-frame video {
        width: 100%; height: 100%; object-fit: cover; object-position: 53% 30%;
      }
    </style>
    <div class="speaker-pip-frame" data-aip-editable="speaker-pip-frame">
      <video id="example-pip-speaker"
        data-pip-src="public/source.mp4"
        data-start="4.5" data-duration="6.5" data-media-start="9.93"
        muted playsinline data-volume="0"></video>
    </div>
    <script>
      const root = document.querySelector('[data-composition-id="example-pip"]');
      const frame = root.querySelector('.speaker-pip-frame');
      const tl = gsap.timeline({ paused: true });
      const full = { left: 0, top: 0, width: 1080, height: 1920, borderRadius: 0 };
      const pip = { left: 120, top: 984, width: 840, height: 840, borderRadius: 32 };
      tl.to(frame, { ...pip, duration: 0.6, ease: 'power2.inOut' }, 0);
      tl.to(frame, { ...full, duration: 0.6, ease: 'power2.inOut' }, 5.9);
      window.__timelines['example-pip'] = tl;
    </script>
  </div>
</template>
```

The seat rect and the `object-position` above are example values: the framing skill owns the shape and position, and `frame_speaker` returns the crop for the slot you place. The opaque composition ground prevents the unchanged root speaker from showing behind the moment-owned view. Animate the frame, not the timed host or composition root.
