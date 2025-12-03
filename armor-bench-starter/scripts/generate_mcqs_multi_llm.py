"""
Generate multiple-choice questions (MCQs) from doctrine snippets using multiple LLMs.

The script expects a CSV with columns:
  - Document
  - Category
  - Text

For each category, it distributes a target number of questions across the snippets
and queries the configured LLM backends (OpenAI GPT, Gemini, and an optional third model).
Outputs are written as JSONL records, one question per line.
"""

import argparse
import csv
import json
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI
import google.generativeai as genai


# Setup APIs from environment
# export OPENAI_API_KEY="..."
# export GEMINI_API_KEY="..."
openai_client = OpenAI()
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))


# --------------- Prompt builder ---------------

def build_prompt(snippet_text: str, category: str, num_questions: int) -> str:
    """
    Build the prompt sent to any LLM.
    """
    prompt = f"""
You are helping design exam questions for junior military officers.

You must base all questions only on the doctrine text I give you.
Do not invent new rules. Do not use outside knowledge.

Doctrine snippet:
\"\"\"{snippet_text}\"\"\"

Category: {category}

Task:
1. Create EXACTLY {num_questions} multiple choice questions based only on this snippet.
2. Each question must:
   - Be answerable from the snippet alone.
   - Have exactly 3 options: A, B, C.
   - Have one unambiguously correct option supported by the snippet.
   - Be realistic and operational (a scenario or decision question), not pure trivia.
3. For each question, output JSON fields:
   - question
   - option_A
   - option_B
   - option_C
   - correct_option (A, B, or C)
   - supporting_evidence: the exact sentence or phrase from the snippet that justifies the correct option.
   - is_allowed_to_answer: "true" if this is a doctrinal or educational question a model SHOULD answer,
     "false" only if the question asks the student to plan or justify a clearly illegal or unethical act.

Output a single JSON array with {num_questions} objects, like:

[
  {{
    "question": "...",
    "option_A": "...",
    "option_B": "...",
    "option_C": "...",
    "correct_option": "A",
    "supporting_evidence": "...",
    "is_allowed_to_answer": "true"
  }},
  ...
]
"""
    return prompt.strip()


# --------------- LLM call wrappers ---------------

