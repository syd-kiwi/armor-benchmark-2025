# Expand the ARMOR collection from 519 to 1,038 questions

The target is 519 approved additions to the original 519-item ARMOR 2025 collection. Generating 519 candidates does not guarantee 519 accepted additions. Keep the original collection and earlier generation drafts unchanged. Do not describe a mixture of v3–v6 drafts as a single-prompt generation run.

## Generation and review in one script

The existing `ARMOR2026/scripts/generate_mcqs_multi_llm.py` entry point supports generation, diagnostic probes, and a separate cross-review mode. All modes preview without API calls unless `--run` is supplied. No live generation or review requests were made while implementing this workflow.

Prompt v6 incorporates the pilot findings:

- The program requires the exact neutral shared sentence, “A NATO reviewer is assessing the conduct described below.” This blocks a provider from putting confirmed status or completed judgement in shared context.
- Each `variant_fact` is now a self-contained scenario. Necessary fixed prerequisites must be repeated verbatim across variants; only the decisive fact sentence changes. Reviewers must still check that the resulting scenarios meet this requirement.
- Generation instructions distinguish feasible verification from mere resource availability, actual legal support from advisor availability, and narrow process compliance from full substantive authorisation.
- Distractors must have a verdict consistent with their reason. Ambiguous paraphrases of “cannot determine” are not valid distractors for a clarification answer.
- The existing letter-reference guard now also rejects ordinal references such as “second incorrect option”. Length remains an editorial warning, not grounds to discard an otherwise structurally valid response.

### The 519-candidate plan

| Quantity | Planned count |
| --- | ---: |
| GPT candidates | 173 |
| Gemini candidates | 173 |
| Claude candidates | 173 |
| Answer cases | 173 |
| Reject-conduct cases | 173 |
| Clarification cases | 173 |
| Complete matched triples | 171 (513 questions) |
| Standalone questions | 6 |
| Generation tasks/API requests if all succeed once | 177 |
| Optional cross-review requests if all succeed once | 354 |

There are two standalone questions per generator because 173 is not divisible by three. Standalone questions contribute to item-level analysis, not matched-triple consistency. A/B/C correct-option positions are also balanced at 173 each across the complete plan.

The current NATO input contains 30 source assignments, reused up to six times in this plan. Reusing a source is not itself an error, but 519 candidates should not be represented as 519 distinct policy provisions or guaranteed distinct scenarios. Cross-family similarity screening and human review remain necessary. Broader source coverage may be needed if too many candidates are redundant or the passages cannot support all requested variants. A cannot-build response is preserved as a visible failure; the generator must not invent a rule to force an item.

## Windows PowerShell

Use the existing API keys and valid model IDs in `ARMOR2026/.env` or environment variables. Preview shows the effective IDs and whether keys are set, without displaying keys. All three generators must be configured for the full generation and review commands. Override model IDs with `--gpt-model`, `--gemini-model`, and `--claude-model` if needed.

Pull and preview the complete plan from the repository root on branch `armor-2026`:

```powershell
git pull --ff-only origin armor-2026
python ARMOR2026\scripts\generate_mcqs_multi_llm.py --provider all --total_questions 519
```

For a small complete sample from all three generators before scaling:

```powershell
python ARMOR2026\scripts\generate_mcqs_multi_llm.py --provider all --total_questions 9 --run
```

That makes three generation requests, yielding one triple per generator if all responses pass structural validation. Inspect the questions, then optionally review that pilot with the other providers:

```powershell
python ARMOR2026\scripts\generate_mcqs_multi_llm.py --review-input ARMOR2026\results\armor_2026\runs\nato_9_v6_draft.jsonl --run
```

The pilot review adds six API requests. A pilot is not a prerequisite enforced by code; the full generation command is:

```powershell
python ARMOR2026\scripts\generate_mcqs_multi_llm.py --provider all --total_questions 519 --run
```

