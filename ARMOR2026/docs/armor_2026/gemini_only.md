# Diagnose and generate with Gemini only

The original three-provider script and its checkpoints are unchanged. This separate entry point never creates OpenAI or Anthropic clients and never opens their checkpoint files. It uses the same original 50-question plan, then selects only Gemini's seven tasks (17 questions). Model selection comes from `GEMINI_MODEL` in `.env`, or an explicit `--model` override. Only `GEMINI_API_KEY` is required.

From the repository root in PowerShell:

```powershell
git pull --ff-only
python ARMOR2026\scripts\generate_gemini_only.py --probe
```

The command above is a preview only. To make **one small paid diagnostic request**, without generating benchmark questions:

```powershell
python ARMOR2026\scripts\generate_gemini_only.py --probe --run
```

The probe asks for `OK` with an output budget of 512 tokens. It prints finish reasons and whether `OK` was returned. A successful probe establishes only basic request handling, not support for the full prompt, valid generated questions, or reliable future availability. A reasoning model may use the small budget without returning visible text.

Errors show sanitized status and message, including 500/503 when Google supplies them. Keys and URLs are redacted. No automatic retries are performed. A failed probe creates no output files. Share only the sanitized error if diagnosis is still needed.

To test **one actual Gemini generation task** (three draft questions), without repeating GPT:

```powershell
python ARMOR2026\scripts\generate_gemini_only.py --run --max_new_tasks 1
```

On success this pauses with a Gemini-only raw checkpoint. To complete Gemini's remaining tasks:

```powershell
python ARMOR2026\scripts\generate_gemini_only.py --run --resume
```

After a failure, the same resume command retries the failed/incomplete Gemini tasks; successful Gemini tasks are skipped. Retries can incur charges. A crash before checkpoint write can cause that task to be called again. Model IDs, token budget, plan, or prompt changes require a new `--output_questions` path. Do not use the original three-provider output path with this script. Do not run two processes against the same path.

Final output: `ARMOR2026/results/armor_2026/runs/nato_gemini_only.jsonl`, containing **17 draft MCQs**, not all 50 questions. Five matched triples plus two standalone items are planned. This file uses the original Gemini task IDs so provenance can be reconciled with GPT/Claude later; no automatic merge or replacement of existing provider results is performed. Human review is still required.

Only offline mocked tests were run while adding this entry point. No live probe or generation was run by the assistant.
