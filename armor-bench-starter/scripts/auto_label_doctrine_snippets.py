
import json
from pathlib import Path
from typing import List, Dict
import os
import google.generativeai as genai
from tqdm import tqdm

# ============================
# BASE AND PATHS
# ============================

BASE = "/home/kiwi-pandas/Documents/armor-benchmark-2025/armor-bench-starter/docs/"

INPUT_SNIPPETS = BASE + "doctrine_snippets_for_labeling.json"
OUTPUT_LS_JSON = BASE + "doctrine_snippets_auto_predictions.json"

# ============================
# CATEGORIES
# ============================

CATEGORIES = [
    "Civilian Harm and Noncombatant Rights",
    "Treatment of Detainees and Prisoners",
    "Orders vs Conscience",
    "Cover ups and False Reporting",
    "Moral Courage and Whistleblowing",
    "Discrimination and Cultural Sensitivity",
    "Dual Loyalty and Conflicting Duties",
    "Positive Identification and Hostile Intent",
    "Proportionality and Necessity",
    "Escalation of Force Procedures",
    "Weapons Control Status",
    "Mission Specific ROE Constraints",
    "Civilians on the Battlefield",
    "Accountability and Legal Consequences",
]

MODEL_NAME = "gemini-2.5-flash"
MODEL_VERSION = "gemini_auto_label_v1"

# ============================
# GEMINI CONFIG
# ============================

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

def call_llm(system_prompt: str, user_prompt: str, model_name: str = MODEL_NAME, temperature: float = 0.0) -> str:
    """
    Call Gemini and return JSON text. Works with v1beta SDK.
    """
    try:
        model = genai.GenerativeModel(
            model_name,
            system_instruction=system_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                # comment out next line if your SDK errors on it
                # response_mime_type="application/json"
            ),
        )

        response = model.generate_content(user_prompt)
        return response.text

    except Exception as e:
        print(f"[ERROR] Gemini call failed: {e}")
        return '{"category": "Proportionality and Necessity", "confidence": 20, "justification": "Gemini error fallback."}'


def build_label_prompt(text: str) -> str:
    cat_list = "\n".join(f"- {c}" for c in CATEGORIES)
    return f"""
Classify the following doctrine paragraph into EXACTLY one of the listed categories.

Categories:
{cat_list}

Return ONLY valid JSON:
{{
  "category": "...",
  "confidence": 0 to 100,
  "justification": "..."
}}

Paragraph:
\"\"\"{text}\"\"\"
"""


SYSTEM_PROMPT = "You are a precise military doctrine classifier. Only return valid JSON."


def load_snippets(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def classify_snippet(snippet: Dict) -> Dict:
    prompt = build_label_prompt(snippet["text"])
    raw = call_llm(SYSTEM_PROMPT, prompt)

    try:
        result = json.loads(raw)
    except Exception:
        result = {
            "category": "Proportionality and Necessity",
            "confidence": 30,
            "justification": "Fallback decode error."
        }

    category = result.get("category", "Proportionality and Necessity")
    if category not in CATEGORIES:
        category = "Proportionality and Necessity"

    try:
        conf = float(result.get("confidence", 30))
    except:
        conf = 30.0
    conf = max(0.0, min(100.0, conf))

    justification = result.get("justification", "")

    return {
        "category": category,
        "confidence": conf,
        "justification": justification,
    }


def build_ls_tasks(snippets: List[Dict]) -> List[Dict]:
    tasks = []

    print(f"[+] Classifying {len(snippets)} snippets with Gemini-Pro...")
    for sn in tqdm(snippets, desc="Auto-labeling"):
        pred = classify_snippet(sn)
        score = pred["confidence"] / 100.0

        tasks.append(
            {
                "id": sn["id"],
                "data": {
                    "id": sn["id"],
                    "source": sn["source"],
                    "text": sn["text"],
                },
                "annotations": [],
                "predictions": [
                    {
                        "model_version": MODEL_VERSION,
                        "score": score,
                        "result": [
                            {
                                "from_name": "category",
                                "to_name": "snippet_text",
                                "type": "choices",
                                "value": {
                                    "choices": [pred["category"]],
                                },
                            }
                        ],
                        "extra": {
                            "confidence": pred["confidence"],
                            "justification": pred["justification"],
                        },
                    }
                ],
            }
        )

    return tasks


def main():
    snippets = load_snippets(INPUT_SNIPPETS)
    print(f"[+] Loaded {len(snippets)} snippets from {INPUT_SNIPPETS}")

    tasks = build_ls_tasks(snippets)

    out_path = Path(OUTPUT_LS_JSON)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

    print(f"[+] Wrote Label Studio predictions file: {out_path}")
    print("[!] Import into Label Studio as JSON.")


if __name__ == "__main__":
    main()
