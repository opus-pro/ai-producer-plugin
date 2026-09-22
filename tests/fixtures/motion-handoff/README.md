# Motion Library handoff scenarios

`scenarios.json` contains synthetic existing-project requests, the deterministic-copy baseline outcome, and observable expectations for Motion Library adaptation. It covers semantic automatic placement, an explicit-time conflict, direct unchanged insertion, hardcoded source derivation, missing facts, split cutout spans, an unavailable package, and a legacy reference whose "here" target remains explicit. It contains no service credentials, real projects, transcripts or user media.

`evaluate.py` scores a candidate agent trace expressed as JSON. Each trace names a `scenario_id`, `route`, `context_reads`, `window`, `calls`, `questions`, `grounded_values`, `refused`, and the returned `page_url` when delivery succeeds. Run it with:

```bash
python3 tests/fixtures/motion-handoff/evaluate.py candidate-traces.json
```

The candidate file must contain each scenario exactly once. To create model inputs without leaking the recorded baseline or expected answer, run `python3 tests/fixtures/motion-handoff/evaluate.py --emit-model-cases`; the emitted records contain only the request, resolved reference and synthetic project context.

The offline repository suite validates the scenario bank and evaluator with deterministic traces. It does not execute a model, authenticate to AI Producer, render a template, or establish visual fidelity. An actual agent evaluation supplies candidate traces from repeated runs, then combines this rubric with human review of semantic fit and recognizable template design.
