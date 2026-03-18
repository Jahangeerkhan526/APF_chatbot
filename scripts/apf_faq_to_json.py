# -*- coding: utf-8 -*-
"""
faq_to_json.py
==============
APF Nancy Chatbot - Convert FAQ txt files to JSON

What it does:
  - Reads all FAQ txt files from data/raw/web-data/faqs/
  - Parses Q&A pairs from each file
  - Saves structured JSON to data/processed/faqs/faqs.json

Usage:
    python scripts/faq_to_json.py

Input:  data/raw/web-data/faqs/*.txt
Output: data/processed/faqs/faqs.json
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
FAQS_DIR   = "data/raw/web-data/faqs"
OUTPUT_DIR = "data/processed/faqs"
OUTPUT_FILE = "faqs.json"

# Map filename → (category, section_label)
FAQ_CATEGORIES = {
    "apf_faqs"                           : ("general",       "APF Organisation"),
    "fertility_treatment_faqs"           : ("preconception", "Fertility Treatment"),
    "general_faqs"                       : ("general",       "General Exercise"),
    "pelvic_floor_faqs"                  : ("general",       "Pelvic Floor"),
    "postnatal_faqs"                     : ("postnatal",     "Postnatal"),
    "pregnancy_faqs"                     : ("pregnancy",     "Pregnancy"),
    "preconception_faqs"                 : ("preconception", "Preconception"),
    "preconception_nhs_faqs"             : ("preconception", "Preconception NHS"),
    "thismummoves_faqs"                  : ("professional",  "This Mum Moves"),
    "thismummoves_pregnancy_leaflet_faqs": ("pregnancy",     "TMM Pregnancy Leaflet"),
    "thismummoves_postnatal_leaflet_faqs": ("postnatal",     "TMM Postnatal Leaflet"),
    "supporter_faqs"                     : ("supporter",     "Supporter Network"),
}

# ── HELPERS ───────────────────────────────────────────────────────────────────

def parse_faq_file(filepath: str) -> list:
    """Parse a FAQ txt file into Q&A pairs."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    pairs = []
    # Split on Q followed by number and period
    blocks = re.split(r'\n(?=Q\d+\.)', content.strip())

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        lines = block.split('\n')
        if not lines:
            continue

        first_line = lines[0].strip()
        q_match = re.match(r'Q(\d+)\.\s*(.*)', first_line)
        if not q_match:
            continue

        q_number = int(q_match.group(1))
        question = q_match.group(2).strip()
        answer   = '\n'.join(lines[1:]).strip()

        if question and answer:
            pairs.append({
                "q_number": q_number,
                "question": question,
                "answer"  : answer,
            })

    return pairs


def main():
    print("\n" + "="*60)
    print("  APF FAQ → JSON Converter")
    print("="*60)
    print(f"  Input : {FAQS_DIR}")
    print(f"  Output: {OUTPUT_DIR}/{OUTPUT_FILE}")

    # Check input directory
    if not Path(FAQS_DIR).exists():
        print(f"\n[ERROR] {FAQS_DIR} not found!")
        return

    # Create output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # Get all txt files
    faq_files = sorted(Path(FAQS_DIR).glob("*.txt"))
    if not faq_files:
        print(f"\n[ERROR] No .txt files found in {FAQS_DIR}")
        return

    print(f"\n  Found {len(faq_files)} FAQ files")
    print(f"\n  {'File':<45} {'Q&As':>5}")
    print(f"  {'-'*52}")

    all_faqs = []
    total_pairs = 0

    for faq_file in faq_files:
        stem     = faq_file.stem
        category_info = FAQ_CATEGORIES.get(stem, ("general", "FAQ"))
        category, section_label = category_info

        pairs = parse_faq_file(str(faq_file))
        if not pairs:
            print(f"  {stem:<45} {'no pairs':>5}")
            continue

        # Build structured records
        for pair in pairs:
            record = {
                "id"           : f"{stem}_q{pair['q_number']}",
                "source_file"  : stem,
                "category"     : category,
                "section_label": section_label,
                "source_type"  : "faq",
                "q_number"     : pair["q_number"],
                "question"     : pair["question"],
                "answer"       : pair["answer"],
                "combined"     : f"Question: {pair['question']}\n\nAnswer: {pair['answer']}",
                "word_count"   : len(pair["answer"].split()),
            }
            all_faqs.append(record)

        total_pairs += len(pairs)
        print(f"  {stem:<45} {len(pairs):>5}")

    # Save to JSON
    output = {
        "metadata": {
            "created_at"   : datetime.now().isoformat(),
            "total_faqs"   : len(all_faqs),
            "total_files"  : len(faq_files),
            "source_dir"   : FAQS_DIR,
        },
        "faqs": all_faqs
    }

    output_path = Path(OUTPUT_DIR) / OUTPUT_FILE
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"  ✅ DONE!")
    print(f"{'='*60}")
    print(f"  Total Q&A pairs : {total_pairs}")
    print(f"  Saved to        : {output_path}")
    print(f"\n  Next step → run: python scripts/embed_faqs.py")


if __name__ == "__main__":
    main()