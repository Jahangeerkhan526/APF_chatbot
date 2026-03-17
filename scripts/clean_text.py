# -*- coding: utf-8 -*-
"""
02_clean.py
===========
APF Chatbot — Step 2: Clean Extracted Text
Safe minimal cleaning — only removes what is clearly noise or duplicate.

What it does:
  1. Remove PAGE 1 (cover page — just title illustration)
  2. Remove PAGE 2 (series list — identical across all 15 PDFs)
  3. Remove garbled [IMAGE CONTENT] OCR blocks (noise lines)
  4. Fix broken hyphenation at line ends (e.g. "activ-\nity" → "activity")
  5. Fix common encoding issues (â€™ → ', â€" → —)
  6. Remove excessive blank lines (3+ → 1)
  7. Keep everything else exactly as-is ✅

What it does NOT do:
  - Does NOT remove any real content
  - Does NOT touch medical/activity text
  - Does NOT remove numbers like 50-100RPM, 6-8 weeks
  - Does NOT rewrite or paraphrase anything

Usage:
    python scripts/02_clean.py

Input:
    data/processed/text/*.txt  (output from 01_extract.py)

Output:
    data/processed/cleaned/<filename>.txt
    data/processed/cleaned/<filename>_clean_report.txt
"""

import os
import re
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────

INPUT_DIR  = "data/processed/text"
OUTPUT_DIR = "data/processed/cleaned"

# These patterns in a line strongly suggest OCR garbage
# We only remove a line if it matches AND is inside [IMAGE CONTENT] block
# Real content lines are NEVER touched
GARBAGE_PATTERNS = [
    r"[A-Za-z]{1,3}\){1,2}\s*\d",          # "Donatecis) 4"
    r"[A-Z][a-z]{1,3}\s+[A-Z][a-z]{1,2}\s+[a-z]{2,4}$",  # "Come Sey ee"
    r"^[A-Z][a-z]{1,3}\s+[a-z]{3,5}$",     # very short garbled lines
    r"Fae\s+eee",                            # known garbage
    r"Donatecis",                            # known garbage
    r"Sey\s+ee",                             # known garbage
    r"<[!?/]",                               # HTML/OCR artifacts like <!
    r"^\s*[^\w\s]{3,}\s*$",                  # lines of only symbols
    r"Thy\s+PR[a-z]+ancy",                   # garbled "The Pregnancy"
    r"Garona",                               # known OCR garbage word
]

# Encoding fixes — common PDF encoding issues
# Encoding fixes
def build_encoding_fixes():
    fixes = []
    fixes.append(("’", "'"))  # right single quote
    fixes.append(("‘", "'"))  # left single quote
    fixes.append(("“", '"'))  # left double quote
    fixes.append(("”", '"'))  # right double quote
    fixes.append(("–", "-"))  # en dash
    fixes.append(("—", "-"))  # em dash
    fixes.append(("•", "*"))  # bullet
    fixes.append((" ", " "))  # non-breaking space
    fixes.append(("…", "..."))  # ellipsis
    return fixes

ENCODING_FIXES = build_encoding_fixes()

# ── SETUP ─────────────────────────────────────────────────────────────────────

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────

def fix_encoding(text: str) -> str:
    """Fix common PDF encoding artifacts."""
    for bad, good in ENCODING_FIXES:
        text = text.replace(bad, good)
    return text


def fix_broken_hyphenation(text: str) -> str:
    """
    Fix words broken across lines with a hyphen.
    e.g. "activ-\nity" → "activity"
    Only fixes clear word breaks — NOT intentional hyphens like "6-8 weeks"
    """
    # Pattern: word ending in hyphen followed by newline + lowercase word start
    text = re.sub(r'(\w+)-\n([a-z])', r'\1\2', text)
    return text


def is_garbage_line(line: str) -> bool:
    """
    Check if a line is clearly OCR garbage.
    Only used inside [IMAGE CONTENT] blocks.
    """
    stripped = line.strip()
    if not stripped:
        return False
    for pattern in GARBAGE_PATTERNS:
        if re.search(pattern, stripped):
            return True
    return False


