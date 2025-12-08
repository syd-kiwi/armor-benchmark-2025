from pathlib import Path
import pandas as pd
import re

# Resolve path to project root (scripts folder → parent)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "docs" / "doctrine_categories_raw_v3.csv"
OUTPUT_FILE = PROJECT_ROOT / "docs" / "doctrine_categories_v3.csv"

def clean_text(text):
    if pd.isna(text):
        return text

    s = str(text)

    # Remove three digit numbers and x.x.x
    s = re.sub(r"\b\d{3}\b", "", s)
    s = re.sub(r"\b\d+(?:\.\d+)+\b", "", s)

    # Remove bullet characters
    s = s.replace("•", "")

    # Remove newlines
    s = s.replace("\n", " ").replace("\r", " ")

    # Normalize quotes and unicode spaces
    s = s.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    s = s.replace("\u00a0", " ")

    return s

def main():
    df = pd.read_csv(INPUT_FILE, encoding='utf-8', encoding_errors='replace')

    for col in df.columns:
        df[col] = df[col].apply(clean_text)

    df.to_csv(OUTPUT_FILE, index=False)
    print("[✔] Saved cleaned csv to", OUTPUT_FILE)

if __name__ == "__main__":
    main()
