import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import json

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained("outputs/doctrine_bert_best")
model = AutoModelForSequenceClassification.from_pretrained("outputs/doctrine_bert_best").to(DEVICE)
model.eval()

def classify_sentence(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=256).to(DEVICE)
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.sigmoid(logits).cpu().numpy()[0]
    indices = [i for i, p in enumerate(probs) if p > 0.5]
    labels = [id2label[i] for i in indices]
    return list(zip(labels, probs[indices]))

results = []
with open("data/doctrine_sentences.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        labels_scores = classify_sentence(row["text"])
        row["predicted_labels"] = [ls[0] for ls in labels_scores]
        row["predicted_scores"] = [float(ls[1]) for ls in labels_scores]
        results.append(row)

with open("data/doctrine_sentences_tagged.jsonl", "w", encoding="utf-8") as f:
    for row in results:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