def clean_image_content_block(block: str) -> str:
    """
    Clean an [IMAGE CONTENT] block.
    Keep lines that are clearly real content.
    Remove lines that are clearly OCR garbage.
    If after cleaning the block has < 5 real words → remove entire block.
    """
    lines = block.split('\n')
    kept_lines = []
    removed = []

    for line in lines:
        if line.strip() == '[IMAGE CONTENT]':
            kept_lines.append(line)
            continue
        if is_garbage_line(line):
            removed.append(line.strip())
        else:
            kept_lines.append(line)

    # Count real words in what we kept (excluding the [IMAGE CONTENT] label)
    content_lines = [l for l in kept_lines if l.strip() != '[IMAGE CONTENT]']
    word_count = sum(len(l.split()) for l in content_lines)

    if word_count < 5:
        # Entire block is garbage — remove it
        return f"[IMAGE CONTENT — removed: {len(removed)} garbage lines, only {word_count} real words remained]"

    cleaned = '\n'.join(kept_lines)
    return cleaned


def split_pages(text: str) -> list:
    """
    Split full document text into pages.
    Returns list of (page_num, page_content) tuples.
    """
    pages = []
    # Split on PAGE markers
    pattern = r'─{50,}\nPAGE (\d+)\n─{50,}\n'
    parts = re.split(pattern, text)

    # parts = [before_first_page, page_num, content, page_num, content, ...]
    # Skip the header (before first page)
    i = 1
    while i < len(parts) - 1:
        page_num = int(parts[i])
        content  = parts[i + 1].strip()
        pages.append((page_num, content))
        i += 2

    return pages


def clean_page_content(content: str) -> str:
    """Clean content of a single page."""

    # Fix encoding
    content = fix_encoding(content)

    # Fix broken hyphenation
    content = fix_broken_hyphenation(content)

    # Clean [IMAGE CONTENT] blocks
    # Find and process each [IMAGE CONTENT] block
    image_block_pattern = r'\[IMAGE CONTENT\].*?(?=\n─{50,}|\Z)'
    def replace_image_block(match):
        block = match.group(0)
        return clean_image_content_block(block)

    content = re.sub(image_block_pattern, replace_image_block,
                     content, flags=re.DOTALL)

    # Remove excessive blank lines (3+ consecutive → max 2)
    content = re.sub(r'\n{3,}', '\n\n', content)

    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in content.split('\n')]
    content = '\n'.join(lines)

    return content.strip()


