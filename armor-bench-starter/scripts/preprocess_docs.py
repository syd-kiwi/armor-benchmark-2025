#!/usr/bin/env python3
import argparse, os, re, pathlib
from pdfminer.high_level import extract_text

def clean_text(txt):
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    os.makedirs(args.output, exist_ok=True)
    for root, _, files in os.walk(args.input):
        for fn in files:
            p = os.path.join(root, fn)
            if fn.lower().endswith('.pdf'):
                try:
                    text = extract_text(p)
                except Exception:
                    continue
            else:
                text = open(p, 'r', errors='ignore').read()
            text = clean_text(text)
            out = os.path.join(args.output, pathlib.Path(fn).with_suffix('.txt').name)
            open(out, 'w', encoding='utf-8').write(text)
            print('wrote', out)
if __name__ == '__main__':
    main()
