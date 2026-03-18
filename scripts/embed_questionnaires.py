# -*- coding: utf-8 -*-
"""
embed_questionnaires.py
=======================
APF Nancy Chatbot - Embed GAQ-P and GAQ-PP questions into ChromaDB

What it does:
  - Reads data/processed/questionnaires/questions.json
  - Embeds each question using sentence-transformers
  - Stores in ChromaDB with metadata
  - Skips duplicates automatically

Usage:
    python scripts/embed_questionnaires.py

Input:  data/processed/questionnaires/questions.json
Output: data/vectordb/chroma/ (ChromaDB collection)
"""

import json
import time
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb

# ── CONFIG ────────────────────────────────────────────────────────────────────
QUESTIONS_JSON = "data/processed/questionnaires/questions.json"
VECTORDB_DIR   = "data/vectordb/chroma"
COLLECTION     = "apf_knowledge"
EMBED_MODEL    = "all-MiniLM-L6-v2"


def main():
    print("\n" + "="*60)
    print("  APF Questionnaire Embedder → ChromaDB")
    print("="*60)
    print(f"  Input : {QUESTIONS_JSON}")
    print(f"  DB    : {VECTORDB_DIR}")

    # Check input file
    if not Path(QUESTIONS_JSON).exists():
        print(f"\n[ERROR] {QUESTIONS_JSON} not found!")
        print(f"  Run first: python scripts/questionnaire_to_json.py")
        return

    # Load JSON
    with open(QUESTIONS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    gaqp_qs  = data["gaqp_questions"]
    gaqpp_qs = data["gaqpp_questions"]
    pelvic   = data["pelvic_symptoms"]
    meta     = data["metadata"]

    print(f"\n  GAQ-P questions  : {meta['total_gaqp']}")
    print(f"  GAQ-PP questions : {meta['total_gaqpp']}")
    print(f"  Pelvic symptoms  : {meta['total_pelvic']}")

    # Load embedding model
    print(f"\n  Loading embedding model: {EMBED_MODEL}...")
    t0    = time.time()
    model = SentenceTransformer(EMBED_MODEL)
    print(f"  Model loaded in {time.time()-t0:.1f}s")

    # Connect to ChromaDB
    print(f"\n  Connecting to ChromaDB...")
    client     = chromadb.PersistentClient(path=VECTORDB_DIR)
    collection = client.get_collection(COLLECTION)
    before     = collection.count()
    print(f"  Existing chunks: {before}")

    # Combine all items to embed
    all_items = []

    # GAQ-P questions
    for q in gaqp_qs:
        all_items.append({
            "id"      : q["question_id"],
            "text"    : f"Screening question for pregnancy: {q['question_original']}",
            "metadata": {
                "source_type"      : "screening_question",
                "questionnaire"    : q["questionnaire"],
                "for"              : q["for"],
                "section"          : q["section"],
                "question_number"  : q["question_number"],
                "question_original": q["question_original"],
                "answer_type"      : q["answer_type"],
                "if_yes"           : q["if_yes"],
                "activity"         : q["for"],
                "section_label"    : f"{q['questionnaire']} Screening",
                "source_file"      : meta["source_gaqp"],
            }
        })

    # GAQ-PP questions
    for q in gaqpp_qs:
        all_items.append({
            "id"      : q["question_id"],
            "text"    : f"Screening question for postnatal: {q['question_original']}",
            "metadata": {
                "source_type"      : "screening_question",
                "questionnaire"    : q["questionnaire"],
                "for"              : q["for"],
                "section"          : q["section"],
                "question_number"  : q["question_number"],
                "question_original": q["question_original"],
                "answer_type"      : q["answer_type"],
                "if_yes"           : q["if_yes"],
                "activity"         : q["for"],
                "section_label"    : f"{q['questionnaire']} Screening",
                "source_file"      : meta["source_gaqpp"],
            }
        })

    # Pelvic symptoms
    for s in pelvic:
        all_items.append({
            "id"      : s["symptom_id"],
            "text"    : f"Pelvic health symptom postnatal: {s['original']}",
            "metadata": {
                "source_type"  : "pelvic_symptom",
                "questionnaire": "PELVIC",
                "for"          : s["for"],
                "section"      : "pelvic_health",
                "question_original": s["original"],
                "action"       : s["action"],
                "signpost"     : s["signpost"],
                "activity"     : s["for"],
                "section_label": "Pelvic Health Symptoms",
                "source_file"  : meta["source_pelvic"],
            }
        })

    # Remove duplicates within the batch first
    seen_ids  = set()
    deduped   = []
    for item in all_items:
        if item["id"] not in seen_ids:
            seen_ids.add(item["id"])
            deduped.append(item)
    all_items = deduped

    # Check duplicates against ChromaDB
    print(f"\n  Checking for duplicates...")
    new_items = []
    for item in all_items:
        try:
            existing = collection.get(ids=[item["id"]])
            if not existing["ids"]:
                new_items.append(item)
        except:
            new_items.append(item)

    skipped = len(all_items) - len(new_items)
    print(f"  Already in DB : {skipped}")
    print(f"  To add        : {len(new_items)}")

    if not new_items:
        print(f"\n  ✅ Nothing to add — all questions already in ChromaDB!")
        return

    # Embed and store
    print(f"\n  Embedding and storing...")
    print(f"\n  {'Type':<25} {'For':<12} {'Added':>6}")
    print(f"  {'-'*45}")

    ids        = [i["id"] for i in new_items]
    texts      = [i["text"] for i in new_items]
    metadatas  = [i["metadata"] for i in new_items]
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    collection.add(
        ids        = ids,
        embeddings = embeddings,
        documents  = texts,
        metadatas  = metadatas,
    )

    # Count by type
    gaqp_added   = sum(1 for i in new_items if i["metadata"]["questionnaire"] == "GAQ-P")
    gaqpp_added  = sum(1 for i in new_items if i["metadata"]["questionnaire"] == "GAQ-PP")
    pelvic_added = sum(1 for i in new_items if i["metadata"]["source_type"] == "pelvic_symptom")

    print(f"  {'GAQ-P screening':<25} {'pregnancy':<12} {gaqp_added:>6}")
    print(f"  {'GAQ-PP screening':<25} {'postnatal':<12} {gaqpp_added:>6}")
    print(f"  {'Pelvic symptoms':<25} {'postnatal':<12} {pelvic_added:>6}")

    # Final count
    after = collection.count()
    print(f"\n{'='*60}")
    print(f"  ✅ EMBEDDING COMPLETE!")
    print(f"{'='*60}")
    print(f"  Questions added  : {len(new_items)}")
    print(f"  ChromaDB before  : {before}")
    print(f"  ChromaDB after   : {after}")

    # Test query
    print(f"\n  Test query: 'safety questions for pregnancy'")
    test_emb = model.encode(["safety questions for pregnancy"])
    results  = collection.query(
        query_embeddings = test_emb.tolist(),
        n_results        = 3,
        include          = ["documents", "metadatas", "distances"],
        where            = {"source_type": "screening_question"}
    )
    for i, (doc, m, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    )):
        score = round(1 - dist, 3)
        print(f"\n  [{i+1}] Score: {score} | {m['questionnaire']} | Q{m['question_number']}")
        print(f"       {m['question_original'][:80]}...")

    print(f"\n  Nancy can now ask screening questions! 🌸")
    print(f"  Next step → Build database/db.py")


if __name__ == "__main__":
    main()