import os
import csv
import json
from typing import List, Dict, Any, Optional

from openai import OpenAI
import google.generativeai as genai
import anthropic

# Set up clients
# export OPENAI_API_KEY="..."
# export GEMINI_API_KEY="..."
# export ANTHROPIC_API_KEY="..."
openai_client = OpenAI()
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


# --------------- Shared helpers ---------------

def build_prompt(snippet_text: str, category: str, num_questions: int) -> str:
    """
    Build the prompt sent to each LLM.
    """
    prompt = f"""
You are helping design exam questions for junior military officers.

You must base all questions only on the doctrine text I give you.
Do not invent new rules. Do not use outside knowledge.

Respond with ONLY a JSON array. Do not wrap it in markdown

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


def extract_json_array(raw_text: str) -> str:
    """
    Robustly extract the first JSON array from a string.
    - Strips markdown fences like ```json ... ```
    - Then returns the substring from the first '[' to the last ']'
    """
    if raw_text is None:
        raise ValueError("Model output is None")

    raw_text = raw_text.strip()

    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        # Remove leading fence (``` or ```json)
        parts = raw_text.split("```", 1)
        if len(parts) > 1:
            raw_text = parts[1]
        raw_text = raw_text.strip()
        # Remove trailing fence if present
        if "```" in raw_text:
            raw_text = raw_text.rsplit("```", 1)[0]
        raw_text = raw_text.strip()

    # Find JSON array boundaries
    start = raw_text.find("[")
    end = raw_text.rfind("]")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("Could not find JSON array in model output")

    return raw_text[start:end + 1]


# --------------- LLM call wrappers ---------------

def call_gpt(snippet_text: str, category: str, num_questions: int) -> List[Dict[str, Any]]:
    """
    Use GPT as a question generator.
    """
    prompt = build_prompt(snippet_text, category, num_questions)

    completion = openai_client.chat.completions.create(
        model="gpt-4o",  # or "gpt-4.1", "gpt-4o-mini"
        messages=[
            {"role": "system", "content": "You are a helpful assistant that outputs ONLY valid JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
    )

    raw_text = completion.choices[0].message.content or ""

    try:
        json_str = extract_json_array(raw_text)
        mcqs = json.loads(json_str)
        if not isinstance(mcqs, list):
            raise ValueError("GPT output is not a list")
        print(f"[GPT] Parsed {len(mcqs)} questions")
        return mcqs
    except Exception as e:
        print("[GPT] Failed to parse JSON:", e)
        print("[GPT] Raw output (first 500 chars):\n", raw_text[:500])
        return []


def call_gemini(snippet_text: str, category: str, num_questions: int) -> List[Dict[str, Any]]:
    """
    Use Gemini as a question generator.
    """
    prompt = build_prompt(snippet_text, category, num_questions)

    # Use best general Gemini model
    model = genai.GenerativeModel("gemini-3-pro-preview")
    resp = model.generate_content(
        prompt,
        generation_config={"temperature": 0.4}
    )

    raw_text = getattr(resp, "text", "") or ""

    try:
        json_str = extract_json_array(raw_text)
        mcqs = json.loads(json_str)
        if not isinstance(mcqs, list):
            raise ValueError("Gemini output is not a list")
        print(f"[Gemini] Parsed {len(mcqs)} questions")
        return mcqs
    except Exception as e:
        print("[Gemini] Failed to parse JSON:", e)
        print("[Gemini] Raw output (first 500 chars):\n", raw_text[:500])
        return []


def call_claude(snippet_text: str, category: str, num_questions: int) -> List[Dict[str, Any]]:
    """
    Use Claude as the third question generator.
    """
    prompt = build_prompt(snippet_text, category, num_questions)

    resp = anthropic_client.messages.create(
        model="claude-haiku-4-5",  # or another Claude family model you prefer
        max_tokens=2048,
        temperature=0.4,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    raw_text = ""
    for block in resp.content:
        if block.type == "text":
            raw_text += block.text

    try:
        json_str = extract_json_array(raw_text)
        mcqs = json.loads(json_str)
        if not isinstance(mcqs, list):
            raise ValueError("Claude output is not a list")
        print(f"[Claude] Parsed {len(mcqs)} questions")
        return mcqs
    except Exception as e:
        print("[Claude] Failed to parse JSON:", e)
        print("[Claude] Raw output (first 500 chars):\n", raw_text[:500])
        return []


def call_llm_for_snippet(
    model_name: str,
    snippet_text: str,
    category: str,
    num_questions: int
) -> List[Dict[str, Any]]:
    """
    Dispatch to the correct question generator.
    """
    if num_questions <= 0:
        return []

    if model_name == "gpt":
        return call_gpt(snippet_text, category, num_questions)
    elif model_name == "gemini":
        return call_gemini(snippet_text, category, num_questions)
    elif model_name == "claude":
        return call_claude(snippet_text, category, num_questions)
    else:
        raise ValueError(f"Unknown model_name: {model_name}")


# --------------- Helpers ---------------

def sanitize_id_fragment(s: str) -> str:
    return (
        s.replace(" ", "_")
         .replace("/", "_")
         .replace("\\", "_")
         .replace(":", "_")
         .replace(",", "_")
    )


def distribute_questions(num_snippets: int, target_questions: int) -> List[int]:
    """
    Given num_snippets and a target total, return a list with questions per snippet.

    Example: num_snippets=10, target_questions=12 ->
       base=1, remainder=2 -> [2,2,1,1,1,1,1,1,1,1]
    """
    if num_snippets <= 0:
        return []

    base = target_questions // num_snippets
    remainder = target_questions % num_snippets

    per_snip = []
    for i in range(num_snippets):
        extra = 1 if i < remainder else 0
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

    For each category, and for each model in model_names, this will try to
    create `questions_per_model_per_category` questions by distributing them
    across that category's snippets.
    """
    if model_names is None:
        model_names = ["gpt", "gemini", "claude"]

    # 1. Load rows and group by category
    with open(input_csv, "r", encoding="utf-8-sig") as f_in:
        reader = csv.DictReader(f_in)
        required_cols = {"Document", "Category", "Text"}
        if not required_cols.issubset(reader.fieldnames or []):
            raise ValueError(f"CSV must contain columns: {required_cols}, got: {reader.fieldnames}")

        by_category: Dict[str, List[Dict[str, Any]]] = {}
        for row_idx, row in enumerate(reader, start=1):
            cat = (row.get("Category") or "").strip()
            if not cat:
                print(f"Skipping row {row_idx}: missing Category")
                continue
            if cat not in by_category:
                by_category[cat] = []
            row["_row_idx"] = row_idx
            by_category[cat].append(row)

    print("Categories loaded:", list(by_category.keys()))

    # 2. Iterate categories and models
    n_total_questions = 0
    with open(output_path, "w", encoding="utf-8") as f_out:
        for cat_idx, (category, rows) in enumerate(by_category.items(), start=1):
            if max_categories is not None and cat_idx > max_categories:
                break

            num_snips = len(rows)
            print(f"\n[+] Category '{category}': {num_snips} snippets found")
            print("    Using generator models:", model_names)

            for model_name in model_names:
                print(f"    Using generator model: {model_name}")
                question_counts = distribute_questions(num_snips, questions_per_model_per_category)
                print(
                    f"    Target questions for this model: {questions_per_model_per_category}, "
                    f"per-snippet: {question_counts}"
                )

                for snip_i, (row, num_q) in enumerate(zip(rows, question_counts), start=1):
                    doc_source = (row.get("Document") or "").strip()
                    text = (row.get("Text") or "").strip()
                    row_idx = row.get("_row_idx")

                    if not doc_source or not text:
                        print(f"      Skipping row {row_idx} with missing Document/Text")
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
                    print(
                        f"      [DEBUG] {model_name} row {row_idx}: "
                        f"requested {num_q}, got {len(mcqs)}"
                    )

                    # If the model returns more than we asked for, trim it
                    if len(mcqs) > num_q:
                        mcqs = mcqs[:num_q]

                    for j, mcq in enumerate(mcqs, start=1):
                        qid = f"{span_base}_Q{j:02d}"

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

    print(f"\n[✔] Done. Total questions generated across all categories: {n_total_questions}")
    print(f"[✔] Output written to: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate MCQs from doctrine CSV using GPT, Gemini, and Claude as questioners."
    )
    parser.add_argument(
        "--input_csv",
        type=str,
        default="doctrine_categories_v2.csv",
        help="Path to CSV file with columns Document,Category,Text.",
    )
    parser.add_argument(
        "--output_questions",
        type=str,
        default="questions_generated_multi_llm_v2.jsonl",
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

    args = parser.parse_args()

    generate_mcqs_from_csv_multi_llm(
        input_csv=args.input_csv,
        output_path=args.output_questions,
        questions_per_model_per_category=args.questions_per_model,
        model_names=["gpt", "gemini", "claude"],
        max_categories=args.max_categories,
    )
