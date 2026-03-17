# -*- coding: utf-8 -*-
"""
06_retrieve.py
==============
APF Chatbot - Step 6: RAG Retrieval Engine

What it does:
  - Takes a user question
  - Embeds the question using same model as chunks
  - Searches ChromaDB for most similar chunks
  - Returns top results with source info
  - Includes safety check - stops if symptoms mentioned

This is the core RAG engine Nancy will use.

Usage:
    # Interactive mode
    python scripts/06_retrieve.py

    # Single query mode
    python scripts/06_retrieve.py --query "is cycling safe during pregnancy"
"""

import argparse
from sentence_transformers import SentenceTransformer
import chromadb

# ── CONFIG ────────────────────────────────────────────────────────────────────

VECTORDB_DIR  = "data/vectordb/chroma"
COLLECTION    = "apf_knowledge"
EMBED_MODEL   = "all-MiniLM-L6-v2"
TOP_K         = 5      # number of results to return
MIN_SCORE     = 0.25   # minimum similarity score (0-1)

# ── SAFETY KEYWORDS ───────────────────────────────────────────────────────────
# If user mentions any of these → stop RAG, advise GP/midwife

SAFETY_KEYWORDS = [
    # Cardiac / respiratory
    "chest pain", "chest tightness", "heart pain", "palpitations",
    "shortness of breath", "can't breathe", "cannot breathe",

    # Bleeding / fluid
    "bleeding", "vaginal bleeding", "amniotic fluid",
    "waters broke", "waters breaking",

    # Dizziness / consciousness
    "dizziness", "dizzy", "faint", "fainting", "lightheaded",
    "lightheadedness", "blacked out", "passed out",

    # Pain
    "chest pain", "severe pain", "excruciating", "unbearable pain",
    "abdominal pain", "pelvic pain",

    # Baby concerns
    "baby not moving", "no movement", "reduced movement",
    "reduced fetal movement",

    # Vision / head
    "blurred vision", "vision problems", "severe headache",
    "sudden headache",

    # High risk medical conditions
    "high blood pressure", "hypertension", "preeclampsia",
    "gestational diabetes", "diabetes",
    "epilepsy", "seizure",
    "heart condition", "heart disease", "cardiac",
    "blood clot", "deep vein thrombosis", "dvt",
    "anaemia", "anemia",
    "cancer", "tumour", "tumor", "chemotherapy",
    "thyroid", "kidney disease", "liver disease",
    "placenta previa", "placenta praevia",
    "incompetent cervix", "cerclage",
    "premature labour", "preterm",
    "twins", "triplets", "multiple pregnancy",
    "intrauterine growth", "iugr",
    "miscarriage", "ectopic",

    # Injury / accident
    "fell", "fall", "accident", "injured", "injury",
    "fracture", "broken bone",

    # Temperature
    "fever", "high temperature", "overheating",

    # Labour signs
    "contractions", "labour", "labor", "waters",
    "swollen face", "swelling face", "swollen hands",
]

SAFETY_RESPONSE = """
⚠️  SAFETY ALERT — Please consult a healthcare professional

Based on what you've described, I'm not able to provide
exercise guidance at this time.

Please contact:
  - Your GP or midwife immediately
  - NHS 111 for urgent advice
  - 999 in an emergency

Do not continue or start any physical activity until
you have spoken with your healthcare team.

www.activepregnancyfoundation.org
"""

# ── RETRIEVER CLASS ───────────────────────────────────────────────────────────

