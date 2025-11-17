import json
import random
from pathlib import Path

random.seed(42)

in_path = Path("../data/doctrine_sentences.jsonl")
out_path = Path("../data/annotation_sample.jsonl")

sentences = []
with in_path.open("r", encoding="utf-8") as f:
    for line in f:
        sentences.append(json.loads(line))

sample = random.sample(sentences, k=min(2000, len(sentences)))

with out_path.open("w", encoding="utf-8") as f:
    for row in sample:
        # empty labels for now, you fill these in
        row["labels"] = []
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

print("Wrote", len(sample), "sentences to", out_path)
