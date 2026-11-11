# Generation v3: matched scenarios and quality checks

The same generator entry point now asks for `shared_context`, `decision_question`, `changed_variable`, and `variant_fact` alongside the options, evidence, explanation, and fact lists. Each triple must reuse the first three fields. Only the fourth varies. The script assembles the displayed question. Human review must still confirm that exactly one meaningful fact dimension changed.

The expected behaviors remain:

- `answer`: the supplied source and facts support a determination.
- `reject_conduct`: the supplied provision prohibits the proposed conduct on the stated facts.
- `clarify`: an essential missing fact can change the result, with no already decisive prohibition.

## Source grounding

The prompt forbids turning definitions into prohibitions, demanding direct NAC approval for every subordinate ROE, inventing PID thresholds, or automatically classifying a violation as a war crime. It distinguishes meeting one doctrinal condition from full authorization. A source that cannot support the requested variants must produce a visible cannot-build reason.

For the PID assignment, NATO-003 is combined with NATO-022, which supplies the actual pre-engagement verification requirement. Both original passages, source locations, and hashes are retained in `source_spans`. The input CSVs are unchanged. Other snippets retain their original source span and reservation metadata. Exact evidence matching is checked; semantic entailment still requires independent review.

## Options and answer positions

Options must contain 10–30 whitespace-separated words and have a longest/shortest ratio no greater than 1.35. The prompt aims for 15–20 words and parallel, plausible interpretations. Full source sentences of eight or more words are rejected when copied into the question stem. Explanations belong in `reference_answer` and must avoid option-letter references because letters change.

The program permutes existing option strings and updates the key, retaining the mapping and original provider key. It never rewrites options during permutation. A/B/C counts differ by at most one for each provider. The full 50-item plan has A=17, B=17, C=16. Balanced positions do not guarantee absence of other answer cues.

The final `.jsonl.quality.json` sidecar reports behavior and answer-position counts, correct-longest frequency, and first-longest/first-shortest heuristic accuracy. A warning is recorded when relevant length cues exceed 60%; it does not certify dataset quality. All generated items remain drafts. Review source interpretation, counterfactual pairing, reservations, and distractor plausibility before evaluation.

## Windows commands

From the repository root on branch `armor-2026`:

```powershell
git pull --ff-only origin armor-2026
python ARMOR2026\scripts\generate_mcqs_multi_llm.py --provider claude --model claude-sonnet-4-6
```

This previews the plan without API calls. To generate only the first task when ready:

```powershell
python ARMOR2026\scripts\generate_mcqs_multi_llm.py --provider claude --model claude-sonnet-4-6 --run --max_new_tasks 1
```

Review the saved raw checkpoint, then finish the same v3 run:

```powershell
python ARMOR2026\scripts\generate_mcqs_multi_llm.py --provider claude --model claude-sonnet-4-6 --run --resume
```

Claude still receives 16 of the 50 planned questions. Default output is `ARMOR2026/results/armor_2026/runs/nato_claude_v3_draft.jsonl`. Other defaults are `nato_gpt_v3_draft.jsonl`, `nato_gemini_v3_draft.jsonl`, and `nato_50_v3_draft.jsonl`. Use a new `--output_questions` path for another run. New runs incur new API usage when `--run` is supplied; old successful generations are not reused across versions.

Generation v3 cannot resume or upgrade older v1/v2 checkpoints because source composition, question schema, and the plan changed. Keep old results intact. Do not edit manifests. Within v3, resume skips completed successful tasks and requests failed or incomplete tasks again. There are no automatic retries. A structural validation failure saves the raw response and stops; inspect it before retrying.

## Offline checks

```powershell
$env:PYTHONPATH = "ARMOR2026"
python -m unittest discover -s ARMOR2026/tests -q
```

Tests use synthetic fixtures and mock clients. They do not generate benchmark questions or contact model APIs.
