# Progressive publication in Codex

Use this path for a fresh prepared project with no visual effects. The Python authoring script calls a task-scoped publisher after each completed effect; it waits for acceptance before authoring the next. One script execution contains all mechanical publications. The helper never starts a model turn, calls a media provider, extracts OAuth credentials, changes host configuration or approves a permission request. Do not add a host response per effect or deliberately delay publication to simulate work. A commit still uses normal server hydration/admission capacity and rate limits.

The native transport requires a Codex CLI exposing `mcpServer/tool/call` on its app-server protocol. It uses `codex` from PATH by default; pass `cli=` only for a known installed Codex executable when the host supplies its path. It fails closed if unavailable or if approval/input is requested. Do not install a new runtime, disable permission checks, change authentication, or fall back to a different MCP server to make it run. The `server` argument is the exact server of the loaded plugin, not an endpoint URL.

## Author and publish

Load helpers from this skill's own `scripts/` directory. Read the current project workspace once as usual. Plan the full edit duration, including intended cuts, and write a complete base `index.html` with no visual hosts. Its root and continuous speaker/audio clips must cover the whole planned output. Keep the source audio and video paired with the same `data-hf-id`, output starts and durations. Declare explicit IDs, source paths, `data-media-start`, `data-track-index` and `data-volume`. This base can represent a deliberately shortened edit; intermediate effects cannot shorten it further.

Construct `ProgressPublisher` after that base exists and before writing any effect. For each beat, write its composition and newly needed assets, update the cumulative index with exactly one additional host, and call `publish`. Include `index.html`, the new composition and every newly referenced dependency in `files`. Paths are relative to `render-engine/` or begin with that service prefix. Already accepted dependencies need not be uploaded again. The helper copies each named batch to an immutable temporary snapshot, checks references against that snapshot and confirmed remote files, and uses the accepted receipt digest for the next commit. Concurrent edits cause a refusal; the helper never silently rebases over them.

```python
from pathlib import Path
import sys

sys.path.insert(0, str(loaded_aip_skill / "scripts"))
from codex_mcp import CodexMcp
from progressive_publish import ProgressPublisher

# Define these authoring functions in this script. They write the actual HTML.
write_complete_speaker_base(workspace, planned_duration)
with CodexMcp(server, workspace) as mcp:
    publisher = ProgressPublisher(workspace, project_id, planned_duration, mcp)
    for position, beat in enumerate(planned_beats):
        files = author_one_effect_and_update_index(workspace, beat)
        publisher.publish(files, final=position == len(planned_beats) - 1)
```

The example's `author_one_effect_and_update_index` creates only the current effect, retains prior hosts, and returns that batch's paths including `index.html`. It does not prebuild the remaining effects. Preserve the full root and speaker/audio timing from the base. Root framing animation may change as effects arrive, but unfinished beats must retain a usable presenter view; do not move the presenter aside for visuals that have not been mounted. Keep BGM/caption changes outside this per-effect loop unless their dependencies are included and the speaker timeline stays unchanged.

Each return prints only the accepted effect count, duration, task ID, final flag and bounded warning codes. Intermediate commits retain authoring state; `final=True` on the last effect closes it. The final cumulative index must mount every requested effect. No additional `finish_project`, publication, transcript read or status heartbeat is needed for this path.

An invalid duration, incomplete AV coverage, changed speaker timing, changed prior host, or addition of more than one effect is refused locally before signing. Upload failure, task failure, stale digest, permission request or an unaccepted receipt stops the session. Preserve the last accepted project and report the failure; do not restart the sequence automatically. A normal rate-limit refusal also stops without buying model work; its wait/recovery is an explicit later action. Do not log signed responses or put them in project files.

The helper's zero-model-turn property covers publication control only. Creative authoring still uses the host model; these checks do not establish equal total token cost, preview quality, audio synchronization or export compatibility. Other hosts and existing effect graphs use the ordinary complete-graph path until a supported transport and matching continuation contract are available.
