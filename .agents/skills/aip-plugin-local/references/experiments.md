# Controlled video experiments

## Define the comparison before spending

Keep the original input files fixed by SHA-256, including audio, video, images, and brand references. Record model, reasoning effort, service tier, source/package hashes, actual loaded skills, MCP endpoint, tool availability, and requested deliverable. Use a new task and project for each run. Do not silently change installed global skills or use old task memory; record any global skill reads as contamination.

"No user prompt" means a minimal creative brief, not an empty request. Use the same input and a neutral request to edit it with the selected plugin, with no prior memory. A detailed-brief run uses the user's actual editorial requirements. Within either group, change only the plugin/candidate under test; do not rewrite the prompt to favor it.

| Group | Input and brief | Question |
| --- | --- | --- |
| Current plugin / minimal brief | Same media; minimal edit request | What does its default creative guidance produce? |
| Candidate plugin / minimal brief | Identical to the previous group | Does the candidate improve default quality without excess work? |
| Current plugin / detailed brief | Same media plus the user's exact constraints | Does it obey the intended style and delivery contract? |
| Candidate plugin / detailed brief | Identical to the previous group | Does guidance help or interfere with explicit direction? |

These are available comparisons, not authorization to run all four. Run only the requested cases. When the user asks for a pure-model baseline, hold model, effort, inputs, brief, target duration, and deliverable constant where possible; remove only the plugin requirement. Record differences such as local HTML versus editable AIP preview, missing editor integration, or absent export. A cheap baseline that does less is useful context, not a like-for-like cost proof.

Ask for a missing media input or material test choice before launching paid generation. A setup-only request ends after installation checks. Batch optional repetitions only after the user requests that scope; a single pair shows an observation, not a causal quality or cost conclusion.

## Run and observe

Use a neutral media workspace. Give the generation task only its input, brief, and selected plugin. Do not inject the development checklist or require intermediate essays. Confirm the actual loaded package/version from its records, rather than asking it to repeatedly inspect installation state.

The generation task follows its runtime skill: open the editable preview in Codex during preparation, deliver the durable link at the end, and do not initiate playback inspection or aesthetic repair. Export remains explicit. Record unexpected exports, repeated commits, tool polling, transcript refetches, unrelated skill reads, and child tasks; do not attribute an entire mixed-purpose child task to sound or another single feature.

Record generation usage before any requested evaluation or follow-up edits. Review quality in a separate task or have the user score it; exclude that review's model usage from generation cost. Opening a page for the user is not an instruction to play or inspect it. If MP4 behavior is itself the requested experiment, record the explicit export/evaluation scope and its incremental cost separately.

## Record results

Keep one local ledger row per run, in ignored scratch. Store identifiers only as needed to find the run; keep transcripts, signed URLs, auth material, and user identity out of the ledger. Do not publish private project/task links or media. Capture prompt/input hashes instead of duplicating their content.

| Metric | Required distinction |
| --- | --- |
| Model work | Responses, uncached input, cached input, output, reasoning subset, child-task contribution, API-equivalent USD or an explicit unknown |
| Timing | Generation elapsed time; original source duration; requested output duration; delivered duration; report service waits separately when available |
| Efficiency | Number of submissions, revisions, exports, inspection calls, polling/refetches, and unrelated skill reads |
| Opening and delivery | In-app open during preparation; final durable link; no external browser or single-use link delivery |
| Editorial quality | Hook, pacing, clarity, specificity of visuals, and whether the result feels flat or repetitive |
| PIP/motion | Actual continuity through intermediate poses, meaningful entrances/exits, abrupt cuts, and deterministic seeking when evaluated |
| Editor contract | Effect/timeline visibility, selectable/editable elements, media paths, synchronization, and caption constraints when evaluated |
| Compliance | User constraints and runtime preserved; generated audio counts only if it is actually present and audible in the evaluated deliverable |

For quality, use a small anchored scale (1 poor, 3 usable, 5 strong) and a concrete observation or timestamp. Leave unreviewed dimensions blank/unknown; static preflight success is not visual or playback proof. Compare minimal and detailed briefs separately. Investigate extra response/context growth, service loops, creative limitations, and contract failures as separate causes before changing prompts. Preserve findings and measurements; do not turn one bad run into another universal creative rule.

The hand-back should show one compact comparison table with cost, responses, both elapsed and output duration, quality, and confounders. Recommend the smallest supported change and its next controlled test. Do not claim that removing aesthetic guidance fixed PIP, or that adding a contract worsened quality, when several variables changed together.
