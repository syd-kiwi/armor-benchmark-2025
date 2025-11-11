#!/usr/bin/env python3
import argparse, csv, os

TEX_TMPL = r"""\documentclass[11pt]{article}
\usepackage[a4paper,margin=1in]{geometry}
\usepackage{booktabs}
\usepackage[table]{xcolor}
\usepackage{helvet}
\renewcommand{\familydefault}{\sfdefault}
\title{ARMOR-BENCH Results}
\date{}
\begin{document}
\maketitle
\begin{table}[h!]
\centering
\caption{Accuracy and Refusal Rate}
\begin{tabular}{lcc}
\toprule
Model & Accuracy & Refusal Rate \\ \midrule
{rows}
\bottomrule
\end{tabular}
\end{table}
\end{document}
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    rows = []
    with open(args.in, newline='') as f:
        for i, r in enumerate(csv.DictReader(f)):
            rows.append(f"{r['model']} & {r['accuracy']} & {r['refusal_rate']} \\ ")
    tex = TEX_TMPL.format(rows='\n'.join(rows))
    open(args.out, 'w').write(tex)
    print('wrote', args.out)

if __name__ == '__main__':
    main()
