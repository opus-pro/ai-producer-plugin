# Legacy `@aip` lines

Read this when the user's message holds a line that starts with `@aip` in place of a [Motion Library handoff](handoff.md) context line.

Only a legacy line that starts with `@aip` goes to `resolve_selection`. Call it with `selection` set to that line verbatim, never under a `request` argument; include `project_id` when the active project is known. Preserve its explicit "here" time unless the user's current words override it, and then validate the returned pinned id and version through `list_motion_assets`. Motion assets otherwise follow the grounding, binding, derivation, cutout, retry and delivery rules of the [handoff](handoff.md). Do not require `get_motion_asset` for an explicit unchanged legacy placement whose live listing already supplies everything needed.

An `omni-preset` line is no longer served: Scene restyle is not available through this server. Tell the user once that this preset cannot be applied here, and do not substitute another tool for it.
