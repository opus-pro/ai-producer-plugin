# AI Producer workspace format

Before source upload, check the format and size: `.mp4`, `.mov`, or `.webm`; at most 3.5 GiB; up to 30 minutes by default. Read the duration only from metadata the host already provides; do not install a media tool to measure it. When the duration stays unknown, submit and let the service enforce the limit. Recommend compression for larger files. Exports follow the source frame rate by default, capped at 30 fps.

The entry is `render-engine/index.html`. Supporting documents go in `compositions/`, assets in `public/`, styles in `styles/`, and fonts in `fonts/`, all beneath `render-engine/`.

The workspace accepts HTML, CSS, JSON, images (`.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`), fonts (`.woff`, `.woff2`, `.ttf`, `.otf`), video (`.mp4`, `.mov`, `.webm`), and audio (`.mp3`, `.wav`, `.m4a`, `.ogg`). Any other type, scripts and `.svg` files included, is rejected at signing and refused at commit as `unpromotable_type`: use the runtime scripts provided by the project and write vector graphics inline in the HTML. HTML is limited to 64 KiB per file; `narrator_captions.html` to 4 MiB.

An editable effect or caption is a composition document containing a `<template>`, mounted from the entry:

```html
<div class="visual-host clip" data-composition-id="example"
     data-composition-src="compositions/example.html"
     data-title="Example title card"
     data-start="0" data-duration="3" data-track-index="3"
     data-width="1080" data-height="1920"></div>
```

Give each independently editable visual beat its own composition file and host, with start and duration matching that beat. The editor exposes one movable effect per host.

The inner composition and its `window.__timelines` registration share the host's composition ID. Animation time is local to the composition.

Split speaker video/audio pairs use `class="clip speaker-clip"` and matching `data-hf-id`. The first pair has IDs `speaker` and `speaker-audio`. `data-start` is output time; `data-media-start` is the offset in the referenced media.

`compositions/editing-script.json` records the same speaker cut in its `av` track and the source-to-output mapping for caption words. Fetch the existing document once with the other workspace reads; preserve its source and other tracks. A changed speaker cut must publish the synchronized document with `index.html`, as [publication](publish.md) says; opaque caption shells or unsupported media mappings require a compatible authoring change before publication, not a guessed mapping.

Read project sources with `list_workspace` and `get_workspace_file`; publish with `commit_workspace`. Every publication is a closed graph: `index.html` mounts only completed moments, and every new host, composition, and asset is staged in the same batch under the previously accepted digest. An intermediate publication is the complete planned movie with fewer visual effects: preserve the root duration and full speaker/audio timeline, including beats whose effects are not ready. [Publication](publish.md) says how a workspace reaches the service on this host. Tool descriptions own lifecycle fields and service limits.

## Local handoff

Locally, the workspace is the `render-engine/` directory inside the project's [working folder](../SKILL.md#working-folder), never one straight in the current folder; `<render-engine-root>` in [publication](publish.md) is its full path.

Write a media, image, stylesheet, `data-composition-src`, or `data-pip-src` reference, and a CSS `url(...)` inside an HTML document, from the render-engine root whichever directory holds the document: the editor mounts a composition's template into `index.html`, so a document in `compositions/` references an image as `public/images/example.jpg` and a stylesheet as `styles/theme.css`, exactly as `index.html` does. A `../public/...` or `../styles/...` path from a composition names a file above the served root; the editor cannot load it and `commit_workspace` refuses it as `missing_reference`. Only a `<script src>` inside a composition is written from the composition's own file (`../public/vendor/gsap.min.js`, or `../public/vendor/three.min.js` for Three.js, which the service writes once a committed document names it), because the export loads the composition as its own page; the editor re-points a vendor script by file name. A `url(...)` inside a `.css` file under `styles/` resolves from that file, as CSS does.
