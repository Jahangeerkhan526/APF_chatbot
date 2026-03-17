# -*- coding: utf-8 -*-
"""
04_chunk.py
===========
APF Chatbot - Step 4: Chunk JSON documents for RAG

What it does:
  - Reads all_documents.json (84 pages)
  - Splits each page content into smaller overlapping chunks
  - Each chunk is ~150 words with 30 word overlap
  - Keeps all metadata from parent page
  - Saves chunks ready for embedding

Why chunking?
  - Embedding models work best on short focused text (100-200 words)
  - Overlap ensures context is not lost at chunk boundaries
  - Smaller chunks = more precise retrieval

Output format per chunk:
  {
    "chunk_id":    "cycling_page_3_chunk_1",
    "parent_id":   "apf_guide_cycling_during_pregnancy_page_3",
    "source_file": "apf_guide_cycling_during_pregnancy",
    "activity":    "cycling",
    "source_type": "web_data",
    "page":        3,
    "section":     "about_activity",
    "section_label": "About This Activity",
    "chunk_index": 1,
    "total_chunks": 2,
    "word_count":  148,
    "content":     "Cycling covers a wide range..."
  }

Usage:
    python scripts/04_chunk.py

Input:  data/processed/json/all_documents.json
Output: data/processed/chunks/all_chunks.json
        data/processed/chunks/chunks_summary.txt
"""

import os
import json
from pathlib import Path
from collections import Counter

# ── CONFIG ────────────────────────────────────────────────────────────────────

INPUT_FILE  = "data/processed/json/all_documents.json"
OUTPUT_DIR  = "data/processed/chunks"

# Chunking settings
CHUNK_SIZE    = 150   # target words per chunk
CHUNK_OVERLAP = 30    # words overlap between chunks
MIN_CHUNK     = 40    # skip chunks smaller than this (too small to be useful)

# Pages to skip entirely from chunking (not useful for RAG)
SKIP_SECTIONS = {"acknowledgements"}  # disclaimer/version info pages

