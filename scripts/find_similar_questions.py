import json
import csv
from typing import List, Dict, Any, Tuple
from pathlib import Path

import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors


# ------------------ CONFIG ------------------
dataset_folder = Path.home() / "Documents" / "armor-benchmark-2025" / "dataset"


INPUT_FILES = [
    dataset_folder / "questions_generated_multi_llm.jsonl",
    dataset_folder / "questions_generated_multi_llm_v2.jsonl",
    dataset_folder / "questions_generated_multi_llm_v3.jsonl",
]

OUTPUT_PAIRS_CSV = "question_similarity_pairs.csv"

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
SIM_THRESHOLD = 0.90
TOP_K_NEIGHBORS = 10

# Plot settings
PLOT_MAX_EDGES = 300
PLOT_OUT_PATH = "embedding_projection_edges.png"


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


# ------------------ DEDUPE ------------------

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


# ------------------ PLOT: EMBEDDING PROJECTION WITH EDGES ------------------

def plot_embedding_projection_with_edges(
    embeddings: np.ndarray,
    pairs: List[Tuple[int, int, float]],
    sim_threshold: float,
    max_edges: int = 300,
    out_path: str = "embedding_projection_edges.png",
):
    """
    Projects embeddings to 2D (PCA) and draws edges for high-similarity pairs.
    """
    import matplotlib.pyplot as plt
    from sklearn.decomposition import PCA

    if embeddings is None or len(embeddings) == 0:
        print("[!] No embeddings to plot.")
        return

    strong_pairs = [p for p in pairs if p[2] >= sim_threshold]
    if len(strong_pairs) == 0:
        print(f"[!] No pairs >= threshold {sim_threshold} to plot.")
        return

    xy = PCA(n_components=2, random_state=7).fit_transform(embeddings)

    strong_pairs.sort(key=lambda t: t[2], reverse=True)
    strong_pairs = strong_pairs[:max_edges]

    plt.figure(figsize=(9, 7))
    plt.scatter(xy[:, 0], xy[:, 1], s=10)

    for i, j, sim in strong_pairs:
        plt.plot([xy[i, 0], xy[j, 0]], [xy[i, 1], xy[j, 1]], alpha=0.2)

    plt.title(f"PCA projection with similarity edges (>= {sim_threshold}, top {len(strong_pairs)})")
    plt.xlabel("PC1")
    plt.ylabel("PC2")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.show()

    print(f"[✔] Saved plot to: {out_path}")

import numpy as np
import matplotlib.pyplot as plt
from sklearn.neighbors import NearestNeighbors

def plot_nearest_neighbor_similarity(embeddings, sim_threshold=0.90):
    nbrs = NearestNeighbors(n_neighbors=2, metric="cosine", n_jobs=-1)
    nbrs.fit(embeddings)
    distances, _ = nbrs.kneighbors(embeddings, return_distance=True)

    nn_sim = 1.0 - distances[:, 1]  # nearest other point

    plt.figure()
    plt.plot(np.sort(nn_sim))
    plt.axhline(sim_threshold)
    plt.title("Sorted nearest neighbor cosine similarity")
    plt.xlabel("question rank")
    plt.ylabel("nearest neighbor cosine similarity")
    plt.show()



# ------------------ MAIN ------------------

def main():
    questions = load_questions(INPUT_FILES)
    texts = [build_text_repr(q) for q in questions]
    embeddings = compute_embeddings(texts, EMBEDDING_MODEL_NAME)
    pairs = find_similar_pairs(embeddings, questions, SIM_THRESHOLD, TOP_K_NEIGHBORS)

    write_pairs_csv(OUTPUT_PAIRS_CSV, pairs, questions)

    # NEW: plot what is happening geometrically in embedding space
    plot_embedding_projection_with_edges(
        embeddings=embeddings,
        pairs=pairs,
        sim_threshold=SIM_THRESHOLD,
        max_edges=PLOT_MAX_EDGES,
        out_path=PLOT_OUT_PATH,
    )

    plot_nearest_neighbor_similarity(
        embeddings=embeddings,
        sim_threshold=SIM_THRESHOLD
    )



if __name__ == "__main__":
    main()