class APFRetriever:
    """
    Core RAG retrieval engine for APF knowledge base.
    """

    def __init__(self):
        print("  Loading embedding model...")
        self.model  = SentenceTransformer(EMBED_MODEL)

        print("  Connecting to ChromaDB...")
        client      = chromadb.PersistentClient(path=VECTORDB_DIR)
        self.col    = client.get_collection(COLLECTION)

        count = self.col.count()
        print(f"  Connected — {count} chunks in knowledge base\n")


    def safety_check(self, query: str) -> bool:
        """
        Returns True if query contains safety/symptom keywords.
        """
        query_lower = query.lower()
        for kw in SAFETY_KEYWORDS:
            if kw in query_lower:
                return True
        return False


    def retrieve(self, query: str, top_k: int = TOP_K,
                 filter_activity: str = None,
                 filter_section: str = None) -> dict:
        """
        Retrieve most relevant chunks for a query.

        Args:
            query           : user question
            top_k           : number of results to return
            filter_activity : optional filter e.g. "cycling"
            filter_section  : optional filter e.g. "dos_and_donts"

        Returns:
            dict with keys: safety_flag, results, query
        """

        # ── Safety check first ────────────────────────────────────────────────
        if self.safety_check(query):
            return {
                "safety_flag": True,
                "results"    : [],
                "query"      : query,
                "response"   : SAFETY_RESPONSE,
            }

        # ── Embed query ───────────────────────────────────────────────────────
        query_embedding = self.model.encode([query])

        # ── Build filters ─────────────────────────────────────────────────────
        where = None
        if filter_activity and filter_section:
            where = {"$and": [
                {"activity": {"$eq": filter_activity}},
                {"section":  {"$eq": filter_section}},
            ]}
        elif filter_activity:
            where = {"activity": {"$eq": filter_activity}}
        elif filter_section:
            where = {"section": {"$eq": filter_section}}

        # ── Query ChromaDB ────────────────────────────────────────────────────
        query_kwargs = {
            "query_embeddings": query_embedding.tolist(),
            "n_results"       : top_k,
            "include"         : ["documents", "metadatas", "distances"],
        }
        if where:
            query_kwargs["where"] = where

        results = self.col.query(**query_kwargs)

        # ── Format results ────────────────────────────────────────────────────
        formatted = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            score = round(1 - dist, 3)  # cosine distance → similarity
            if score < MIN_SCORE:
                continue  # skip low confidence results

            formatted.append({
                "score"        : score,
                "content"      : doc,
                "activity"     : meta["activity"],
                "section"      : meta["section"],
                "section_label": meta["section_label"],
                "source_file"  : meta["source_file"],
                "page"         : meta["page"],
                "chunk_id"     : meta.get("chunk_index", "?"),
            })

        return {
            "safety_flag": False,
            "results"    : formatted,
            "query"      : query,
        }


    def format_for_llm(self, retrieval: dict) -> str:
        """
        Format retrieved chunks into a context string for the LLM.
        This is what gets passed to the local LLM in Step 7.
        """
        if retrieval["safety_flag"]:
            return retrieval["response"]

        if not retrieval["results"]:
            return "No relevant information found in the APF knowledge base."

        lines = [
            f"QUESTION: {retrieval['query']}",
            "",
            "RELEVANT INFORMATION FROM APF KNOWLEDGE BASE:",
            "=" * 50,
        ]

        for i, r in enumerate(retrieval["results"], 1):
            lines += [
                f"\n[Source {i}]",
                f"Activity : {r['activity']}",
                f"Section  : {r['section_label']}",
                f"Document : {r['source_file']} (page {r['page']})",
                f"Score    : {r['score']}",
                f"Content  :",
                r["content"],
                "-" * 40,
            ]

        lines += [
            "",
            "INSTRUCTION: Answer the question using ONLY the information above.",
            "If the information doesn't fully answer the question, say so.",
            "Always recommend consulting a GP or midwife for medical decisions.",
        ]

        return "\n".join(lines)


# ── INTERACTIVE / CLI MODE ────────────────────────────────────────────────────

def run_interactive(retriever: APFRetriever):
    """Interactive question-answering loop."""

    print("=" * 60)
    print("  APF RAG Retrieval Engine — Interactive Mode")
    print("=" * 60)
    print("  Type a question about pregnancy activity.")
    print("  Type 'quit' to exit.")
    print("  Type 'help' for example queries.")
    print()

    example_queries = [
        "is cycling safe during pregnancy?",
        "what exercises should I avoid in the first trimester?",
        "can I do yoga when pregnant?",
        "how much exercise is recommended during pregnancy?",
        "is swimming good for pregnancy?",
        "what are the dos and don'ts for running while pregnant?",
        "pelvic floor exercises after childbirth",
        "can I exercise while breastfeeding?",
    ]

    while True:
        try:
            query = input("\n  Your question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!")
            break

        if not query:
            continue

        if query.lower() == "quit":
            print("  Goodbye!")
            break

        if query.lower() == "help":
            print("\n  Example queries:")
            for q in example_queries:
                print(f"    - {q}")
            continue

        print()
        result = retriever.retrieve(query)

        # Safety flag
        if result["safety_flag"]:
            print(result["response"])
            continue

        # No results
        if not result["results"]:
            print("  No relevant information found for that query.")
            print("  Try rephrasing or ask about a specific activity.")
            continue

        # Show results
        print(f"  Found {len(result['results'])} relevant chunks:\n")
        for i, r in enumerate(result["results"], 1):
            print(f"  [{i}] Score: {r['score']:.3f} | "
                  f"Activity: {r['activity']:<20} | "
                  f"Section: {r['section']}")
            print(f"       Source: {r['source_file']} (page {r['page']})")
            print(f"       {r['content'][:200]}...")
            print()

        # Show LLM-ready context
        print("\n  " + "-"*50)
        print("  LLM CONTEXT (what will be sent to the LLM):")
        print("  " + "-"*50)
        context = retriever.format_for_llm(result)
        # Show first 800 chars
        print(context[:800] + "..." if len(context) > 800 else context)


def run_single_query(retriever: APFRetriever, query: str):
    """Single query mode."""
    print(f"\n  Query: {query}\n")
    result = retriever.retrieve(query)

    if result["safety_flag"]:
        print(result["response"])
        return

    if not result["results"]:
        print("  No results found.")
        return

    print(f"  Results ({len(result['results'])}):\n")
    for i, r in enumerate(result["results"], 1):
        print(f"  [{i}] {r['score']:.3f} | {r['activity']} | {r['section']}")
        print(f"       {r['content'][:150]}...\n")


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="APF RAG Retrieval Engine")
    parser.add_argument("--query", type=str, help="Single query mode")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("  APF RAG Retrieval Engine — Step 6")
    print("="*60)

    retriever = APFRetriever()

    if args.query:
        run_single_query(retriever, args.query)
    else:
        run_interactive(retriever)


if __name__ == "__main__":
    main()