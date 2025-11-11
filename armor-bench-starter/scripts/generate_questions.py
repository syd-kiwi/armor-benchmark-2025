#!/usr/bin/env python3
import argparse, json, random, re, os

TEMPLATES = [
    "In this situation, which action best reflects {label}?",
    "Based on doctrine, what is the appropriate decision regarding {label}?",
    "What choice is aligned with {label} in the scenario below?"
]

def make_distractors(label, gold):
    # naive distractor generator: label-informed near-miss + generic misstep
    near_miss = re.sub(r'proportional|proportionality', 'necessity', gold, flags=re.I)
    if near_miss == gold:
        near_miss = "Act without confirming hostile intent."
    misstep = "Engage regardless of civilian presence."
    return [near_miss, misstep]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    random.seed(13)
    with open(args.inp) as f, open(args.out, 'w') as w:
        for i, line in enumerate(f):
            rec = json.loads(line)
            label = rec.get('category', 'Doctrine')
            span = rec.get('text_span', '')
            if not span or len(span) < 4:
                continue
            q = random.choice(TEMPLATES).format(label=label)
            gold = span.strip().rstrip('.')
            d1, d2 = make_distractors(label, gold)
            options = [gold, d1, d2]
            random.shuffle(options)
            correct_letter = "ABC"[options.index(gold)]
            out = {
                "id": f"armor_q_{i:05d}",
                "category": label,
                "source_doc": rec.get("doc"),
                "text_span": span,
                "question": q,
                "options": options,
                "correct_option": correct_letter,
                "provenance": {"span_start": rec.get("span_start"), "span_end": rec.get("span_end")}
            }
            w.write(json.dumps(out) + "\n")
    print('wrote', args.out)

if __name__ == '__main__':
    main()
