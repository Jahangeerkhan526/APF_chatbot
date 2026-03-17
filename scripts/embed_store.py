# -*- coding: utf-8 -*-
"""
05_embed_store.py
=================
APF Chatbot - Step 5: Embed chunks and store in ChromaDB

What it does:
  - Loads all_chunks.json (145 chunks)
  - Embeds each chunk using sentence-transformers (all-MiniLM-L6-v2)
  - Stores embeddings + metadata in ChromaDB (persistent local DB)
  - Runs 100% offline - no internet, no API keys needed

Usage:
    python scripts/05_embed_store.py

Input:  data/processed/chunks/all_chunks.json
Output: data/vectordb/chroma/  (persistent ChromaDB)
"""

import os
import json
import time
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# ── CONFIG ────────────────────────────────────────────────────────────────────

CHUNKS_FILE  = "data/processed/chunks/all_chunks.json"
VECTORDB_DIR = "data/vectordb/chroma"
COLLECTION   = "apf_knowledge"

# Embedding model - local, free, fast
EMBED_MODEL  = "all-MiniLM-L6-v2"

# Batch size for embedding (process N chunks at once)
BATCH_SIZE   = 32

# ── SETUP ─────────────────────────────────────────────────────────────────────

os.makedirs(VECTORDB_DIR, exist_ok=True)


def main():
    print("\n" + "="*60)
    print("  APF Embedder + ChromaDB Store — Step 5")
    print("="*60)
    print(f"  Chunks  : {CHUNKS_FILE}")
    print(f"  VectorDB: {VECTORDB_DIR}")
    print(f"  Model   : {EMBED_MODEL}")
    print(f"  Mode    : 100% local / offline")

    # ── Load chunks ───────────────────────────────────────────────────────────
    if not Path(CHUNKS_FILE).exists():
        print(f"\n[ERROR] {CHUNKS_FILE} not found. Run 04_chunk.py first.")
        return

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"\n  Loaded {len(chunks)} chunks")

    # ── Load embedding model ──────────────────────────────────────────────────
    print(f"\n  Loading embedding model: {EMBED_MODEL}")
    print(f"  (First run downloads ~90MB — subsequent runs are instant)")
    t0 = time.time()
    model = SentenceTransformer(EMBED_MODEL)
    print(f"  Model loaded in {time.time()-t0:.1f}s")

    # ── Setup ChromaDB ────────────────────────────────────────────────────────
    print(f"\n  Setting up ChromaDB at: {VECTORDB_DIR}")
    client = chromadb.PersistentClient(path=VECTORDB_DIR)

    # Delete existing collection if it exists (fresh rebuild)
    try:
        client.delete_collection(COLLECTION)
        print(f"  Deleted existing collection: {COLLECTION}")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"}  # cosine similarity for text
    )
    print(f"  Created collection: {COLLECTION}")

    # ── Embed and store in batches ────────────────────────────────────────────
    print(f"\n  Embedding {len(chunks)} chunks in batches of {BATCH_SIZE}...")
    print(f"  {'Batch':<8} {'Chunks':<10} {'Time':>8}  {'Progress'}")
    print(f"  {'-'*50}")

    total_stored = 0
    t_start = time.time()

    for batch_start in range(0, len(chunks), BATCH_SIZE):
        batch      = chunks[batch_start:batch_start + BATCH_SIZE]
        batch_num  = (batch_start // BATCH_SIZE) + 1
        t_batch    = time.time()

        # Extract text for embedding
        texts = [c["content"] for c in batch]

        # Create embeddings
        embeddings = model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True
        )

        # Prepare for ChromaDB
        ids        = [c["chunk_id"] for c in batch]
        documents  = texts
        metadatas  = []

        for c in batch:
            metadatas.append({
                "parent_id"    : c["parent_id"],
                "source_file"  : c["source_file"],
                "activity"     : c["activity"],
                "source_type"  : c["source_type"],
                "page"         : str(c["page"]),
                "section"      : c["section"],
                "section_label": c["section_label"],
                "chunk_index"  : str(c["chunk_index"]),
                "total_chunks" : str(c["total_chunks"]),
                "word_count"   : str(c["word_count"]),
            })

        # Store in ChromaDB
        collection.add(
            ids        = ids,
            embeddings = embeddings.tolist(),
            documents  = documents,
            metadatas  = metadatas,
        )

        total_stored += len(batch)
        elapsed = time.time() - t_batch
        progress = f"{total_stored}/{len(chunks)} ({100*total_stored//len(chunks)}%)"

        print(f"  {batch_num:<8} {len(batch):<10} {elapsed:>6.1f}s  {progress}")

    total_time = time.time() - t_start

    # ── Verify ────────────────────────────────────────────────────────────────
    count = collection.count()
    print(f"\n  Verification: {count} chunks stored in ChromaDB ✅")

    # ── Quick test query ──────────────────────────────────────────────────────
    print(f"\n  Running test query: 'cycling during pregnancy'")
    test_embedding = model.encode(["cycling during pregnancy"])
    results = collection.query(
        query_embeddings=test_embedding.tolist(),
        n_results=3,
        include=["documents", "metadatas", "distances"]
    )

    print(f"\n  Top 3 results:")
    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    )):
        score = round(1 - dist, 3)  # convert distance to similarity
        print(f"\n  [{i+1}] Score: {score} | Activity: {meta['activity']} | Section: {meta['section']}")
        print(f"       Source: {meta['source_file']} (page {meta['page']})")
        print(f"       Text: {doc[:120]}...")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  EMBEDDING COMPLETE")
    print(f"{'='*60}")
    print(f"  Chunks embedded : {total_stored}")
    print(f"  Total time      : {total_time:.1f}s")
    print(f"  ChromaDB path   : {VECTORDB_DIR}")
    print(f"  Collection      : {COLLECTION}")
    print(f"  Embedding model : {EMBED_MODEL}")
    print(f"\n  Next step: run scripts/06_retrieve.py to test RAG queries")
    print()


if __name__ == "__main__":
    main()