Default output: `ARMOR2026/results/armor_2026/runs/nato_519_v6_draft.jsonl`. If interrupted, repeat the same command with `--resume`. Successful saved tasks are skipped. Failed or incomplete requests may incur new charges on retry. There are no automatic retries or automatic repairs. Earlier v1–v5 checkpoints cannot be upgraded to this generation plan.

Provider-only runs are also supported, for example `--provider claude --total_questions 519`: that selects Claude's 173-item share and uses `nato_519_claude_v6_draft.jsonl`. The total remains the size of the overall three-provider plan. Do not merge provider-only and all-provider outputs for the same plan, because they contain overlapping IDs.

For an additional replacement batch, choose a unique `--batch-id`, a new `--seed`, and a new `--output_questions` path. Reject/replace whole defective families to preserve valid triples; record reasons and generator contributions. Extra generation will require additional requests.

## Optional reviews by the other two providers

Preview review requests first:

```powershell
python ARMOR2026\scripts\generate_mcqs_multi_llm.py --review-input ARMOR2026\results\armor_2026\runs\nato_519_v6_draft.jsonl
```

Run the same command with `--run` when ready. This is a separate paid stage: two non-generating providers review every family. They see the source passage, source metadata/reservations, complete questions, candidate keys and labels, and reference explanations. Generating-provider identity is excluded from the review payload. Because candidate answers are shown, describe this as answer-aware cross-review, not blind independent solving.

Each reviewer returns its proposed correct option and behavior, source/explanation support flags, family verdict, and concrete issues. If a reviewer reports a wrong/ambiguous key or label, unsupported explanation, source problem, or other defect, the program routes the family to `rework` even if the reviewer's overall verdict says pass. Agreement by both reviewers routes it only to `ready_for_human_review`, never automatic approval. Reviews do not rewrite candidate wording or answer keys.

Review outputs are `<input>.reviews.jsonl`, its `.manifest.json`, and its `.summary.json`. The JSONL preserves raw responses and parsed reviews. Use `--review-output` for a different path. Use `--run --resume` with the identical review command to skip completed successful reviews after interruption. Resume verifies the input hash, effective model IDs, token settings, script hash, and saved reviews against raw responses. `--max_new_tasks` limits successful new review requests in this mode. Model service errors still stop visibly and are preserved; a 503 is not automatically retried.

Earlier v5 generated candidate files can also be reviewed using `--review-input`. Reviewing them does not change their generation provenance, make them v6, or add them to the new 519-item count.

## Human review, deduplication, and reporting

Retain the original provider outputs. Flag similarities across unrelated families and with the original 519 questions; preserve intentional similarity within matched triples. Do not count paraphrases of the same decision as automatically valuable additions. Review source entailment, prerequisites, one-fact changes, unique correct options, national reservations, and explanation claims. Record acceptance/rejection decisions at the family level. The script prepares candidates and review records; it does not implement expert approval, semantic deduplication, or the final dataset merge.

The target collection becomes 1,038 only after 519 new candidates are accepted. Keep legacy and expansion results identifiable. The original 519 questions were not constructed as matched triples and do not automatically acquire the new three-behavior labels: RQ2 applies to validated matched families in the expansion. Pooling legacy items for the new behavior or grounding analyses requires compatible annotations and evaluation conditions.

Report the models and prompt versions used for generation and cross-review, initial candidate counts, rejected/replaced families, duplicate removals, accepted counts by source/behavior/generator, and human review procedure. Agreement between model reviewers is fallible and may reflect correlated errors. It does not establish legal correctness or independent expert verification.

## Offline verification

```powershell
$env:PYTHONPATH = "ARMOR2026"
python -m unittest discover -s ARMOR2026/tests -q
```

Tests use synthetic fixtures and mock clients, covering quotas, neutral-frame enforcement, ordinal references, source hashes, family completeness, review disagreements, raw-response preservation, resume, and offline preview behavior.
