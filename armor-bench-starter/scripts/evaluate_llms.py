#!/usr/bin/env python3
# Placeholder evaluator: simulates model answers and computes accuracy/refusal rate
import argparse, json, random, csv

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--questions', required=True)
    ap.add_argument('--models', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    qs = [json.loads(l) for l in open(args.questions)]
    results = []
    for model_name in ["gpt4-sim","claude-sim","llama-sim"]:
        correct = 0
        refusals = 0
        for q in qs:
            # toy simulation: 10% refusal on detainee items
            refuse = ("Detainee" in q['category']) and (random.random() < 0.10)
            if refuse:
                refusals += 1
                continue
            # toy correctness
            guess = random.choice(["A","B","C"])
            if guess == q['correct_option']:
                correct += 1
        acc = correct / max(1, (len(qs)-refusals))
        refusal_rate = refusals / len(qs)
        results.append({"model": model_name, "accuracy": round(acc,3), "refusal_rate": round(refusal_rate,3)})

    with open(args.out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=["model","accuracy","refusal_rate"])
        w.writeheader(); w.writerows(results)
    print('wrote', args.out)

if __name__ == '__main__':
    main()
