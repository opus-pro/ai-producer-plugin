# AIP workspace format

Before source upload, check the format and size: `.mp4`, `.mov`, or `.webm`; at most 1.5 GiB; up to 15 minutes by default. Read the duration only from metadata the host already provides; do not install a media tool to measure it. When the duration stays unknown, submit and let the service enforce the limit. Recommend compression for larger files. Exports follow the source frame rate by default, capped at 30 fps.

The entry is `render-engine/index.html`. Supporting documents go in `compositions/`, assets in `public/`, styles in `styles/`, and fonts in `fonts/`, all beneath `render-engine/`.

The workspace accepts HTML, CSS, JSON, images, fonts, video, and audio. HTML is limited to 64 KiB per file; `narrator_captions.html` to 256 KiB. Use the runtime scripts provided by the project and embed vector graphics in HTML.

A commit replaces a document or a stylesheet already at a path under `compositions/`, `styles/`, or `fonts/`. It never replaces a file already committed under `public/`, nor any committed image, video, audio file, or font: different bytes at such a path are refused as `immutable_asset`, because an export reads those by path, and a replaced file would leave an earlier export reading as current. Upload the new bytes under a new name, repoint every reference to that name in the same commit, and leave the old file in the workspace.

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

The same digest identifies an export. Every `start_export` and `get_export_url` reply reports `current_workspace_digest` (the accepted workspace now) beside `export_workspace_digest` (the one the returned task rendered), with `reuse_reason`, `staged_files_present`, and warnings for uploads no commit accepted. To require a file of one exact tree, pass that tree's digest as `start_export`'s `expected_workspace_digest`, or name the `commit_workspace` task your edit went in by as `expected_commit_task_id` and let the server resolve it. Either way the request is bound: a workspace that has moved, a commit that was not accepted (`expected_commit_unmet`, with the reason and what clears it), a live turn that would decide the tree (`export_expectation_unbindable`, retryable), or a render already running over a different one is refused and nothing is exported. A refusal answers through `next_data`, not through the reply fields above.

## Local handoff

Write a media, image, stylesheet, `data-composition-src`, or `data-pip-src` reference, and a CSS `url(...)` inside an HTML document, from the render-engine root whichever directory holds the document: the editor mounts a composition's template into `index.html`, so a document in `compositions/` references an image as `public/images/example.jpg` and a stylesheet as `styles/theme.css`, exactly as `index.html` does. A `../public/...` or `../styles/...` path from a composition names a file above the served root; the editor cannot load it and `commit_workspace` refuses it as `missing_reference`. Only a `<script src>` inside a composition is written from the composition's own file (`../public/vendor/gsap.min.js`), because the export loads the composition as its own page; the editor re-points a vendor script by file name. A `url(...)` inside a `.css` file under `styles/` resolves from that file, as CSS does.

The bundled helpers require Python 3.9 or newer on the client host, invoked as `python3`, or as `py -3` on Windows. Without an interpreter, upload with the host's batch HTTP tools and skip the local check: submit and let admission report contract errors, rather than installing a runtime as part of the video task.

Run `python3 <loaded-aip-skill>/scripts/preflight.py <render-engine-root>` once after authoring. Use repeated `--remote-file` arguments only for paths confirmed present in `list_workspace` but absent locally, such as `public/source.mp4`, `public/source.mp3`, or `public/vendor/gsap.min.js`. Both helpers accept local root-relative paths and service paths beginning with `render-engine/`; they remove exactly one such prefix. This checks known local integration mistakes, not rendering or visual quality. Fix reported errors before uploading.

For one batch transfer, construct a temporary JSON array of objects with `path` (the service path or a path relative to the local render-engine root), `upload_url`, and `headers` from the signed-upload response. Feed it on stdin to `python3 <loaded-aip-skill>/scripts/upload_batch.py <render-engine-root>`. The helper runs bounded parallel PUTs through the host's HTTPS proxy when one is configured, and prints only relative paths and outcomes. Do not print signed URLs or persist them in project documentation. It does not sign, commit, retry failed uploads, or call an LLM; if any upload fails, do not commit the incomplete batch.
