# Generation prompt v5

This update changes instructions sent to the question-generating model. It does not edit saved questions, add a judge model, rewrite answers after generation, or make live API requests during development.

The system instruction identifies the task as source-grounded assessment design and prioritizes one changing fact, valid counterfactual outcomes, comparable options, and explanations without positional references. The task prompt supplies the source, requested behavior order, output schema, and a six-stage drafting process:

1. Identify the narrow requirement actually stated by the source and one fact that controls its satisfaction.
2. Draft supported, prohibited, and unknown values of that fact while holding the decision and other prerequisites constant.
3. Write a short neutral shared context last. Apply the deletion test: without the variant fact, the context must not settle the question. Apply the substitution test: all three variants must fit the same context without contradiction.
4. Draft plausible, grammatically parallel options with comparable detail. Aim for 16–20 words each and at most two words between longest and shortest. Avoid padding, duplicate distractors, and an obviously more detailed correct choice.
5. Explain the rule, decisive fact, and conclusion by substance. Never refer to letters, numbers, ordinals, former/latter, or other option positions.
6. Check the assembled family and revise drafting failures before returning the JSON.

The prompt specifically addresses CDE-family leakage, actual legal support versus availability, governing-policy overreach, unnecessary source-rule repetition in the stem, and unsupported acronym expansions. If the source cannot support the requested variants, the generator must return a cannot-build reason.

These instructions do not guarantee compliance. Existing parser checks remain limited structural checks, and length remains a reported editorial warning. No claim of human verification, independent model consensus, or semantic validation is made. Review a small new sample before generating a full batch.

## PowerShell preview

```powershell
git pull --ff-only origin armor-2026
python ARMOR2026\scripts\generate_mcqs_multi_llm.py --provider claude --model claude-sonnet-4-6
```

This makes no API calls. When ready, add `--run --max_new_tasks 1` to request one task for inspection. Its raw checkpoint is `ARMOR2026/results/armor_2026/runs/nato_claude_v5_draft.jsonl.raw.jsonl`. After inspection, `--run --resume` continues that same v5 run.

Claude's share remains 16 questions from the total 50-item plan. Defaults use `nato_claude_v5_draft.jsonl`, analogous GPT/Gemini names, and `nato_50_v5_draft.jsonl` for all providers. Saved v4 and earlier drafts are unchanged. They cannot be resumed or upgraded into v5 because generation instructions changed. Keep them for comparison; running v5 creates new API usage. `--upgrade-checkpoint` remains a historical option and cannot migrate v4 into v5.

Offline checks cover plan behavior, provider adapter instruction delivery, existing validation and provenance, mock resume, and blocking cross-prompt upgrades. They do not demonstrate empirical improvements in generated question quality.
