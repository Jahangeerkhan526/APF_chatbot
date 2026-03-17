# -*- coding: utf-8 -*-
"""
03_to_json.py
=============
APF Chatbot - Step 3: Convert Cleaned Text to Structured JSON

What it does:
  - Reads each cleaned .txt file from data/processed/cleaned/
  - Splits into individual pages
  - Auto-detects section name for each page
  - Extracts activity name from filename
  - Adds full metadata to each page
  - Saves one .json file per PDF

Output format per page:
  {
    "id":          "apf_guide_cycling_during_pregnancy_page_3",
    "source_file": "apf_guide_cycling_during_pregnancy",
    "activity":    "cycling",
    "source_type": "web_data",
    "page":        3,
    "section":     "about_activity",
    "section_label": "About This Activity",
    "content":     "Cycling covers a wide range of activities...",
    "word_count":  245
  }

Usage:
    python scripts/03_to_json.py

Input:  data/processed/cleaned/*.txt
Output: data/processed/json/<filename>.json
        data/processed/json/all_documents.json  (combined)
"""

import os
import re
import json
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────

INPUT_DIR  = "data/processed/cleaned"
OUTPUT_DIR = "data/processed/json"

# ── ACTIVITY NAME MAP ─────────────────────────────────────────────────────────
# Extract clean activity name from filename

ACTIVITY_MAP = {
    "cycling"          : "cycling",
    "dancing"          : "dancing",
    "walking"          : "walking",
    "swimming"         : "swimming",
    "running"          : "running",
    "yoga"             : "yoga",
    "pilates"          : "pilates",
    "aquantal"         : "aquanatal",
    "aquanatal"        : "aquanatal",
    "homeworkout"      : "home_workouts",
    "home_workout"     : "home_workouts",
    "personaltraining" : "personal_training",
    "personal_training": "personal_training",
    "resistancetraining": "resistance_training",
    "resistance_training": "resistance_training",
    "big_push"         : "general",
    "big-push"         : "general",
    "endorsement"      : "general",
    "thismummoves"     : "general",
    "postnatal"        : "postnatal",
    "pregnancy_leaflet": "general",
}

# ── SECTION DETECTION ─────────────────────────────────────────────────────────
# Maps keywords found in page content → section name + label

SECTION_RULES = [
    # (keywords_to_check, section_name, section_label)
    # Order matters — more specific first
    (["ABOUT THIS ACTIVITY"],                    "about_activity",   "About This Activity"),
    (["TOP TIPS"],                                "top_tips",         "Top Tips"),
    (["AFTER CHILDBIRTH"],                        "after_childbirth", "After Childbirth"),
    (["GENERAL\nADVICE", "GENERAL ADVICE",
      "KEEP GOING", "STOP & SEEK ADVICE",
      "Chief Medical Officers"],                  "general_advice",   "General Advice"),
    (["ACKNOWLEDGEMENTS", "DISCLAIMER",
      "CONNECT WITH US", "www.activepregnancy"], "acknowledgements", "Acknowledgements"),
    (["DO'S", "DON'T", "DON\u2019T",
      "DONTS", "Avoid ", "Don't "],              "dos_and_donts",    "Do's and Don'ts"),
    (["Not active?", "Already active?",
      "Start gradually", "Keep going"],          "activity_intro",   "Activity Introduction"),
]

def detect_section(content: str) -> tuple:
    """
    Auto-detect section name and label from page content.
    Returns (section_name, section_label)
    """
    content_upper = content.upper()

    for keywords, section_name, section_label in SECTION_RULES:
        for kw in keywords:
            if kw.upper() in content_upper or kw in content:
                return section_name, section_label

    return "general_content", "General Content"


def extract_activity(filename: str) -> str:
    """
    Extract activity name from filename.
    e.g. 'apf_guide_cycling_during_pregnancy' -> 'cycling'
    """
    name = filename.lower()
    # Remove common prefixes/suffixes
    name = name.replace("apf_guide_", "")
    name = name.replace("_during_pregnancy", "")
    name = name.replace("-during-pregnancy", "")
    name = name.replace("apf-our-", "")
    name = name.replace("-programme", "")
    name = name.replace("thismummoves-", "")
    name = name.replace("-leaflet", "")
    name = name.replace("apf_", "")

    # Check against activity map
    for key, value in ACTIVITY_MAP.items():
        if key in name:
            return value

    # Fallback - use cleaned filename
    return name.strip("-_")


