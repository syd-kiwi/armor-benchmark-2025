#!/usr/bin/env python3
# Placeholder: attach category labels if needed. For now, passthrough.
import argparse, json
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    with open(args.inp) as f, open(args.out, 'w') as w:
        for line in f:
            w.write(line)
    print('labels passthrough ->', args.out)
if __name__ == '__main__':
    main()
