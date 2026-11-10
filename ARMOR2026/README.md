# ARMOR 2026 development

All 2026 work is consolidated here: `armor2026/` contains the earlier paired-format pipeline, `scripts/` contains the three-provider MCQ generator, `data/nato/` contains 30 source snippets and provenance, `input_policy_documents/` contains the NATO PDF, and `paper/` contains the current LaTeX draft copied from the paper repository.

## One generation script for all providers

Use [provider selection and diagnostic commands](docs/armor_2026/provider_selection.md). `scripts/generate_mcqs_multi_llm.py` supports `--provider gpt`, `--provider gemini`, `--provider claude`, or `--provider all`, along with `--model` for one selected provider and `--probe` for a small API test. Provider-only runs have separate output files and do not repeat other providers. The former Gemini-only entry point has been consolidated into this script; saved run files are not moved or deleted.

## Prepare the 50-question pilot

See [setup and Windows commands](docs/armor_2026/generate_50.md). The allocation is **17 GPT, 17 Gemini, 16 Claude**. Edit `.env` using `.env.example` for keys and model IDs. The generator defaults to planning only and needs `--run` for paid calls. No pilot questions have been generated. Its flat draft MCQs require review and conversion before use with the paired-format pipeline below.

This branch develops the next ARMOR benchmark: expanded doctrinal coverage and evaluation of whether models answer, reject proposed prohibited conduct, or identify missing information appropriately. The published ARMOR 2025 data and results remain in their original paths. The original 2025 files remain at the repository root. Run all commands on this page from the `ARMOR2026` folder.

**Status:** runnable development pipeline with offline tests, the original NATO PDF, and six draft passage selections. No new questions have been approved and no live model evaluations have been run as part of this setup.

## New NATO source

NATO Standardization Office, *Allied Joint Doctrine for Joint Targeting*, AJP-3.9, Edition B, Version 1, November 2021.

