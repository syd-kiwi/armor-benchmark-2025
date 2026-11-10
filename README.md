# ARMOR 2026 development

This branch develops the next ARMOR benchmark: expanded doctrinal coverage and evaluation of whether models answer, reject proposed prohibited conduct, or identify missing information appropriately. The published ARMOR 2025 data and results remain in their original paths. The default `main` branch holds the 2025 work.

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

---

# ARMOR-BENCH 2025 (published benchmark)

ARMOR-BENCH 2025 is a doctrine-grounded benchmark for evaluating how large language models (LLMs) answer multiple-choice questions about military decision-making, law-of-war concepts, rules of engagement, and professional ethics. The benchmark is intended for educational and analytical evaluation of model behavior against source-backed policy documents, not for operational decision support.

## Publication and citation

The ARMOR-BENCH 2025 paper was published at the International Conference on Military Communications and Information Systems (ICMCIS).

- Paper: <https://arxiv.org/abs/2605.00245>
- Conference: <https://icmcis.eu/>

If you use this dataset or benchmark outputs in your work, please cite the paper:

```bibtex
@misc{johns2026armorbenchmark,
  title         = {ARMOR-BENCH 2025: Evaluating Large Language Models for Military Decision-Making},
  author        = {Johns, Sydney},
  year          = {2026},
  eprint        = {2605.00245},
  archivePrefix = {arXiv},
  primaryClass  = {cs.AI},
  url           = {https://arxiv.org/abs/2605.00245}
}
```

## Repository contents

| Path | Description |
| --- | --- |
| `dataset/questions_final_519.jsonl` | Final benchmark question set in JSON Lines format. Each line is one multiple-choice question with source, category, options, answer key, supporting evidence, and answerability metadata. |
| `input_policy_documents/` | Source doctrine and policy files used to construct the benchmark, including rules-of-engagement, law-of-war, and joint ethics references. |
| `input_policy_documents/document_&_category_passages.xlsx` | Spreadsheet mapping source-document passages to benchmark categories. Quote or escape the path in shell commands because it contains `&`. |
| `llm_preformance_results/` | Per-model response/evaluation CSVs plus aggregate category-score, refusal-rate, and similarity outputs. The directory name is preserved as it appears in the project. |
| `requirements.txt` | Python dependencies useful for inspecting the dataset and reproducing related analysis workflows. |

> **Historical note:** The original 2025 generation/evaluation scripts were not included in the published snapshot. This branch adds the separate `armor2026/` implementation described above.

## Dataset overview

The final dataset contains **519** questions in `dataset/questions_final_519.jsonl`. Each line is a JSON object with fields such as:

- `qid`: stable question identifier.
- `span_id`: source-passage or generation-span identifier.
- `doc_source`: source document family, for example `rules_of_engagement` or `law_of_war_2023`.
- `category`: doctrinal category for the question.
- `generator_model`: model family that generated the draft question.
- `question`: multiple-choice question text.
- `option_A`, `option_B`, `option_C`, and, when present, `option_D`: answer choices.
- `correct_option`: correct answer label.
- `supporting_evidence`: source-backed evidence justifying the answer.
- `is_allowed_to_answer`: whether the item is intended to be answerable in an educational/doctrinal setting.
- `_source_file`: source generation file recorded for provenance.

### Example record shape

```json
{
  "qid": "rules_of_engagement__Mission-Specific_ROE_Constraints__ROW0001__gpt_Q01",
  "span_id": "rules_of_engagement__Mission-Specific_ROE_Constraints__ROW0001__gpt",
  "doc_source": "rules_of_engagement",
  "category": "Mission-Specific ROE Constraints",
  "generator_model": "gpt",
  "question": "...",
  "option_A": "...",
  "option_B": "...",
  "option_C": "...",
  "correct_option": "C",
  "supporting_evidence": "...",
  "is_allowed_to_answer": "true",
  "_source_file": "questions_generated_multi_llm.jsonl"
}
```

## Result files

Per-model result files in `llm_preformance_results/` follow this naming pattern:

```text
<model_name>_result.csv
```

These CSVs include:

- `Category`
- `Subcategory`
- `QID`
- `RawResponse`
- `AIChoice`
- `Result`

Aggregate files include:

- `llm_preformance_results/category_scores_by_model.csv`: category-level score summaries by model.
- `llm_preformance_results/refusal_phrase_counts_by_model.csv`: refusal counts and refusal rates by model.
- `llm_preformance_results/refusal_phrase_counts_by_category_all_models.csv`: refusal counts and refusal rates by category across models.
- `llm_preformance_results/question_similarity_pairs.csv`: question-pair similarity output used to inspect possible overlap or duplication.

## Getting started

Create a Python environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Some exploratory workflows may use hosted model APIs. Set only the keys needed for the providers you plan to use:

```bash
export OPENAI_API_KEY="..."
export ANTHROPIC_API_KEY="..."
export GEMINI_API_KEY="..."
export TOGETHER_API_KEY="..."
```

## Inspecting the dataset

Count records:

```bash
python - <<'PY'
from pathlib import Path

path = Path("dataset/questions_final_519.jsonl")
print(sum(1 for _ in path.open()))
PY
```

Preview the first question:

```bash
python - <<'PY'
import json
from pathlib import Path

path = Path("dataset/questions_final_519.jsonl")
with path.open() as handle:
    first = json.loads(next(handle))
print(json.dumps(first, indent=2))
PY
```

Load result summaries with pandas:

```bash
python - <<'PY'
import pandas as pd

scores = pd.read_csv("llm_preformance_results/category_scores_by_model.csv")
print(scores.head())
PY
```

## Notes and limitations

- ARMOR-BENCH 2025 is intended for research, education, and model-behavior analysis; it is not a substitute for expert legal, ethical, or command judgment.
- Questions are multiple-choice and source-backed, so scores measure answer selection in this constrained format rather than complete operational competence.
- Hosted-model behavior can change as providers update model snapshots, APIs, and safety systems.
- Directory names with special characters, such as `input_policy_documents/document_&_category_passages.xlsx`, should be quoted or escaped in shell commands.
- The result directory is named `llm_preformance_results/` in the repository; the spelling is intentionally preserved in this README so paths remain copy-pasteable.

## Contributing

Contributions are welcome. Please open an issue or pull request for dataset corrections, documentation improvements, reproducibility notes, or additional analysis artifacts.

When contributing benchmark questions or results, include enough provenance to trace each item back to its source document and supporting evidence.

## Contact

For questions or inquiries, please contact [syd-kiwi](https://github.com/syd-kiwi).