def clean_file(input_path: str) -> dict:
    """
    Clean a single extracted text file.
    Returns stats dict.
    """
    filename = Path(input_path).stem
    print(f"\n{'='*60}")
    print(f"  Cleaning: {filename}")
    print(f"{'='*60}")

    with open(input_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    # Extract header info
    lines = raw_text.split('\n')
    header_lines = []
    for line in lines[:5]:
        if line.startswith('SOURCE FILE') or line.startswith('TOTAL PAGES') or line.startswith('='):
            header_lines.append(line)

    # Split into pages
    pages = split_pages(raw_text)
    total_pages = len(pages)
    print(f"  Total pages found: {total_pages}")

    kept_pages   = []
    skipped_pages = []
    report_lines = [
        f"CLEAN REPORT: {filename}",
        "=" * 60,
        f"{'Page':<6} {'Action':<12} {'Words Before':<14} {'Words After'}",
        "-" * 60,
    ]

    for page_num, content in pages:
        words_before = len(content.split())

        # ── SKIP PAGE 1 (cover) ───────────────────────────────────────────────
        if page_num == 1:
            print(f"  Page {page_num:2d} → SKIPPED (cover page)")
            report_lines.append(f"{page_num:<6} {'SKIPPED':<12} {words_before:<14} 0  (cover page)")
            skipped_pages.append(page_num)
            continue

        # ── SKIP PAGE 2 (series list — same in all PDFs) ─────────────────────
        if page_num == 2 and (
            "ACTIVITIES COVERED IN THIS SERIES" in content or
            "AQUANATAL" in content and "CYCLING" in content and
            "DANCING" in content and "SWIMMING" in content
        ):
            print(f"  Page {page_num:2d} → SKIPPED (series list — duplicate across all PDFs)")
            report_lines.append(f"{page_num:<6} {'SKIPPED':<12} {words_before:<14} 0  (series list)")
            skipped_pages.append(page_num)
            continue

        # ── CLEAN page content ────────────────────────────────────────────────
        cleaned_content = clean_page_content(content)
        words_after = len(cleaned_content.split())
        words_removed = words_before - words_after

        print(f"  Page {page_num:2d} → KEPT    "
              f"({words_before}w → {words_after}w, "
              f"removed {words_removed}w)")

        report_lines.append(
            f"{page_num:<6} {'KEPT':<12} {words_before:<14} {words_after}"
            + (f"  (-{words_removed} noise)" if words_removed > 0 else "")
        )

        # Rebuild page block with separator
        page_block = (
            f"\n{'─'*50}\n"
            f"PAGE {page_num}\n"
            f"{'─'*50}\n"
            f"{cleaned_content}"
        )
        kept_pages.append(page_block)

    # ── Build output ──────────────────────────────────────────────────────────
    header = '\n'.join(header_lines)
    full_cleaned = header + '\n' + '\n'.join(kept_pages)

    # Save cleaned text
    out_path = os.path.join(OUTPUT_DIR, f"{filename}.txt")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(full_cleaned)

    # Save report
    report_lines.append("-" * 60)
    report_lines.append(f"Pages kept   : {len(kept_pages)}")
    report_lines.append(f"Pages skipped: {len(skipped_pages)} {skipped_pages}")
    report_lines.append(f"Output       : {out_path}")
    out_report = os.path.join(OUTPUT_DIR, f"{filename}_clean_report.txt")
    with open(out_report, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    print(f"\n  ✅ Saved : {out_path}")
    print(f"  📋 Report: {out_report}")
    print(f"  Pages kept: {len(kept_pages)} / {total_pages}")

    return {
        "file"          : filename,
        "total_pages"   : total_pages,
        "kept_pages"    : len(kept_pages),
        "skipped_pages" : skipped_pages,
        "output"        : out_path,
    }


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("  APF Text Cleaner — Step 2")
    print("=" * 60)
    print(f"  Input  : {INPUT_DIR}")
    print(f"  Output : {OUTPUT_DIR}")
    print(f"\n  Rules:")
    print(f"    ✂️  Skip cover pages (page 1)")
    print(f"    ✂️  Skip series list pages (page 2)")
    print(f"    ✂️  Remove garbled OCR lines from image blocks")
    print(f"    🔧 Fix encoding issues")
    print(f"    🔧 Fix broken hyphenation")
    print(f"    🔧 Remove excessive blank lines")
    print(f"    ✅ Keep all real content unchanged")

    # Find all extracted text files (skip report files)
    txt_files = [
        p for p in sorted(Path(INPUT_DIR).glob("*.txt"))
        if "_report" not in p.name
    ]

    if not txt_files:
        print(f"\n❌  No .txt files found in {INPUT_DIR}")
        print("    Run 01_extract.py first.")
        return

    print(f"\n  Found {len(txt_files)} file(s) to clean:\n")
    for f in txt_files:
        print(f"    - {f.name}")

    results = []
    for txt_path in txt_files:
        result = clean_file(str(txt_path))
        results.append(result)

    # ── Final summary ─────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  ✅  CLEANING COMPLETE")
    print(f"{'='*60}")
    print(f"  Files cleaned : {len(results)}")
    print(f"  Output folder : {OUTPUT_DIR}")
    print(f"\n  Summary:")
    for r in results:
        skipped_str = str(r['skipped_pages'])
        print(f"    {r['file'][:45]:<45} | "
              f"kept {r['kept_pages']}/{r['total_pages']} pages | "
              f"skipped {skipped_str}")

    print(f"\n  ➡️   Next step: run scripts/03_to_json.py")
    print()


if __name__ == "__main__":
    main()