# ── SETUP ─────────────────────────────────────────────────────────────────────

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── CHUNKER ───────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int, overlap: int) -> list:
    """
    Split text into overlapping word-based chunks.

    Example with chunk_size=5, overlap=2:
    words = [A B C D E F G H I J]
    chunk1 = [A B C D E]
    chunk2 = [D E F G H]   ← overlaps D E
    chunk3 = [G H I J]     ← overlaps G H
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    start  = 0

    while start < len(words):
        end        = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunk_text  = " ".join(chunk_words)
        chunks.append(chunk_text)

        # If we've reached the end, stop
        if end == len(words):
            break

        # Move forward by (chunk_size - overlap)
        start += chunk_size - overlap

    return chunks


def process_document(doc: dict) -> list:
    """
    Split a single page document into chunks.
    Returns list of chunk dicts.
    """
    # Skip acknowledgements/disclaimer pages — not useful for RAG
    if doc.get("section") in SKIP_SECTIONS:
        return []

    content = doc.get("content", "").strip()
    if not content:
        return []

    # Split into chunks
    raw_chunks = chunk_text(content, CHUNK_SIZE, CHUNK_OVERLAP)

    chunks = []
    valid_index = 1

    for i, chunk_content in enumerate(raw_chunks):
        word_count = len(chunk_content.split())

        # Skip tiny chunks
        if word_count < MIN_CHUNK:
            continue

        chunk = {
            "chunk_id"    : f"{doc['source_file']}_page_{doc['page']}_chunk_{valid_index}",
            "parent_id"   : doc["id"],
            "source_file" : doc["source_file"],
            "activity"    : doc["activity"],
            "source_type" : doc["source_type"],
            "page"        : doc["page"],
            "section"     : doc["section"],
            "section_label": doc["section_label"],
            "chunk_index" : valid_index,
            "total_chunks": len(raw_chunks),   # approximate, updated after
            "word_count"  : word_count,
            "content"     : chunk_content,
        }
        chunks.append(chunk)
        valid_index += 1

    # Update total_chunks to reflect actual valid chunks
    for chunk in chunks:
        chunk["total_chunks"] = len(chunks)

    return chunks


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("  APF Chunker — Step 4")
    print("="*60)
    print(f"  Input  : {INPUT_FILE}")
    print(f"  Output : {OUTPUT_DIR}")
    print(f"  Settings: chunk_size={CHUNK_SIZE} words | overlap={CHUNK_OVERLAP} words | min={MIN_CHUNK} words")
    print(f"  Skipping sections: {SKIP_SECTIONS}")

    # Load all documents
    if not Path(INPUT_FILE).exists():
        print(f"\n[ERROR] {INPUT_FILE} not found. Run 03_to_json.py first.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        documents = json.load(f)

    print(f"\n  Loaded {len(documents)} pages from JSON")

    # Process each document
    all_chunks   = []
    skipped      = 0
    section_stats = Counter()

    print(f"\n  {'Source':<50} {'Pages':>6} {'Chunks':>7} {'Skipped':>8}")
    print(f"  {'-'*75}")

    # Group by source file for reporting
    from collections import defaultdict
    by_source = defaultdict(list)
    for doc in documents:
        by_source[doc["source_file"]].append(doc)

    for source_file, docs in sorted(by_source.items()):
        file_chunks  = 0
        file_skipped = 0

        for doc in docs:
            chunks = process_document(doc)
            if not chunks:
                file_skipped += 1
                skipped += 1
            else:
                all_chunks.extend(chunks)
                file_chunks += len(chunks)
                for c in chunks:
                    section_stats[c["section"]] += 1

        short_name = source_file[:48]
        print(f"  {short_name:<50} {len(docs):>6} {file_chunks:>7} {file_skipped:>8}")

    # ── Save chunks ───────────────────────────────────────────────────────────
    out_path = os.path.join(OUTPUT_DIR, "all_chunks.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    # ── Save summary ──────────────────────────────────────────────────────────
    activity_stats  = Counter(c["activity"] for c in all_chunks)
    word_counts     = [c["word_count"] for c in all_chunks]
    avg_words       = sum(word_counts) / len(word_counts) if word_counts else 0

    summary_lines = [
        "APF RAG CHUNKS SUMMARY",
        "=" * 50,
        f"Total pages processed : {len(documents)}",
        f"Pages skipped         : {skipped} (acknowledgements)",
        f"Total chunks created  : {len(all_chunks)}",
        f"Average chunk size    : {avg_words:.0f} words",
        f"Min chunk size        : {min(word_counts) if word_counts else 0} words",
        f"Max chunk size        : {max(word_counts) if word_counts else 0} words",
        "",
        "Chunks by section:",
    ]
    for section, count in sorted(section_stats.items()):
        summary_lines.append(f"  {section:<25} : {count}")

    summary_lines += ["", "Chunks by activity:"]
    for activity, count in sorted(activity_stats.items()):
        summary_lines.append(f"  {activity:<25} : {count}")

    summary_path = os.path.join(OUTPUT_DIR, "chunks_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))

    # ── Final output ──────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  CHUNKING COMPLETE")
    print(f"{'='*60}")
    print(f"  Total chunks    : {len(all_chunks)}")
    print(f"  Avg chunk size  : {avg_words:.0f} words")
    print(f"  Pages skipped   : {skipped} (acknowledgements)")
    print(f"  Output file     : {out_path}")
    print(f"  Summary         : {summary_path}")
    print(f"\n  Chunks by section:")
    for section, count in sorted(section_stats.items()):
        print(f"    {section:<25} : {count}")
    print(f"\n  Chunks by activity:")
    for activity, count in sorted(activity_stats.items()):
        print(f"    {activity:<25} : {count}")
    print(f"\n  Next step: run scripts/05_embed_store.py")
    print()


if __name__ == "__main__":
    main()