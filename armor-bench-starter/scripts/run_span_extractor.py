#!/usr/bin/env python3
import argparse, os, json, glob
from transformers import BertForQuestionAnswering, BertTokenizerFast
import torch

def find_answer_span(model, tok, context, question, max_len=384):
    enc = tok(question, context, return_tensors='pt', truncation=True, padding='max_length', max_length=max_len)
    with torch.no_grad():
        out = model(**enc)
        start = int(torch.argmax(out.start_logits))
        end = int(torch.argmax(out.end_logits))
    input_ids = enc['input_ids'][0]
    offset_mapping = tok(question, context, return_offsets_mapping=True, truncation=True, padding='max_length', max_length=max_len)['offset_mapping']
    s_off, e_off = offset_mapping[start][1], offset_mapping[end][1]
    # crude fallback if offsets are zeroed
    if s_off == 0 and e_off == 0:
        s_off, e_off = 0, min(len(context), 80)
    span_text = context[s_off:e_off].strip()
    return s_off, e_off, span_text

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--docs', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    tok = BertTokenizerFast.from_pretrained(args.model)
    model = BertForQuestionAnswering.from_pretrained(args.model)
    questions = [
        ('What does proportionality require?', 'Proportionality and Necessity'),
        ('What is required before engagement?', 'Positive Identification and Hostile Intent'),
        ('How must detainees be treated?', 'Treatment of Detainees and Prisoners')
    ]
    out_path = args.out
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as fout:
        for fp in glob.glob(os.path.join(args.docs, '*.txt')):
            ctx = open(fp, 'r', encoding='utf-8', errors='ignore').read()
            for q, cat in questions:
                s, e, span = find_answer_span(model, tok, ctx, q)
                rec = {'doc': os.path.basename(fp), 'category': cat, 'question': q,
                       'span_start': s, 'span_end': e, 'text_span': span}
                fout.write(json.dumps(rec) + '\n')
                print('span from', fp, '->', span[:60])
    print('wrote', out_path)

if __name__ == '__main__':
    main()
