# AIP workspace format

The entry is `render-engine/index.html`. Supporting documents go in `compositions/`, assets in `public/`, styles in `styles/`, and fonts in `fonts/`, all beneath `render-engine/`.

The workspace accepts HTML, CSS, JSON, images, fonts, video, and audio. HTML is limited to 64 KiB per file; `narrator_captions.html` to 256 KiB. Use the runtime scripts provided by the project and embed vector graphics in HTML.

An editable effect or caption is a composition document containing a `<template>`, mounted from the entry:

```html
<div class="visual-host clip" data-composition-id="example"
     data-composition-src="compositions/example.html"
     data-start="0" data-duration="3" data-track-index="3"
     data-width="1080" data-height="1920"></div>
```

Give each independently editable visual beat its own composition file and host, with start and duration matching that beat. The editor exposes one movable effect per host.

The inner composition and its `window.__timelines` registration share the host's composition ID. Animation time is local to the composition.

Split speaker video/audio pairs use `class="clip speaker-clip"` and matching `data-hf-id`. The first pair has IDs `speaker` and `speaker-audio`. `data-start` is output time; `data-media-start` is the offset in the referenced media.

Read project sources with `list_workspace` and `get_workspace_file`; stage uploads and apply them with `commit_workspace`. The workspace digest supplies `base_digest`, and `last_promote` reports the accepted files or specific refusals. Tool descriptions provide the transfer details.

## Local handoff

Write a media, image, `data-composition-src`, or `data-pip-src` reference, and a CSS `url(...)` inside an HTML document, from the render-engine root whichever directory holds the document: the editor mounts a composition's template into `index.html`, so a document in `compositions/` references an image as `public/images/example.jpg` exactly as `index.html` does. A `../public/...` media path from a composition names a file above the served root; the editor cannot load it and `commit_workspace` refuses it as `missing_reference`. A `<script src>` or `<link href>` inside a composition is written from the composition's own file (`../public/vendor/gsap.min.js`, `../styles/theme.css`), because the export loads the composition as its own page; the editor re-points those two by file name. A `url(...)` inside a `.css` file under `styles/` resolves from that file, as CSS does.

The bundled helpers require Python 3.10 or newer on the client host. If unavailable, perform equivalent static checks and batch PUTs with available host tools; do not install a runtime as part of the video task.

Run `python3 <loaded-aip-skill>/scripts/preflight.py <render-engine-root>` once after authoring. Use repeated `--remote-file` arguments only for paths confirmed present in `list_workspace` but absent locally, such as `public/source.mp4`, `public/source.mp3`, or `public/vendor/gsap.min.js`. Both helpers accept local root-relative paths and service paths beginning with `render-engine/`; they remove exactly one such prefix. This checks known local integration mistakes, not rendering or visual quality. Fix reported errors before uploading.

For one batch transfer, construct a temporary JSON array of objects with `path` (the service path or a path relative to the local render-engine root), `upload_url`, and `headers` from the signed-upload response. Feed it on stdin to `python3 <loaded-aip-skill>/scripts/upload_batch.py <render-engine-root>`. The helper runs bounded parallel PUTs and prints only relative paths and outcomes. Do not print signed URLs or persist them in project documentation. It does not sign, commit, retry failed uploads, or call an LLM; if any upload fails, do not commit the incomplete batch.
