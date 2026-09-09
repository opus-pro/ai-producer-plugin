# AIP workspace contract

Prepare editable source files and assets for an AIP project. Choose authoring tools separately; this plugin describes the service's file boundary. Read the existing workspace before editing and preserve its document structure, timing, media references, and editable elements. For a new project, use the current AIP tools and their returned project state as the starting point.

## File layout

Tool paths are relative to the project root, including the `render-engine/` prefix. The externally writable portion is:

```text
render-engine/
  index.html          # Editable project entry
  compositions/       # Supporting documents and data, when used
  public/             # Referenced media and assets, when used
  styles/             # Stylesheets, when used
  fonts/              # Font files, when used
```

`render-engine/index.html` is the entry file. The four directories are allowed destinations, not a requirement to create empty folders. Their filenames and contents follow the actual project. AIP owns the rest of the workspace, including plans, transcripts, build metadata, dependencies, and generated exports. Do not upload an entire repository, dependency tree, or render output as project source.

Destination paths use `/` separators and only ASCII letters, digits, `.`, `_`, and `-` within each segment. No leading slash, backslash, NUL, empty segment, `.` segment, or `..` segment is accepted. Limits are 512 characters per path, 128 per segment, and eight segments including the filename. Keep caches, temporary directories, and version-control metadata out of the upload.

## Accepted files

| Kind | Extensions |
| --- | --- |
| Documents and data | `.html`, `.htm`, `.css`, `.json` |
| Images | `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif` |
| Fonts | `.woff`, `.woff2`, `.ttf`, `.otf` |
| Video | `.mp4`, `.mov`, `.webm` |
| Audio | `.mp3`, `.wav`, `.m4a`, `.ogg` |

HTML must be UTF-8 and at most 64 KiB per file. A caption document named `narrator_captions.html` has a 256 KiB limit. Each non-HTML asset is limited to 256 MiB. These are file-admission limits, not evidence that a document or codec will render correctly.

The service does not accept uploaded JavaScript modules, standalone scripts, or SVG files. Reference the scripts AIP already provides in the project; do not install or upload replacement runtime files or dependency manifests.

## Documents and references

Keep all required assets available in the project. An uploaded HTML file's relative `src` and `href` references are checked from that document's directory against existing workspace files, files accepted in the same batch, and service-provided resources. A missing reference refuses the whole batch. Preserve the existing project's working references and inspect playback after changing paths.

HTML must not load remote scripts, contain `on*` event-handler attributes or `javascript:` URLs, or make network calls such as `fetch`, `XMLHttpRequest`, `WebSocket`, or `sendBeacon`. Author the document from the resources supplied to the project.

File placement alone does not define an editable video. Preserve the established canvas, timeline, audio behavior, and editor metadata in the project's sources. The service's preview and export checks determine whether the resulting document works.

## Handoff and verification

The MCP tool descriptions own transfer procedures, arguments, costs, and recovery. Use `list_workspace` and `get_workspace_file` to inspect the current sources. When the listing returns a non-null digest, use it as `base_digest` when committing changes so a concurrent editor update is detected rather than overwritten. A truncated listing can return a null digest; inspect the affected files using the tool guidance, omit `base_digest` if no complete-workspace token is available, and state that this commit has no digest-based concurrency check. Do not invent a token or pass null as a digest.

A staged upload is not part of the playable project. `commit_workspace` accepts or refuses the entire staged batch; inspect the terminal task and `last_promote` result before treating files as accepted. On a stale base, read the current project and reconcile the changes before trying again.

An accepted batch proves file admission, not renderability. Inspect the actual AIP preview and, when export is requested, its completed export result. Report failed or unperformed checks clearly and return the editable project link with the delivery.
