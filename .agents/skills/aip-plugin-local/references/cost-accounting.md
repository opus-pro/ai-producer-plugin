# Client cost accounting

Use the host's task-read tool first to resolve the supplied task ID/title, completion state, and elapsed time. A `codex://threads/<id>` link identifies a live local task; a shared snapshot may omit unfinished work and detailed usage. Read only the relevant task and descendant usage records. Filter tool responses before displaying them: raw task/command output can contain transcripts, signed URLs, or credentials.

For Codex, use the bundled reader instead of rewriting a log parser each time:

```text
python3 <this-skill>/scripts/cost_report.py <task-id-or-codex-link> --rates <verified-rates.json> --output <ignored-report.json>
```

The default scope includes all turns and follow-ups. To isolate the original generation, pass `--turn <root-turn-id>` from the task's usage rows. The reader selects that turn and descendant receipts carrying its `root_turn_id`, while reconciling each complete log before filtering. Keep generation and subsequent review/edit costs separate. A child turn with no receipt or missing root-turn attribution cannot yet be assigned to a generation scope and is reported as incomplete. When querying a child directly, ancestor context IDs are read only to exclude inherited turns, without adding ancestor usage.

Without `--rates` it reports tokens and leaves USD unknown. Read current official pricing for the **actual** recorded model and requested tier before supplying rates. Do not assume today's model, price, long-context policy, or cache-write semantics will remain unchanged. The rates file has this shape (numbers below are synthetic, not product prices):

```json
{
  "source": "https://developers.openai.com/",
  "verified_on": "YYYY-MM-DD",
  "models": {
    "example-model": {
      "tier": "standard",
      "input": 10,
      "cached": 1,
      "output": 50,
      "long_context": {
        "threshold": 272000,
        "input_multiplier": 2,
        "cached_multiplier": 2,
        "output_multiplier": 1.5
      }
    }
  }
}
```

Prices are USD per million tokens. Use `long_context: null` only after verifying there is no applicable threshold rule. A null recorded service tier is estimated at the supplied standard rate and labeled as such. Unknown models, mismatched tiers, unsupported cache-write usage, missing receipts, or incomplete reconciliation prevent a complete USD total; they must not silently become zero cost.

The reader deduplicates `response_id`, filters receipts to their owning `thread_id` (forked histories can contain parent receipts), discovers descendant tasks from session metadata, and checks per-thread cumulative totals. It never sums cumulative checkpoints. Cached tokens are a subset of input; reasoning is a subset of output. For the supported zero-cache-write case, cost is `(input - cached) * input_rate + cached * cache_rate + output * output_rate`, divided by one million. Apply any long-context multipliers per request, not to the run's cumulative input.

Record main and child costs separately before summing them. Elapsed time belongs to the root task; do not add parallel child durations to it. Running-task results are snapshots. The report includes safe numeric per-response rows for optional stage allocation; label stages from actual operations and cover each response once, without inferring its purpose solely from a child task's name.

For a Claude task, use that host's available usage receipts and documented cost field; this script does not parse Claude logs. Separate an explicit API charge from an API-equivalent estimate on a subscription. If the requested host does not expose enough usage, say which fields are missing instead of estimating from text length or borrowing another task's rate.

Report client model tokens only unless the user requests broader cost. Keep backend credits, render/vendor fees, and separate tool charges outside that total. Preserve a reproducible local numeric receipt, but do not publish raw task logs, reasoning, or private identifiers. A successful install or a reduced skill word count is not a measured generation-cost improvement.
