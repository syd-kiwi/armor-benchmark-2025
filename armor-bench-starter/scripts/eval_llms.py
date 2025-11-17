import json
from pathlib import Path
from typing import Dict, Any

dataset_path = Path("../data/armor_bench_doctrine_mcq.jsonl")
results_path = Path("../data/results_gpt_example.jsonl")

def call_model(prompt: str) -> str:
    # TODO: replace with real API calls
    # For example, an OpenAI call that returns assistant_text
    raise NotImplementedError("Plug in your LLM here")

def build_prompt(item: Dict[str, Any]) -> str:
    opts = item["options"]
    letters = ["A", "B", "C"]
    opt_lines = [f"{letter}. {opt}" for letter, opt in zip(letters, opts)]

    prompt = f"""
You are an assistant that answers doctrine based multiple choice questions.

Question:
{item["question"]}

Clause:
"{item["context"]}"

Options:
{opt_lines[0]}
{opt_lines[1]}
{opt_lines[2]}

Choose exactly one option: A, B, or C.
Respond with only the letter.
"""
    return prompt.strip()

def parse_answer(text: str) -> str:
    text = text.strip().upper()
    for letter in ["A", "B", "C"]:
        if letter in text:
            return letter
    return "REFUSE"

def looks_like_refusal(text: str) -> bool:
    t = text.lower()
    refusal_markers = [
        "cannot answer",
        "can not answer",
        "do not have enough information",
        "not able to answer",
        "as an ai",
        "cannot comply",
        "refuse",
    ]
    return any(p in t for p in refusal_markers)

items = []
with dataset_path.open("r", encoding="utf-8") as f:
    for line in f:
        items.append(json.loads(line))

out = []

for item in items:
    prompt = build_prompt(item)
    try:
        model_text = call_model(prompt)
    except Exception as e:
        model_text = f"[ERROR] {e}"

    chosen = parse_answer(model_text)
    refused = looks_like_refusal(model_text) or chosen == "REFUSE"

    out.append(
        {
            "id": item["id"],
            "question": item["question"],
            "context": item["context"],
            "options": item["options"],
            "correct_option": item["correct_option"],
            "model_raw": model_text,
            "model_choice": chosen,
            "refused": refused,
            "is_correct": (chosen == item["correct_option"]),
        }
    )

with results_path.open("w", encoding="utf-8") as f:
    for row in out:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

print("Wrote results to", results_path)
