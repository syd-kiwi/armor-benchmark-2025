import pdfplumber
import spacy
from pathlib import Path
import json

nlp = spacy.load("en_core_web_sm")

def pdf_to_sentences(pdf_path, source_name):
    sentences = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            doc = nlp(text)
            for sent in doc.sents:
                s = sent.text.strip()
                if len(s) < 20:
                    continue  # drop very short fragments
                sentences.append({
                    "source": source_name,
                    "page": page_num + 1,
                    "text": s
                })
    return sentences

docs = []
BASE = "armor-bench-starter/documents/"

docs += pdf_to_sentences(BASE + "law_of_war_2023.pdf", "LawOfWar2023")
docs += pdf_to_sentences(BASE + "roe_tbs_b130936.pdf", "ROE_TBS_B130936")
docs += pdf_to_sentences(BASE + "joint_ethics_regulation.pdf", "JointEthicsReg")

Path("data").mkdir(exist_ok=True)

with open("data/doctrine_sentences.jsonl", "w", encoding="utf-8") as f:
    for row in docs:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

print(f"Total sentences: {len(docs)}")
