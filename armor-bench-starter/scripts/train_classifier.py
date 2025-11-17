import json
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score
from config_labels import LABELS, label2id, id2label

MODEL_NAME = "bert-base-uncased"

data_files = {
    "train": "../data/train_labeled.jsonl",
    "validation": "../data/val_labeled.jsonl",
}

raw_datasets = load_dataset("json", data_files=data_files)

def convert_label_names(batch):
    vecs = []
    for label_names in batch["labels"]:
        v = [0] * len(LABELS)
        for name in label_names:
            if name not in label2id:
                continue
            v[label2id[name]] = 1
        vecs.append(v)
    batch["labels"] = vecs
    return batch

raw_datasets = raw_datasets.map(convert_label_names, batched=True)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def tokenize_batch(batch):
    enc = tokenizer(
        batch["text"],
        truncation=True,
        padding="max_length",
        max_length=256,
    )
    enc["labels"] = batch["labels"]
    return enc

tokenized = raw_datasets.map(tokenize_batch, batched=True)
tokenized = tokenized.remove_columns(
    [c for c in tokenized["train"].column_names if c not in ["input_ids", "token_type_ids", "attention_mask", "labels"]]
)
tokenized.set_format("torch")

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(LABELS),
    problem_type="multi_label_classification",
    id2label=id2label,
    label2id=label2id,
)

def compute_metrics(pred):
    logits, labels = pred
    probs = 1 / (1 + np.exp(-logits))
    preds = (probs > 0.5).astype(int)

    return {
        "f1_micro": f1_score(labels, preds, average="micro", zero_division=0),
        "f1_macro": f1_score(labels, preds, average="macro", zero_division=0),
        "precision_micro": precision_score(labels, preds, average="micro", zero_division=0),
        "recall_micro": recall_score(labels, preds, average="micro", zero_division=0),
    }

training_args = TrainingArguments(
    output_dir="../models/doctrine_bert",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=16,
    num_train_epochs=3,
    weight_decay=0.01,
    load_best_model_at_end=True,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized["train"],
    eval_dataset=tokenized["validation"],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
)

trainer.train()
trainer.save_model("../models/doctrine_bert_best")
tokenizer.save_pretrained("../models/doctrine_bert_best")
