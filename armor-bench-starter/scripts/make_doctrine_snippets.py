import pdfplumber
from pathlib import Path
import json
import re
from typing import List, Dict

BASE = "/home/kiwi-pandas/Documents/armor-benchmark-2025/armor-bench-starter/docs/"

# adjust these to your real paths
PDFS = [
    #{"path": BASE + "/law_of_war_2023.pdf", "source": "LOW"},
    {"path": BASE + "/roe_tbs_b130936.pdf", "source": "ROE"},
    {"path": BASE + "/NIST.AI.100-1.pdf", "source": "NIST"},
    {"path": BASE + "/joint_ethics_regulation.pdf", "source": "JER"},
]

OUT_JSONL = "doctrine_snippets_for_labeling.jsonl"        # simple jsonl
OUT_JSON = "doctrine_snippets_for_labeling.json"          # simple json array
OUT_LS_JSON = "doctrine_snippets_labelstudio.json"        # Label Studio format

# Snippet length controls
MIN_CHARS = 250
MAX_CHARS = 1200


# ==========================
# PDF text extraction
# ==========================

def extract_text_from_pdf(pdf_path: str) -> str:
    text_chunks: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_chunks.append(page_text)
    return "\n".join(text_chunks)


def normalize_text(raw_text: str) -> str:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    # join hyphenated words across line breaks: "law-\nfare" -> "lawfare"
    text = re.sub(r"-\n(\w)", r"\1", text)
    # mark paragraph breaks
    text = re.sub(r"\n{2,}", "<<<PARA>>>", text)
    # single newlines -> spaces
    text = re.sub(r"\n+", " ", text)
    text = text.replace("<<<PARA>>>", "\n\n")
    # collapse extra spaces
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text


# ==========================
# Paragraph splitting
# ==========================

def split_into_paragraphs(raw_text: str) -> List[str]:
    cleaned = normalize_text(raw_text)
    raw_paras = cleaned.split("\n\n")

    paras: List[str] = []

    for p in raw_paras:
        p = p.strip()
        if not p:
            continue

        # skip pure page numbers
        if re.fullmatch(r"\d{1,4}", p):
            continue

        # skip short all caps headers
        if len(p) < 80 and p.upper() == p and re.search(r"[A-Z]", p):
            continue

        # skip weird noise from previous errors
        if "The filetype of file \"doctrine_snippets_for_labeling.jsonl\" is not supported" in p:
            continue

        if len(p) < MIN_CHARS:
            continue

        if len(p) > MAX_CHARS:
            sentences = re.split(r"(?<=[.!?])\s+", p)
            chunk = ""
            for s in sentences:
                s = s.strip()
                if not s:
                    continue
                if len(chunk) + len(s) + 1 <= MAX_CHARS:
                    chunk = (chunk + " " + s).strip()
                else:
                    if len(chunk) >= MIN_CHARS:
                        paras.append(chunk)
                    chunk = s
            if len(chunk) >= MIN_CHARS:
                paras.append(chunk)
        else:
            paras.append(p)

    return paras


# ==========================
# Build snippet dicts
# ==========================

def build_snippets() -> List[Dict]:
    """
    Return list of:
    {
      "id": "LOW_0001",
      "source": "LOW",
      "text": "..."
    }
    """
    all_snippets: List[Dict] = []

    for pdf_info in PDFS:
        pdf_path = pdf_info["path"]
        source = pdf_info["source"]

        print(f"[+] Processing {pdf_path} (source={source})")
        full_text = extract_text_from_pdf(pdf_path)
        paras = split_into_paragraphs(full_text)
        print(f"    -> found {len(paras)} candidate snippets")

        for idx, para in enumerate(paras, start=1):
            snippet_id = f"{source}_{idx:04d}"
            all_snippets.append(
                {
                    "id": snippet_id,
                    "source": source,
                    "text": para,
                }
            )

    print(f"[+] Total snippets: {len(all_snippets)}")
    return all_snippets


# ==========================
# Save in three formats
# ==========================

def save_snippets(snippets: List[Dict]) -> None:
    out_jsonl = Path(OUT_JSONL)
    out_json = Path(OUT_JSON)
    out_ls_json = Path(OUT_LS_JSON)

    # 1) JSONL (simple)
    with out_jsonl.open("w", encoding="utf-8") as f_out:
        for obj in snippets:
            f_out.write(json.dumps(obj, ensure_ascii=False) + "\n")
    print(f"[+] Wrote JSONL: {out_jsonl} ({len(snippets)} lines)")

    # 2) JSON (simple array)
    with out_json.open("w", encoding="utf-8") as f_out:
        json.dump(snippets, f_out, indent=2, ensure_ascii=False)
    print(f"[+] Wrote JSON array: {out_json}")

    # 3) Label Studio JSON:
    # each item must have:
    #   - data: task data (we put text, id, source)
    #   - annotations: [] (empty on import)
    #   - predictions: [] (empty on import)
    ls_items = []
    for sn in snippets:
        ls_items.append(
            {
                "id": sn["id"],  # optional, but nice to keep
                "data": {
                    "id": sn["id"],
                    "source": sn["source"],
                    "text": sn["text"],
                },
                "annotations": [],
                "predictions": [],
            }
        )

    with out_ls_json.open("w", encoding="utf-8") as f_out:
        json.dump(ls_items, f_out, indent=2, ensure_ascii=False)
    print(f"[+] Wrote Label Studio JSON: {out_ls_json}")


def main():
    snippets = build_snippets()
    save_snippets(snippets)


if __name__ == "__main__":
    main()
