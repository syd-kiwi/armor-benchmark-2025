# ARMOR 2026 results

No live model evaluations have been performed for this branch setup. Keep run files in `runs/` (ignored by git by default); explicitly add reviewed release artifacts when ready.

Each run has a JSON manifest with the dataset hash, requested model, API endpoint, prompt hash, context condition, temperature, token budget, repetitions, and scenario limit. Each response preserves actual returned model identity, provider ID, usage, finish reason, prompt, raw output, and question hash when available. Never put API keys in tracked files.

Use a new `run_id` and output path for every changed configuration. `--resume` skips IDs already written and requires identical inputs/settings. Transport errors and empty output are recorded separately and are not automatically retried by resume: use a new run ID for a documented retry. A truncated nonempty response remains available for annotation; inspect `finish_reason` and account for truncation in analysis.

Automatic judge outputs are draft labels. Final summaries require human-approved labels, with a named human `reviewer` when the original label was automatic. Use `--exploratory` only for clearly labeled exploratory summaries. `analyze` reports each group's denominators and missing labels; a partial annotation file is not a complete evaluation.