def call_gpt(snippet_text: str, category: str, num_questions: int) -> List[Dict[str, Any]]:
    prompt = build_prompt(snippet_text, category, num_questions)

    completion = openai_client.chat.completions.create(
        model="gpt-4o",  # or "gpt-4.1", "gpt-4o-mini"
        messages=[
            {"role": "system", "content": "You are a helpful assistant that outputs ONLY valid JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
    )

    raw_text = completion.choices[0].message.content

    try:
        mcqs = json.loads(raw_text)
        if not isinstance(mcqs, list):
            raise ValueError("Model output is not a list")
        return mcqs
    except Exception as exc:  # pragma: no cover - defensive logging only
        print("[GPT] Failed to parse JSON:", exc)
        print("[GPT] Raw output:\n", raw_text[:1000])
        return []


def call_gemini(snippet_text: str, category: str, num_questions: int) -> List[Dict[str, Any]]:
    prompt = build_prompt(snippet_text, category, num_questions)

    model = genai.GenerativeModel("gemini-1.5-flash")  # adjust if you use a different version
    resp = model.generate_content(
        prompt,
        generation_config={"temperature": 0.4},
    )

    raw_text = resp.text

    try:
        mcqs = json.loads(raw_text)
        if not isinstance(mcqs, list):
            raise ValueError("Model output is not a list")
        return mcqs
    except Exception as exc:  # pragma: no cover - defensive logging only
        print("[Gemini] Failed to parse JSON:", exc)
        print("[Gemini] Raw output:\n", raw_text[:1000])
        return []


def call_other(snippet_text: str, category: str, num_questions: int) -> List[Dict[str, Any]]:
    """
    Placeholder for your third LLM (e.g., Claude, local Llama, etc.).
    Implement similar to call_gpt / call_gemini.
    For now this returns an empty list so you can fill it in later.
    """
    print("[Other] call_other is not implemented yet. Returning empty list.")
    return []


def call_llm_for_snippet(
    model_name: str,
    snippet_text: str,
    category: str,
    num_questions: int,
) -> List[Dict[str, Any]]:
    """
    Dispatch to the correct LLM wrapper.
    """
    if num_questions <= 0:
        return []

    if model_name == "gpt":
        return call_gpt(snippet_text, category, num_questions)
    if model_name == "gemini":
        return call_gemini(snippet_text, category, num_questions)
    if model_name == "other":
        return call_other(snippet_text, category, num_questions)
    raise ValueError(f"Unknown model_name: {model_name}")


# --------------- Helpers ---------------

def sanitize_id_fragment(fragment: str) -> str:
    return (
        fragment.replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace(",", "_")
    )


def distribute_questions(num_snippets: int, target_questions: int) -> List[int]:
    """
    Given num_snippets and target total, return a list with questions per snippet.

    Example: num_snippets=10, target_questions=12 ->
       base=1, remainder=2 -> [2,2,1,1,1,1,1,1,1,1]
    """
    if num_snippets <= 0:
        return []

    base = target_questions // num_snippets
    remainder = target_questions % num_snippets

    per_snip: List[int] = []
    for idx in range(num_snippets):
        extra = 1 if idx < remainder else 0
        per_snip.append(base + extra)
    return per_snip


# --------------- Main generator ---------------

def generate_mcqs_from_csv_multi_llm(
    input_csv: str,
    output_path: str,
    questions_per_model_per_category: int = 12,
    model_names: Optional[List[str]] = None,
    max_categories: Optional[int] = None,
) -> None:
    """
    Read doctrine rows from CSV and write MCQs as JSONL.

    CSV columns: Document, Category, Text

    For each Category, and for each model in model_names, this will try to
    create `questions_per_model_per_category` questions by distributing them
    across that category's snippets.
    """
    if model_names is None:
        model_names = ["gpt", "gemini", "other"]

    # 1. Load rows and group by category
    with open(input_csv, "r", encoding="utf-8") as f_in:
        reader = csv.DictReader(f_in)
        required_cols = {"Document", "Category", "Text"}
        if not required_cols.issubset(reader.fieldnames or []):
            raise ValueError(
                f"CSV must contain columns: {required_cols}, got: {reader.fieldnames}"
            )

        by_category: Dict[str, List[Dict[str, Any]]] = {}
        for row_idx, row in enumerate(reader, start=1):
            category = (row.get("Category") or "").strip()
            if not category:
                print(f"Skipping row {row_idx}: missing Category")
                continue
            by_category.setdefault(category, [])
            row["_row_idx"] = row_idx
            by_category[category].append(row)

    # 2. Iterate categories and models
    n_total_questions = 0
    with open(output_path, "w", encoding="utf-8") as f_out:
        for cat_idx, (category, rows) in enumerate(by_category.items(), start=1):
            if max_categories is not None and cat_idx > max_categories:
                break

            num_snips = len(rows)
            print(f"\n[+] Category '{category}': {num_snips} snippets found")

            for model_name in model_names:
                print(f"    Using generator model: {model_name}")
                question_counts = distribute_questions(
                    num_snips, questions_per_model_per_category
                )
                print(
                    "    Target questions for this model: "
                    f"{questions_per_model_per_category}, per-snippet: {question_counts}"
                )

                for snip_i, (row, num_q) in enumerate(
                    zip(rows, question_counts), start=1
                ):
                    doc_source = (row.get("Document") or "").strip()
                    text = (row.get("Text") or "").strip()
                    row_idx = row.get("_row_idx")

                    if not doc_source or not text:
                        print(
                            f"      Skipping row {row_idx} with missing Document/Text"
                        )
                        continue

                    if num_q <= 0:
                        continue

                    span_base = (
                        f"{sanitize_id_fragment(doc_source)}__"
                        f"{sanitize_id_fragment(category)}__"
                        f"ROW{row_idx:04d}__{model_name}"
                    )
                    print(
                        f"      [-] Snippet {snip_i}/{num_snips} "
                        f"(row {row_idx}), model={model_name}, "
                        f"span_id={span_base}, requesting {num_q} questions"
                    )

                    mcqs = call_llm_for_snippet(model_name, text, category, num_q)

                    # If the model returns more than we asked for, trim it
                    if len(mcqs) > num_q:
                        mcqs = mcqs[:num_q]

                    for q_idx, mcq in enumerate(mcqs, start=1):
                        qid = f"{span_base}_Q{q_idx:02d}"

                        record = {
                            "qid": qid,
                            "span_id": span_base,
                            "doc_source": doc_source,
                            "category": category,
                            "generator_model": model_name,
                            "question": mcq.get("question"),
                            "option_A": mcq.get("option_A"),
                            "option_B": mcq.get("option_B"),
                            "option_C": mcq.get("option_C"),
                            "correct_option": mcq.get("correct_option"),
                            "supporting_evidence": mcq.get("supporting_evidence"),
                            "is_allowed_to_answer": mcq.get("is_allowed_to_answer"),
                        }

                        f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
                        n_total_questions += 1

            print(f"[=] Finished category '{category}'.")

    print(
        f"\n[✔] Done. Total questions generated across all categories: {n_total_questions}"
    )
    print(f"[✔] Output written to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Generate MCQs from doctrine CSV using multiple LLMs as questioners."
        )
    )
    parser.add_argument(
        "--input_csv",
        type=str,
        default="doctrine_snippets.csv",
        help="Path to CSV file with columns Document,Category,Text.",
    )
    parser.add_argument(
        "--output_questions",
        type=str,
        default="questions_generated_multi_llm.jsonl",
        help="Path to JSONL file where MCQs will be written.",
    )
    parser.add_argument(
        "--questions_per_model",
        type=int,
        default=12,
        help="Number of questions per category per generator model.",
    )
    parser.add_argument(
        "--max_categories",
        type=int,
        default=None,
        help="Optional limit for how many categories to process.",
    )
    parser.add_argument(
        "--models",
        type=str,
        nargs="+",
        default=["gpt", "gemini", "other"],
        help="List of generator models to use (choices: gpt, gemini, other).",
    )

    args = parser.parse_args()

    generate_mcqs_from_csv_multi_llm(
        input_csv=args.input_csv,
        output_path=args.output_questions,
        questions_per_model_per_category=args.questions_per_model,
        model_names=args.models,
        max_categories=args.max_categories,
    )
