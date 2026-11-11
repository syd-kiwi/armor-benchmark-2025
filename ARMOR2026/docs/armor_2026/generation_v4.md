# Generation v4

Review of the completed Claude v3 batch found contradictions between shared context and variant facts, questions that asked invariant doctrine rather than scenario compliance, and stale option letters in explanations after permutation.

The single generator now instructs providers to:

- Keep every value of the changing fact exclusively in `variant_fact`, including uncertainty. Shared context contains only the setting and invariant facts.
- Ask the same scenario-specific compliance question in all variants, whose answer actually changes with the fact. Do not ask which general obligation exists.
- Establish every other condition in the source explicitly. A legal advisor being available does not establish actual support received.
- Check assembled stems for contradictions, missing-fact leakage, and whether clarification is necessary to answer the question.
- Explain distractors by substance, without letter references.

The parser rejects explicit option/choice/answer references to uppercase A/B/C in options, explanations, reservations, and fact lists before shuffling. It rejects common invariant question patterns, such as “What obligation…” and “What does … establish/state/require…”, in matched triples. These are limited syntactic guards, not semantic or legal verification. There is no additional judge model or automatic repair request. Contradiction detection and source entailment still require independent review.

Option word limits, the 1.35 length ratio, balanced positions, source-span provenance, and the quality report remain as documented in [generation_v3.md](generation_v3.md). Correct-longest frequency is reported for review; similar word counts do not remove all answer cues.

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
