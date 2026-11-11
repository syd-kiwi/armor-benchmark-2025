# Generation v4

Review of the completed Claude v3 batch found contradictions between shared context and variant facts, questions that asked invariant doctrine rather than scenario compliance, and stale option letters in explanations after permutation.

The single generator now instructs providers to:

- Keep every value of the changing fact exclusively in `variant_fact`, including uncertainty. Shared context contains only the setting and invariant facts.
- Ask the same scenario-specific compliance question in all variants, whose answer actually changes with the fact. Do not ask which general obligation exists.
- Establish every other condition in the source explicitly. A legal advisor being available does not establish actual support received.
- Check assembled stems for contradictions, missing-fact leakage, and whether clarification is necessary to answer the question.
- Explain distractors by substance, without letter references.

The parser rejects explicit option/choice/answer references to uppercase A/B/C in options, explanations, reservations, and fact lists before shuffling. It rejects common invariant question patterns, such as “What obligation…” and “What does … establish/state/require…”, in matched triples. These are limited syntactic guards, not semantic or legal verification. There is no additional judge model or automatic repair request. Contradiction detection and source entailment still require independent review.

Option lengths of 10–30 words and a longest/shortest ratio of 1.35 remain drafting targets. Deviations are now editorial warnings in `length_warnings` in the quality report, rather than generation failures. Balanced positions and source-span provenance remain as documented in [generation_v3.md](generation_v3.md). Correct-longest frequency is reported for review; similar word counts do not remove all answer cues.

## PowerShell

Pull and preview from the repository root on branch `armor-2026`:

```powershell
git pull --ff-only origin armor-2026
python ARMOR2026\scripts\generate_mcqs_multi_llm.py --provider claude --model claude-sonnet-4-6
```

When ready, generate one task for inspection:

```powershell
python ARMOR2026\scripts\generate_mcqs_multi_llm.py --provider claude --model claude-sonnet-4-6 --run --max_new_tasks 1
```

This makes paid API requests only when `--run` is present. Inspect the raw checkpoint before completing the same v4 run with `--run --resume` and without `--max_new_tasks`. Claude's share remains 16 questions. The new default output is `ARMOR2026/results/armor_2026/runs/nato_claude_v4_draft.jsonl`; analogous filenames apply to other providers and the full plan.

Existing v3 drafts are preserved and not reused. Do not resume or upgrade them with v4 or edit their manifests. Start a separate output, which incurs fresh API usage if run. There are no live model calls in the offline tests.

## Recover the v4 length-check failure

The length-check fix keeps the same v4 prompt, task plan, and output format. Only the immediately preceding v4 script from commit `b4faac4` is eligible for a checked upgrade (Git LF and Windows CRLF checkouts are recognized). Models, sources, task plan, and token settings must match exactly. Older v1–v3 or locally modified script versions remain blocked.

```powershell
git pull --ff-only origin armor-2026
python ARMOR2026\scripts\generate_mcqs_multi_llm.py --provider claude --model claude-sonnet-4-6 --run --resume --upgrade-checkpoint
```

The old manifest is backed up as `.json.before-length-fix.json`; raw checkpoint lines and successful records remain intact. A saved response explicitly recorded as a length-only validation failure is revalidated against all remaining checks and appended as a recovered draft only if it passes. The recovery entry records that no API call was made. Responses failing evidence, schema, or other checks are not automatically accepted. The script does not rewrite or shorten options.

Recovery requires that the raw checkpoint contains the full response. Other failed or incomplete tasks still require new requests when the run continues, and those requests can incur charges. Successful tasks are skipped. After this upgrade, normal `--resume` is sufficient; use `--upgrade-checkpoint` again only if explicitly recovering another saved length-only failure. Completed final files cannot be resumed or overwritten.
