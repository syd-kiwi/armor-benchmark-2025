import json
import csv
from typing import List, Dict, Any, Tuple
from pathlib import Path

import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors


# ------------------ CONFIG ------------------

INPUT_FILES = [
    "questions_generated_multi_llm.jsonl",
    "questions_generated_multi_llm_v2.jsonl",
    "questions_generated_multi_llm_v3.jsonl",
]

OUTPUT_PAIRS_CSV = "question_similarity_pairs.csv"

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
SIM_THRESHOLD = 0.90
TOP_K_NEIGHBORS = 10


# ------------------ LOADING ------------------

def load_questions(files: List[str]) -> List[Dict[str, Any]]:
    merged = []
    print(f"\n[+] Loading questions from {len(files)} files...\n")

    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            for line in tqdm(f, desc=f"Loading {file}", unit=" lines"):
                if not line.strip():
                    continue
                q = json.loads(line)
                q["_source_file"] = file
                merged.append(q)

    print(f"\n[✔] Loaded {len(merged)} total questions.\n")
    return merged


def build_text_repr(q: Dict[str, Any]) -> str:
    stem = q.get("question", "") or ""
    category = q.get("category", "") or ""
    gen_model = q.get("generator_model", "") or ""
    src = q.get("_source_file", "")
    return f"[{category}] ({gen_model}) <{src}> {stem}"


# ------------------ EMBEDDINGS ------------------

def compute_embeddings(texts: List[str], model_name: str) -> np.ndarray:
    print(f"\n[+] Generating embeddings using model: {model_name}\n")
    model = SentenceTransformer(model_name)

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    print(f"\n[✔] Finished generating embeddings. Shape = {embeddings.shape}\n")
    return embeddings


# ------------------ SIMILARITY SEARCH ------------------

def find_similar_pairs(
    embeddings: np.ndarray,
    questions: List[Dict[str, Any]],
    sim_threshold: float,
    top_k: int
) -> List[Tuple[int, int, float]]:

    print("\n[+] Building nearest neighbor index...\n")

    nbrs = NearestNeighbors(
        n_neighbors=min(top_k, len(questions)),
        metric="cosine",
        n_jobs=-1,
    )
    nbrs.fit(embeddings)

    print("\n[+] Searching for similar question pairs...\n")

    pairs = []
    for i in tqdm(range(len(questions)), desc="Computing similarities"):
        distances, indices = nbrs.kneighbors(embeddings[i:i+1], return_distance=True)

        for dist, j in zip(distances[0], indices[0]):
            if i == j:
                continue
            sim = 1.0 - float(dist)
            if sim >= sim_threshold:
                a, b = sorted([i, j])
                pairs.append((a, b, sim))

    # Deduplicate
    unique_pairs = {}
    for a, b, sim in pairs:
        key = (a, b)
        if key not in unique_pairs or sim > unique_pairs[key]:
            unique_pairs[key] = sim

    result = [(a, b, s) for (a, b), s in unique_pairs.items()]
    result.sort(key=lambda x: x[2], reverse=True)

    print(f"\n[✔] Found {len(result)} similar pairs above threshold {sim_threshold}\n")

    return result


# ------------------ CSV OUTPUT ------------------

def write_pairs_csv(path: str, pairs: List[Tuple[int, int, float]], questions: List[Dict[str, Any]]):
    print(f"[+] Writing similarity pairs to: {path}\n")
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "qid_1", "qid_2",
            "similarity",
            "category_1", "category_2",
            "model_1", "model_2",
            "file_1", "file_2",
            "question_1", "question_2",
        ])

        for i, j, sim in tqdm(pairs, desc="Saving pairs"):
            q1 = questions[i]
            q2 = questions[j]
            writer.writerow([
                q1.get("qid"),
                q2.get("qid"),
                f"{sim:.4f}",
                q1.get("category"),
                q2.get("category"),
                q1.get("generator_model"),
                q2.get("generator_model"),
                q1.get("_source_file"),
                q2.get("_source_file"),
                q1.get("question"),
                q2.get("question"),
            ])

    print(f"\n[✔] Done. Written to {path}\n")

def dedupe_questions_from_pairs(
    pairs: List[Tuple[int, int, float]],
    questions: List[Dict[str, Any]],
    output_path: str = "questions_deduped.jsonl",
    sim_threshold: float = 0.90
):
    """
    Remove near-duplicate questions based on similarity pairs.
    For each pair (i, j) with similarity >= sim_threshold:
        - Keep the earlier index
        - Remove the later index
    """
    print(f"\n[+] Deduplicating questions with similarity >= {sim_threshold} ...")

    duplicates = set()

    for i, j, sim in pairs:
        if sim >= sim_threshold:
            # remove the later question consistently
            duplicates.add(max(i, j))

    print(f"[✔] Marked {len(duplicates)} questions as duplicates.")

    kept = 0
    with open(output_path, "w", encoding="utf-8") as f:
        for idx, q in enumerate(questions):
            if idx in duplicates:
                continue
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
            kept += 1

    print(f"[✔] Deduped dataset saved to: {output_path}")
    print(f"[✔] Total kept: {kept}, removed: {len(duplicates)}\n")


# ------------------ MAIN ------------------

def main():
    questions = load_questions(INPUT_FILES)
    texts = [build_text_repr(q) for q in questions]
    embeddings = compute_embeddings(texts, EMBEDDING_MODEL_NAME)
    pairs = find_similar_pairs(embeddings, questions, SIM_THRESHOLD, TOP_K_NEIGHBORS)

    write_pairs_csv(OUTPUT_PAIRS_CSV, pairs, questions)

    dedupe_questions_from_pairs(
        pairs,
        questions,
        output_path="questions_deduped.jsonl",
        sim_threshold=SIM_THRESHOLD,
    )



if __name__ == "__main__":
    main()

'''
[+] Deduplicating questions with similarity >= 0.9 ...
[✔] Marked 21 questions as duplicates.
[✔] Deduped dataset saved to: questions_deduped.jsonl
[✔] Total kept: 519, removed: 21
'''