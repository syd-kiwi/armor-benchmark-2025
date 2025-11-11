# ARMOR-BENCH (Doctrinal MCQ Benchmark) — Starter Repo

This repository is a **ready-to-extend scaffold** for building a doctrinally grounded, multiple-choice benchmark using a **BERT-based span extractor** (ground truth) + **template generation**. It avoids GPT for generation/evaluation.

## Pipeline (Makefile targets)
1. `prepare_data` → clean & split doctrine corpus (Military AI Law Corpus / Operational Ethics Corpus).
2. `train_bert_qa` → fine-tune BERT QA on small labeled examples.
3. `extract_spans` → run BERT QA to auto-label answer spans with provenance.
4. `classify_spans` (optional) → tag spans into the 14 categories.
5. `generate_questions` → turn spans into 3-option MCQs (A/B/C) + distractors.
6. `validate_dataset` → dedupe similar items (cosine), schema checks.
7. `evaluate_llms` → pose MCQs to models; compute Accuracy + Refusal Rate.
8. `generate_report` → produce LaTeX tables/plots in `outputs/reports`.

## Quickstart
```bash
pip install -r requirements.txt
make all
```

- Add your PDFs/TXT to `data/raw_docs/`.
- Provide small seed labels under `data/label_examples/` (see sample files).

## Metrics (kept simple)
- **Accuracy** (primary)
- **Refusal Rate** (ethical restraint)
- Optional: Paraphrase consistency (toggle in `configs/eval.yaml`)

## 14 Categories (example)
Civilian Harm, Detainees, Orders vs Conscience, Cover-ups, Moral Courage, Cultural Sensitivity, Dual Loyalty,
PID/Hostile Intent, Proportionality/Necessity, Escalation, Weapons Control, Mission ROE, Civilians on Battlefield, Accountability.

---
