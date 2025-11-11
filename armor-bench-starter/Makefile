# ARMOR-BENCH pipeline
.PHONY: all prepare_data train_bert_qa extract_spans classify_spans generate_questions validate_dataset evaluate_llms generate_report

all: prepare_data train_bert_qa extract_spans generate_questions validate_dataset evaluate_llms generate_report

prepare_data:
	python scripts/preprocess_docs.py --input data/raw_docs --output data/clean_docs

train_bert_qa:
	python scripts/train_bert_qa.py --train data/label_examples/train_qa.json --val data/label_examples/val_qa.json --out outputs/models/bert_qa

extract_spans:
	python scripts/run_span_extractor.py --model outputs/models/bert_qa --docs data/clean_docs --out data/spans/spans.jsonl

classify_spans:
	python scripts/run_classifier.py --in data/spans/spans.jsonl --out data/spans/labeled_spans.jsonl

generate_questions:
	python scripts/generate_questions.py --in data/spans/spans.jsonl --out data/questions/questions.jsonl

validate_dataset:
	python scripts/validate_questions.py --in data/questions/questions.jsonl --out data/questions/questions.valid.jsonl --dedupe

evaluate_llms:
	python scripts/evaluate_llms.py --questions data/questions/questions.valid.jsonl --models configs/model_list.yaml --out outputs/armor_eval.csv

generate_report:
	python scripts/generate_report.py --in outputs/armor_eval.csv --out outputs/reports/armor_results.tex
