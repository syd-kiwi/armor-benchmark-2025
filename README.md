# ARMOR Benchmark 2025

ARMOR Benchmark 2025 is a doctrine-grounded benchmark for evaluating how large language models (LLMs) answer multiple-choice questions about military decision-making, law-of-war concepts, rules of engagement, and professional ethics. The benchmark is designed for educational and analytical evaluation of model behavior against source-backed policy documents.

## Citation
This paper was published at the International Conference on Military Communications and Information Systems (ICMCIS).
Paper: https://arxiv.org/abs/2605.00245
Conference: https://icmcis.eu/

If you use this code or benchmark in your work, please cite our paper:

```bibtex
@misc{johns2026armorbenchmark,
  title        = {ARMOR-BENCH 2025: Evaluating Large Language Models for Military Decision-Making},
  author       = {Johns, Sydney},
  year         = {2026},
  eprint       = {2605.00245},
  archivePrefix = {arXiv},
  primaryClass = {cs.AI},
  url          = {https://arxiv.org/abs/2605.00245}
```

## What is in this repository?

This repository contains the benchmark dataset, source doctrine PDFs, question-generation and model-evaluation scripts, and aggregate analysis outputs.

| Path | Description |
| --- | --- |
| `dataset/questions_final_519.jsonl` | Final benchmark question set in JSON Lines format. Each record includes a question ID, source document, category, answer options, correct option, supporting evidence, and safety/answerability metadata. |
| `input_policy_documents/` | Source policy and doctrine PDFs used to build the benchmark, including law-of-war, rules-of-engagement, and ethics references. |
| `question_generation_pipeline/` | Scripts for cleaning doctrine text, generating MCQs with multiple LLMs, finding similar questions, and evaluating model answers. |
| `llm_preformance_results/` | Per-model result CSVs and aggregated score/refusal summaries. The directory name is preserved as it appears in the project. |
| `data_analysis_&_outputs/` | Analysis artifacts such as heatmaps, category-level accuracy tables, most-missed questions, similarity pairs, and the analysis notebook. |
| `requirements.txt` | Python dependencies for generation, evaluation, and analysis workflows. |

## Dataset format

The final benchmark is stored at `dataset/questions_final_519.jsonl`. Each line is a JSON object with fields such as:

- `qid`: stable question identifier.
- `doc_source`: source document family, for example `rules_of_engagement` or `law_of_war_2023`.
- `category`: doctrinal category for the question.
- `generator_model`: model family that generated the draft question.
- `question`: the multiple-choice question text.
- `option_A`, `option_B`, `option_C`, and optionally `option_D`: answer choices.
- `correct_option`: correct answer label.
- `supporting_evidence`: source-backed evidence justifying the answer.
- `is_allowed_to_answer`: whether the item is intended to be answerable in an educational/doctrinal setting.

## Installation

Create a Python environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Some workflows use hosted model APIs. Set only the keys needed for the providers you plan to run:

```bash
export OPENAI_API_KEY="..."
export ANTHROPIC_API_KEY="..."
export GEMINI_API_KEY="..."
export TOGETHER_API_KEY="..."
```

Local Hugging Face model evaluation expects downloaded models under a project-local `models/` directory.

## Evaluating models

Use `question_generation_pipeline/llm_decision_eval.py` to evaluate online or local models against the JSONL benchmark.

Evaluate one online model:

```bash
python question_generation_pipeline/llm_decision_eval.py \
  --online_only \
  --model_name gpt-4o-2024-08-06 \
  --dataset_path dataset/questions_final_519.jsonl \
  --output_path outputs
```

Evaluate all configured online models:

```bash
python question_generation_pipeline/llm_decision_eval.py \
  --online_only \
  --dataset_path dataset/questions_final_519.jsonl \
  --output_path outputs
```

Evaluate local models from `models/` only:

```bash
python question_generation_pipeline/llm_decision_eval.py \
  --local_only \
  --dataset_path dataset/questions_final_519.jsonl \
  --output_path outputs
```

The evaluator expects model responses to contain an answer in this form:

```text
Answer: [[C]]
```

Result CSVs include category, subcategory, question ID, raw response, extracted model choice, and correctness.

## Generating new questions

The multi-model question generator reads a doctrine/category CSV and writes JSONL MCQs:

```bash
python question_generation_pipeline/generate_mcqs_multi_llm.py \
  --input_csv doctrine_categories_v3.csv \
  --output_questions questions_generated_multi_llm_v3.jsonl \
  --questions_per_model 12
```

Optional arguments include `--max_categories` for small test runs.

## Analysis outputs

Existing analysis artifacts include:

- `data_analysis_&_outputs/accuracy_by_category_and_model.csv`: category-by-model accuracy matrix.
- `data_analysis_&_outputs/most_missed_questions.csv`: questions most frequently missed across evaluated models.
- `data_analysis_&_outputs/heatmap.png`: accuracy heatmap.
- `data_analysis_&_outputs/refusal_heatmap_percent.png`: refusal-rate heatmap.
- `llm_preformance_results/category_scores_by_model.csv`: long-form category score table.
- `llm_preformance_results/refusal_phrase_counts_by_model.csv`: refusal summary by model.

For exploratory analysis, open `data_analysis_&_outputs/llm_analysis.ipynb` in Jupyter after installing the requirements.

## Notes and limitations

- The benchmark is intended for research and educational evaluation, not operational decision support.
- Questions are multiple-choice and source-backed, so scores measure answer selection under this format rather than complete operational competence.
- Hosted-model results may vary over time as providers update model snapshots, APIs, and safety behavior.
- Directory names with special characters, such as `data_analysis_&_outputs/`, may need quoting or escaping in shell commands.

## Contributing

Contributions are welcome. Please open an issue or pull request for dataset corrections, additional documentation, reproducibility improvements, or new analysis outputs.

When contributing benchmark questions or results, include enough provenance to trace each item back to its source document and supporting evidence.

## Contact

For questions or inquiries, please contact [syd-kiwi](https://github.com/syd-kiwi).
