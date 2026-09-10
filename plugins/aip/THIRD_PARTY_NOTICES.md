# Source and branding notices

Original AIP plugin source, helper scripts, and tests are provided under the [MIT License](LICENSE), except for the HyperFrames-derived skill described below. This package contains no bundled third-party authoring engine, animation runtime, or media library.

## HyperFrames-derived composition skill

The files in `skills/aip-composition/` adapt HyperFrames composition and seekable-animation guidance and are distributed under the [Apache License, Version 2.0](licenses/Apache-2.0.txt), including OpusClip's modifications to those files.

Copyright 2026 HeyGen, Inc.

Modifications Copyright 2026 OpusClip.

Upstream: [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes). The upstream license and applicable source notices were verified at commit [`a7e2e3853a347c862d0d910515c7224a14b114f0`](https://github.com/heygen-com/hyperframes/tree/a7e2e3853a347c862d0d910515c7224a14b114f0). Reference sources: [composition contract](https://github.com/heygen-com/hyperframes/blob/a7e2e3853a347c862d0d910515c7224a14b114f0/skills/hyperframes-core/SKILL.md), [animation guidance](https://github.com/heygen-com/hyperframes/blob/a7e2e3853a347c862d0d910515c7224a14b114f0/skills/hyperframes-animation/SKILL.md), and [keyframes guidance](https://github.com/heygen-com/hyperframes/blob/a7e2e3853a347c862d0d910515c7224a14b114f0/skills/hyperframes-keyframes/SKILL.md).

Modified by OpusClip: condensed and renamed the guidance for AIP's hosted workspace and editor; added AIP-specific speaker, audio, effect, timing, and delivery constraints; added a limited single-speaker PIP example. These are modified AIP instructions, not an unmodified upstream skill or an endorsement by HeyGen. No upstream `NOTICE` file applies to the referenced skill directories at the verified revision. Notices for unrelated upstream fixtures and skills do not apply because those materials are not included.

## Separate tools, media, and trademarks

Tools and media chosen for individual projects retain their own licenses and terms. The plugin's source licenses do not replace their conditions or license the hosted AI Producer service. Referencing GSAP or supplying it separately to a development fixture does not redistribute it in this package.

Product names and the AI Producer icon identify this plugin; the source licenses do not grant trademark rights or imply endorsement of modified distributions.
