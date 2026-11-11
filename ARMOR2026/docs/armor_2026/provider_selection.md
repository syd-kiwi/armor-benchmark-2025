# One script: choose a provider, model, or diagnostic probe

All question generation and provider tests now use `scripts/generate_mcqs_multi_llm.py`. The separate Gemini-only entry point was consolidated into it. The earlier paired-format analysis pipeline is separate from this MCQ generator.

Run from the repository root in PowerShell:

```powershell
git pull --ff-only
python ARMOR2026\scripts\generate_mcqs_multi_llm.py --provider claude --model claude-sonnet-4-6 --probe
```

That is a preview only, without API calls. Add `--run` for **one small paid diagnostic request**:

```powershell
python ARMOR2026\scripts\generate_mcqs_multi_llm.py --provider claude --model claude-sonnet-4-6 --probe --run
```

The probe requests a small JSON confirmation with a 1024-token output budget. It prints whether the expected object was returned, creates no question/checkpoint files, and tests only basic API access. A reasoning model might exhaust the budget without returning the expected object. Only the selected provider's SDK and API key are needed; GPT and Gemini are not initialized for a Claude-only run. Provider credentials remain in `.env` or environment variables.

For Gemini or GPT, replace `claude` with `gemini` or `gpt` and supply the matching provider model ID. Omit `--model` to use that provider's `.env` setting. For `--provider all`, use the individual `--gpt-model`, `--gemini-model`, and `--claude-model` flags instead. The default remains `all`. A probe requires a single provider.

## Generate only one provider's share

Once the Claude probe works:

```powershell
python ARMOR2026\scripts\generate_mcqs_multi_llm.py --provider claude --model claude-sonnet-4-6 --run
```

This generates only **16 Claude draft questions** in `ARMOR2026/results/armor_2026/runs/nato_claude_v4_draft.jsonl`. It does not call GPT or Gemini. The total plan still has 50 questions: GPT 17, Gemini 17, Claude 16. Selecting a provider chooses its share rather than reallocating all 50 to it. Source assignments and task IDs remain those of the full plan. Five matched triples plus one standalone are planned for Claude. Model and human review requirements are unchanged.

Default outputs are distinct: `nato_gpt_v4_draft.jsonl`, `nato_gemini_v4_draft.jsonl`, `nato_claude_v4_draft.jsonl`, and `nato_50_v4_draft.jsonl` for all providers. Use `--output_questions` to choose another new path. Do not use the path of a saved three-provider or older Gemini-only run for a provider-only run.

To stop after the first generation task, add `--max_new_tasks 1`. This saves a raw checkpoint, not the complete final file. To finish later, use the same provider/model/output with `--run --resume`, without that task limit. Successful tasks in that run are skipped. No automatic retries are made; resumed failed requests can incur charges.

Resume requires identical source data, task plan, effective model IDs, script hash, and token settings. Previous-version checkpoints remain intact, but their script hashes/formats are not migrated by this update. Start a new provider-only output for further work without repeating other providers. Existing successful GPT records in older raw files are not automatically merged or replaced; retain those files for later reconciliation. Do not edit manifests to bypass the guard or run concurrent processes against the same output.

Errors now include a sanitized HTTP status and provider message, redacting configured keys and URLs. This helps distinguish service errors such as 503 from permission, model access, or generation-validation failures. No live calls were made while preparing this update; tests use synthetic fixtures and mock clients.

## Generation v4

See [generation_v4.md](generation_v4.md) for neutral shared contexts, compliance questions, and option-letter validation. Start a new v4 output; older checkpoints and drafts remain intact. Resume only the same interrupted v4 run with identical inputs, script, model IDs, and settings.
