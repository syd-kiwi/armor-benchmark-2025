import json
from pathlib import Path
from collections import defaultdict
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from config_labels import LABELS

in_path = Path("../data/doctrine_spans_labeled.jsonl")
out_path = Path("../data/questions_raw.jsonl")

rows = []
with in_path.open("r", encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        if not row.get("labels"):
            continue
        rows.append(row)

texts = [r["text"] for r in rows]
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

label_to_indices = defaultdict(list)
for idx, r in enumerate(rows):
    for lab in r["labels"]:
        label_to_indices[lab].append(idx)

def pick_distractor_labels(idx, top_k=20):
    vec = embeddings[idx].reshape(1, -1)
    sims = cosine_similarity(vec, embeddings)[0]
    sims[idx] = -1.0

    sorted_idx = np.argsort(-sims)
    target_labels = set(rows[idx]["labels"])
    candidates = []
    for j in sorted_idx:
        labels_j = set(rows[j].get("labels", []))
        if not labels_j:
            continue
        if labels_j.isdisjoint(target_labels):
            candidates.extend(list(labels_j))
        if len(candidates) >= 5:
            break

    candidates = [c for c in candidates if c not in target_labels]
    candidates = list(dict.fromkeys(candidates))
    if len(candidates) < 2:
        other = [l for l in LABELS if l not in target_labels]
        candidates.extend(other)
    return candidates[:2]

def make_mcq(entry_id, row, distractor_labels):
    correct = row["labels"][0]
    options = [correct] + distractor_labels
    np.random.shuffle(options)
    correct_index = options.index(correct)
    correct_letter = ["A", "B", "C"][correct_index]

    question = (
        "Which doctrinal category best matches the following clause from official guidance?"
    )

    return {
        "id": entry_id,
        "question": question,
        "context": row["text"],
        "options": options,
        "correct_answer": correct,
        "correct_option": correct_letter,
        "meta": {
            "source": row.get("source"),
            "page": row.get("page"),
            "labels_all": row.get("labels", []),
        },
    }

items = []
for idx, row in enumerate(rows):
    distractors = pick_distractor_labels(idx)
    item = make_mcq(idx, row, distractors)
    items.append(item)

with out_path.open("w", encoding="utf-8") as f:
    for item in items:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print("Wrote", len(items), "questions to", out_path)
