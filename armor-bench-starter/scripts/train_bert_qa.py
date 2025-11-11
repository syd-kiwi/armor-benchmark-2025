#!/usr/bin/env python3
import argparse
from datasets import load_dataset
from transformers import BertForQuestionAnswering, BertTokenizerFast, TrainingArguments, Trainer

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--train', required=True)
    ap.add_argument('--val', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    model_name = 'bert-base-uncased'
    tok = BertTokenizerFast.from_pretrained(model_name)
    model = BertForQuestionAnswering.from_pretrained(model_name)

    data = load_dataset('json', data_files={'train': args.train, 'validation': args.val})

    def preprocess(examples):
        return tok(examples['question'], examples['context'], truncation=True, padding='max_length', max_length=384)
    tokenized = data.map(preprocess, batched=True, remove_columns=data['train'].column_names)

    args_tr = TrainingArguments(
        output_dir=args.out, evaluation_strategy='epoch', learning_rate=3e-5,
        per_device_train_batch_size=8, num_train_epochs=2, weight_decay=0.01, save_total_limit=1
    )

    trainer = Trainer(model=model, args=args_tr, train_dataset=tokenized['train'], eval_dataset=tokenized['validation'], tokenizer=tok)
    trainer.train()
    model.save_pretrained(args.out); tok.save_pretrained(args.out)
    print('saved model to', args.out)

if __name__ == '__main__':
    main()
