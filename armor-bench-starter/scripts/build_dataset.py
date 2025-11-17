import json
from pathlib import Path

in_path = Path("../data/questions_raw.jsonl")
out_path = Path("../data/armor_bench_doctrine_mcq.jsonl")

final_items = []

with in_path.open("r", encoding="utf-8") as f:
    for line in f:
        q = json.loads(line)
        item = {
            "id": q["id"],
            "question": q["question"],
            "context": q["context"],
            "options": q["options"],
            "correct_option": q["correct_option"],
            "correct_answer": q["correct_answer"],
            "label_category": q["correct_answer"],
            "provenance": {
                "source": q["meta"].get("source"),
                "page": q["meta"].get("page"),
            },
        }
        final_items.append(item)

with out_path.open("w", encoding="utf-8") as f:
    for item in final_items:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print("Final dataset size:", len(final_items))
print("Saved to", out_path)
