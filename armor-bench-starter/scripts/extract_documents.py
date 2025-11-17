#!/usr/bin/env python3
import json
from pathlib import Path

import pdfplumber
import spacy
from tqdm import tqdm

# Absolute path to your PDFs
BASE = "/home/kiwi-pandas/Documents/armor-benchmark-2025/armor-bench-starter/docs/"

# Load spaCy model
nlp = spacy.load("en_core_web_sm")


def pdf_to_sentences(pdf_path: str, source_name: str):
    """Extract sentences from a single PDF file."""
    sentences = []

    with pdfplumber.open(pdf_path) as pdf:
        # Progress bar over pages in this PDF
        for page_num, page in enumerate(
            tqdm(pdf.pages, desc=source_name, unit="page"), start=1
        ):
            text = page.extract_text()
            if not text:
                continue

            doc = nlp(text)
            for sent in doc.sents:
                s = sent.text.strip()
                # Skip very short fragments
                if len(s) < 20:
                    continue

                sentences.append(
                    {
                        "source": source_name,
                        "page": page_num,
                        "text": s,
                    }
                )

    return sentences


def main():
    pdf_files = [
        ("law_of_war_2023.pdf", "LawOfWar2023"),
        ("roe_tbs_b130936.pdf", "ROE_TBS_B130936"),
        ("joint_ethics_regulation.pdf", "JointEthicsReg"),
    ]

    all_sentences = []

    # Progress bar over the three documents
    for filename, source in tqdm(pdf_files, desc="Documents", unit="pdf"):
        pdf_path = BASE + filename
        all_sentences.extend(pdf_to_sentences(pdf_path, source))

    # Create output folder (relative to where you run the script)
    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)

    out_path = out_dir / "doctrine_sentences.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for row in all_sentences:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Total sentences: {len(all_sentences)}")
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