- PDF: [`input_policy_documents/AJP-3.9_EDB_V1_E.pdf`](input_policy_documents/AJP-3.9_EDB_V1_E.pdf)
- Edition, checksum, URL, and reservation notes: [`input_policy_documents/AJP-3.9_EDB_V1_E.source.json`](input_policy_documents/AJP-3.9_EDB_V1_E.source.json)
- [Official publication page](https://www.gov.uk/government/publications/allied-joint-doctrine-for-joint-targeting-ajp-39a)

Questions must specify their doctrinal framework and preserve applicable national reservations. Explaining that conduct is prohibited is a substantive answer, not automatically a refusal.

## ARMOR 2026 files

| Path | Purpose |
| --- | --- |
| `armor2026/` | Command-line extraction, generation, validation, querying, annotation, and analysis |
| `configs/armor_2026/pilot.json` | Initial passage selections and reservation review notes |
| `dataset/armor_2026/passages.jsonl` | Six extracted **draft** page selections awaiting review |
| `schemas/armor_2026_question.schema.json` | Question schema, provenance, expected behavior, and review metadata |
| `prompts/armor_2026/` | Versioned generation and response grading instructions |
| `docs/armor_2026/design.md` | Pilot design, comparisons, scope, and limitations |
| `docs/armor_2026/annotation.md` | Behavior labels, correctness judgments, and metric denominators |
| `docs/armor_2026/related_work.bib` | NATO source and the six comparison works cited by WARBENCH, plus WARBENCH |
| `results/armor_2026/` | Run conventions; local runs are ignored by git by default |
| `tests/test_pipeline.py` | Offline tests for pairing, evidence, leakage, resume, and refusal scoring |

## Install the small CPU-only environment

From the repository root, first run `cd ARMOR2026`.

Python 3.10 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-2026.txt
python -m armor2026 --help
python -m unittest discover -s tests -v
```

On Windows, activate with `.venv\Scripts\Activate.ps1` in PowerShell or `.venv\Scripts\activate.bat` in Command Prompt. The original `requirements.txt` is retained for historical workflows; the 2026 pipeline needs neither CUDA nor a local model.

## 1. Extract and review source passages

Reproduce extraction into new working files:

```bash
python -m armor2026 extract \
  --pages results/armor_2026/runs/pages.jsonl \
  --output results/armor_2026/runs/passages.jsonl
```

The input PDF checksum is verified. Selections contain full PDF pages, including adjacent context. Review them against the PDF, trim each `text` to the intended complete provision, verify reservations, and set `review_status` to `approved` and `reviewer` to the human reviewer's name. Do not approve automatically. See [dataset instructions](dataset/armor_2026/README.md).

## 2. Generate paired draft questions

Inspect requests first, without an API key or paid calls. Replace `YOUR_MODEL_ID` with a model ID supported by the chosen provider:

```bash
python -m armor2026 generate \
  --passages results/armor_2026/runs/passages.jsonl \
  --output results/armor_2026/runs/generation_requests.jsonl \
  --batch-id nato-pilot-01 --model YOUR_MODEL_ID --per-passage 2 --dry-run
```

For live generation, set the key in your shell, remove `--dry-run`, and use a new output file such as `dataset/armor_2026/candidates.jsonl`. Live generation requires approved source passages. Each scenario yields an MCQ and an open-response record sharing `scenario_id`, source metadata, expected behavior, and reference answer. The generator cannot approve its own questions.

The default API is OpenAI-compatible Chat Completions over HTTPS. For Together, add:

```text
--base-url https://api.together.xyz/v1 --api-key-env TOGETHER_API_KEY
```

Use a model that supports Chat Completions and the configured temperature/token parameters. For generation, choose a token budget large enough for all requested scenarios. Generation raw outputs are checkpointed in `<output>.raw.jsonl`; malformed or truncated generations fail visibly. Generation has no automatic resume: inspect preserved outputs and choose a new batch ID/output for a retry.

Validate candidate structure and exact evidence quotations:

```bash
python -m armor2026 validate dataset/armor_2026/candidates.jsonl
```

Review BOTH versions, verify one correct MCQ option and factual equivalence, and check the expected behavior and reference answer. Save only approved pairs as `dataset/armor_2026/reviewed.jsonl`, with named reviewers. Keep scenario families in a single split. Structural checks do not establish legal correctness or semantic uniqueness.

```bash
python -m armor2026 validate dataset/armor_2026/reviewed.jsonl --approved
```

## 3. Run models with and without source context

This command saves prompts only. Remove `--dry-run` and choose a new output/run ID when ready for live evaluation:

```bash
python -m armor2026 run \
  --questions dataset/armor_2026/reviewed.jsonl \
  --output results/armor_2026/runs/model-no-context-preview.jsonl \
  --run-id model-no-context-preview --model YOUR_MODEL_ID \
  --condition without_context --repeats 1 --dry-run
```

Run the matched condition with `--condition with_context`, a new `--run-id`, and a new output file. Both conditions state the framework. Only `with_context` supplies the source passage and reservation notes. Reference answers and grading labels are never sent to the evaluated model. `--limit N` selects complete scenario pairs.

Every response is checkpointed. To resume an interrupted evaluation, repeat exactly the same command with `--resume`. Dataset or configuration changes require a new run. Errors already recorded are not silently retried. See [run conventions](results/armor_2026/README.md).

## 4. Annotate responses and summarize

After a live run, create a human annotation template:

```bash
python -m armor2026 annotate \
  --questions dataset/armor_2026/reviewed.jsonl \
  --responses results/armor_2026/runs/model-no-context.jsonl \
  --output results/armor_2026/runs/labels.jsonl --mode human
```

Alternatively, `--mode judge --model YOUR_JUDGE_MODEL_ID` calls an API to propose **draft** labels. Keep independent human validation and adjudication separate. Each annotation records observed behavior, correctness, appropriateness, prohibited-conduct endorsement, and rationale. Follow the [annotation guide](docs/armor_2026/annotation.md), then mark adjudicated labels approved. Automatic labels also require a named human `reviewer` for final reporting.

```bash
python -m armor2026 analyze \
  --responses results/armor_2026/runs/model-no-context.jsonl \
  --labels results/armor_2026/runs/labels.jsonl \
  --output results/armor_2026/runs/summary.json
```

Reports show denominators, missing labels, refusals, correctness, appropriateness, and technical failures separately. `--exploratory` permits valid unapproved labels but marks the report exploratory. This is descriptive analysis, not a paired statistical significance test. Review related scenarios and repetitions as correlated observations.
