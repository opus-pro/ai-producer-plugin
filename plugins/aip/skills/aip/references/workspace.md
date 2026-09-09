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
