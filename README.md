# ARMOR-BENCH 2025

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

> **Note:** Earlier project workflows may have used generation/evaluation scripts that are not included in this repository snapshot. The files currently tracked here are the dataset, source documents, dependency list, and result artifacts.

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