def extract_source_type(filename: str) -> str:
    """
    Determine source type from filename.
    All files in web-data/pdf are web_data.
    """
    return "web_data"


def split_into_pages(text: str) -> list:
    """
    Split cleaned text into pages.
    Looks for PAGE N markers in the text.
    """
    pages = []
    page_finder = re.compile(r"PAGE\s+(\d+)\s*\n", re.MULTILINE)
    matches = list(page_finder.finditer(text))

    for idx, match in enumerate(matches):
        page_num = int(match.group(1))
        content_start = match.end()

        if idx + 1 < len(matches):
            next_start = matches[idx + 1].start()
            raw = text[content_start:next_start]
        else:
            raw = text[content_start:]

        # Remove separator lines (made of dashes or box chars)
        lines = raw.split("\n")
        clean_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip separator lines
            if stripped and all(c in ("-", "\u2500", " ") for c in stripped):
                continue
            clean_lines.append(line)

        content = "\n".join(clean_lines).strip()
        if content:
            pages.append((page_num, content))

    return pages

def process_file(input_path: str) -> list:
    """
    Process a single cleaned text file.
    Returns list of document dicts (one per page).
    """
    filename = Path(input_path).stem
    activity = extract_activity(filename)
    source_type = extract_source_type(filename)

    print(f"\n{'='*60}")
    print(f"  {filename}")
    print(f"  Activity: {activity} | Type: {source_type}")
    print(f"{'='*60}")

    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    pages = split_into_pages(text)

    if not pages:
        print(f"  [WARNING] No pages found in {filename}")
        return []

    documents = []

    for page_num, content in pages:
        section_name, section_label = detect_section(content)
        word_count = len(content.split())

        doc = {
            "id"           : f"{filename}_page_{page_num}",
            "source_file"  : filename,
            "activity"     : activity,
            "source_type"  : source_type,
            "page"         : page_num,
            "section"      : section_name,
            "section_label": section_label,
            "word_count"   : word_count,
            "content"      : content,
        }

        documents.append(doc)

        print(f"  Page {page_num:2d} → section: {section_name:<20} | {word_count} words")

    return documents


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("  APF JSON Converter - Step 3")
    print("="*60)
    print(f"  Input  : {INPUT_DIR}")
    print(f"  Output : {OUTPUT_DIR}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Find all cleaned text files (skip report files)
    txt_files = [
        p for p in sorted(Path(INPUT_DIR).glob("*.txt"))
        if "_report" not in p.name and "_clean" not in p.name
    ]

    if not txt_files:
        print(f"\n[ERROR] No .txt files found in {INPUT_DIR}")
        print("  Run 02_clean.py first.")
        return

    print(f"\n  Found {len(txt_files)} file(s):\n")
    for f in txt_files:
        print(f"    - {f.name}")

    all_documents = []

    for txt_path in txt_files:
        docs = process_file(str(txt_path))

        if not docs:
            continue

        # Save individual JSON per file
        filename = Path(txt_path).stem
        out_path = os.path.join(OUTPUT_DIR, f"{filename}.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(docs, f, indent=2, ensure_ascii=False)

        print(f"\n  Saved: {out_path} ({len(docs)} pages)")
        all_documents.extend(docs)

    # Save combined JSON (all documents in one file)
    combined_path = os.path.join(OUTPUT_DIR, "all_documents.json")
    with open(combined_path, 'w', encoding='utf-8') as f:
        json.dump(all_documents, f, indent=2, ensure_ascii=False)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  ALL DONE")
    print(f"{'='*60}")
    print(f"  Files processed : {len(txt_files)}")
    print(f"  Total pages     : {len(all_documents)}")
    print(f"  Combined JSON   : {combined_path}")

    # Section breakdown
    from collections import Counter
    section_counts = Counter(d["section"] for d in all_documents)
    activity_counts = Counter(d["activity"] for d in all_documents)

    print(f"\n  Pages by section:")
    for section, count in sorted(section_counts.items()):
        print(f"    {section:<25} : {count}")

    print(f"\n  Pages by activity:")
    for activity, count in sorted(activity_counts.items()):
        print(f"    {activity:<25} : {count}")

    print(f"\n  Next step: run scripts/04_chunk.py")
    print()


if __name__ == "__main__":
    main()