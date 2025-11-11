#!/usr/bin/env python3
import argparse, json, math
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--dedupe', action='store_true')
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.inp)]
    if args.dedupe:
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        emb = model.encode([r['question'] for r in rows], normalize_embeddings=True)
        sims = cosine_similarity(emb)
        keep = [True]*len(rows)
        for i in range(len(rows)):
            if not keep[i]: continue
            for j in range(i+1, len(rows)):
                if sims[i,j] >= 0.90:
                    keep[j] = False
        rows = [r for k,r in zip(keep, rows) if k]

    with open(args.out, 'w') as w:
        for r in rows:
            w.write(json.dumps(r) + "\n")
    print('kept', len(rows), 'of', len(rows))

if __name__ == '__main__':
    main()
