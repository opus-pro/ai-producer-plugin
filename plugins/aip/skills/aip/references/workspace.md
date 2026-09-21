# AI Producer workspace format

Before source upload, check the format and size: `.mp4`, `.mov`, or `.webm`; at most 1.5 GiB; up to 15 minutes by default. Read the duration only from metadata the host already provides; do not install a media tool to measure it. When the duration stays unknown, submit and let the service enforce the limit. Recommend compression for larger files. Exports follow the source frame rate by default, capped at 30 fps.

The entry is `render-engine/index.html`. Supporting documents go in `compositions/`, assets in `public/`, styles in `styles/`, and fonts in `fonts/`, all beneath `render-engine/`.

The workspace accepts HTML, CSS, JSON, images (`.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`), fonts (`.woff`, `.woff2`, `.ttf`, `.otf`), video (`.mp4`, `.mov`, `.webm`), and audio (`.mp3`, `.wav`, `.m4a`, `.ogg`). Any other type, scripts and `.svg` files included, is rejected at signing and refused at commit as `unpromotable_type`: use the runtime scripts provided by the project and write vector graphics inline in the HTML. HTML is limited to 64 KiB per file; `narrator_captions.html` to 4 MiB.

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

`compositions/editing-script.json` records the same speaker cut in its `av` track and the source-to-output mapping for caption words. Fetch the existing document once with the other workspace reads; preserve its source and other tracks. A changed speaker cut must publish the synchronized document with `index.html`. The progressive helper handles this automatically. For ordinary publication, run preflight with `--sync-editing-script` and include the document in the upload batch; opaque caption shells or unsupported media mappings require a compatible authoring change before publication, not a guessed mapping.

Read project sources with `list_workspace` and `get_workspace_file`; stage uploads and apply them with `commit_workspace`. The workspace digest supplies `base_digest`, and `last_promote` reports the accepted files or specific refusals. When the current schema exposes `asset_origins`, the commit also says who supplied each media file it stages, as one `{path, origin}` per staged image, video, audio file or font: `upload` for a file the user handed over, `agent` for one you found, generated, or staged yourself. Only you know that, and it is what the project shows the user their own material by; a staged media file the list leaves out is recorded as `agent`. Every publication is a closed graph: `index.html` mounts only completed moments, and every new host, composition, and asset is staged in the same batch under the previously accepted digest. An intermediate publication is the complete planned movie with fewer visual effects: preserve the root duration and full speaker/audio timeline, including beats whose effects are not ready. For fresh Codex projects, the [progressive checkpoint flow](progressive-publication.md) validates that contract while the current task adds one effect per accepted commit through its loaded AI Producer MCP tools. Tool descriptions own lifecycle fields and service limits.

## Local handoff

Write a media, image, stylesheet, `data-composition-src`, or `data-pip-src` reference, and a CSS `url(...)` inside an HTML document, from the render-engine root whichever directory holds the document: the editor mounts a composition's template into `index.html`, so a document in `compositions/` references an image as `public/images/example.jpg` and a stylesheet as `styles/theme.css`, exactly as `index.html` does. A `../public/...` or `../styles/...` path from a composition names a file above the served root; the editor cannot load it and `commit_workspace` refuses it as `missing_reference`. Only a `<script src>` inside a composition is written from the composition's own file (`../public/vendor/gsap.min.js`), because the export loads the composition as its own page; the editor re-points a vendor script by file name. A `url(...)` inside a `.css` file under `styles/` resolves from that file, as CSS does.

The bundled helpers require Python 3.9 or newer on the client host, invoked as `python3`, or as `py -3` on Windows. Without an interpreter, upload with the host's batch HTTP tools and skip the local check: submit and let admission report contract errors, rather than installing a runtime as part of the video task.

Run `python3 <loaded-aip-skill>/scripts/preflight.py <render-engine-root>` before each real publication. Use repeated `--remote-file` arguments only for paths confirmed present in `list_workspace` but absent locally, such as `public/source.mp4`, `public/source.mp3`, or `public/vendor/gsap.min.js`, or staged by a service build and named in its result's `files`. A declared composition the host cannot read is reported as `composition_not_locally_inspectable` as a warning; undeclared, it is an error. Both helpers accept local root-relative paths and service paths beginning with `render-engine/`; they remove exactly one such prefix. This checks known local integration mistakes, not rendering or visual quality. Fix reported errors before uploading.

For one publication batch, construct a temporary JSON array of objects with `path` (the service path or a path relative to the local render-engine root), `upload_url`, and `headers` from the signed-upload response. Feed it on stdin to `python3 <loaded-aip-skill>/scripts/upload_batch.py <render-engine-root>`. The helper runs bounded parallel PUTs through the host's HTTPS proxy when one is configured, and prints only relative paths and outcomes. Do not print signed URLs or persist them in project documentation. It does not sign, commit, retry failed uploads, call an LLM, or authenticate to MCP; if any upload fails, do not commit the incomplete batch.
