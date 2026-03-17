# -*- coding: utf-8 -*-
import sys, time, torch
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from retrieve import APFRetriever
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# ── CONFIG ────────────────────────────────────────────────────────────────────
LLM_MODEL      = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
MAX_NEW_TOKENS = 400
TEMPERATURE    = 0.3
TOP_K_CHUNKS   = 4

SYSTEM_PROMPT = """You are Nancy, a helpful pregnancy activity guide from the Active Pregnancy Foundation (APF).
Answer questions about physical activity during pregnancy using ONLY the provided context.
Be warm, supportive and concise (3-5 sentences).
Always recommend consulting a GP or midwife for medical decisions.
If the context does not contain the answer, say: I don't have specific information about that. Please consult your GP or midwife."""

SAFETY_KEYWORDS = [
    "chest pain","chest tightness","heart pain","palpitations",
    "shortness of breath","bleeding","vaginal bleeding",
    "amniotic fluid","waters broke","dizziness","dizzy","faint",
    "fainting","lightheaded","severe pain","abdominal pain","pelvic pain",
    "baby not moving","no movement","reduced movement",
    "blurred vision","severe headache","high blood pressure",
    "hypertension","preeclampsia","gestational diabetes","diabetes",
    "epilepsy","seizure","heart condition","heart disease","cardiac",
    "blood clot","cancer","tumour","tumor","thyroid","kidney disease",
    "placenta previa","incompetent cervix","cerclage","premature labour",
    "preterm","twins","triplets","miscarriage","ectopic",
    "fell","fall","accident","injured","fever","contractions",
    "labour","labor","swollen face","swollen hands",
]

SAFETY_RESPONSE = """
⚠️  SAFETY ALERT — Please consult a healthcare professional

Based on what you've described, I'm not able to provide
exercise guidance at this time.

Please contact:
  - Your GP or midwife immediately
  - NHS 111 for urgent advice
  - 999 in an emergency

www.activepregnancyfoundation.org
"""

# ── SAFETY CHECK ──────────────────────────────────────────────────────────────
def safety_check(query):
    q = query.lower()
    return any(kw in q for kw in SAFETY_KEYWORDS)

# ── LOAD LLM ──────────────────────────────────────────────────────────────────
def load_llm():
    print(f"  Loading LLM: {LLM_MODEL}")
    print(f"  First run downloads ~600MB, then cached forever...")
    t0 = time.time()

    tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        LLM_MODEL,
        torch_dtype=torch.float32,
        device_map="cpu",
    )
    llm = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=MAX_NEW_TOKENS,
        temperature=TEMPERATURE,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
        return_full_text=False,
    )
    print(f"  LLM loaded in {time.time()-t0:.1f}s ✅\n")
    return llm

# ── BUILD PROMPT ──────────────────────────────────────────────────────────────
def build_prompt(question, chunks):
    context = "\n\n".join([
        f"[Source {i+1} - {c['activity'].title()} | {c['section_label']} | Page {c['page']}]\n{c['content']}"
        for i, c in enumerate(chunks)
    ])
    # TinyLlama chat format
    return (
        f"<|system|>\n{SYSTEM_PROMPT}</s>\n"
        f"<|user|>\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {question}</s>\n"
        f"<|assistant|>\n"
    )

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print("  Nancy — APF Pregnancy Activity Guide")
    print("  Powered by TinyLlama + ChromaDB RAG")
    print("="*60)

    print("\n  Loading components...")
    retriever = APFRetriever()
    llm = load_llm()

    print("="*60)
    print("  Nancy is ready! Ask about pregnancy activity.")
    print("  Type 'quit' to exit.")
    print("="*60 + "\n")

    while True:
        try:
            question = input("  Your question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!")
            break

        if not question:
            continue
        if question.lower() == "quit":
            print("  Goodbye!")
            break

        # Safety check
        if safety_check(question):
            print(SAFETY_RESPONSE)
            continue

        # Retrieve from ChromaDB
        retrieval = retriever.retrieve(question, top_k=TOP_K_CHUNKS)
        if not retrieval["results"]:
            print("\n  I don't have specific information about that.")
            print("  Please consult your GP or midwife.\n")
            continue

        # Generate answer
        print("  Generating answer...", end=" ", flush=True)
        t0 = time.time()
        prompt = build_prompt(question, retrieval["results"])
        output = llm(prompt)
        answer = output[0]["generated_text"].strip()
        # Clean special tokens
        for tok in ["</s>", "<|system|>", "<|user|>", "<|assistant|>"]:
            answer = answer.replace(tok, "").strip()
        elapsed = round(time.time() - t0, 1)
        print(f"done in {elapsed}s\n")

        # Print answer
        print("="*60)
        print(f"  Q: {question}")
        print("="*60)
        print(f"\n  Nancy says:\n")
        # Word wrap
        words = answer.split()
        line = "  "
        for word in words:
            if len(line) + len(word) > 72:
                print(line)
                line = "  " + word + " "
            else:
                line += word + " "
        if line.strip():
            print(line)

        # Sources
        print(f"\n  Sources:")
        for r in retrieval["results"]:
            print(f"    - {r['source_file']} (p{r['page']}) | {r['section']} | score: {r['score']}")
        print()

if __name__ == "__main__":
    main()