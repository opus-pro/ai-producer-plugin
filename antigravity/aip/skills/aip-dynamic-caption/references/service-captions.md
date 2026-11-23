# Service-built captions

Read this when a project already has the service's caption layer, a `narrator-captions` host in `index.html`. Captions you write are caption moments under the [dynamic caption skill](../SKILL.md), and none of this applies to them.

A project that already has the layer keeps it as mounted, with no offset on its host or its `.caption-band` from `index.html`, which would move the whole full-canvas band and put every word off screen.

In such a project, a visual moment's host may carry the caption policy for its window:

- `data-hide-captions="false"` keeps the running caption on under the moment; absent or `"true"` hides it, the default.
- `data-caption-position="<integer percent of frame height>"` moves the caption band's anchor for that window.
- `data-caption-ink="#<six hex digits>"` gives the caption type that colour under the moment, for a ground this composition painted light.

The editor, the service's edit paths, and the export re-derive that caption layer's windows from these attributes, so a moment moved or deleted carries its policy with it.
