# -*- coding: utf-8 -*-
"""
backend/main.py
===============
APF Nancy Backend — FastAPI + Groq (fast) with TinyLlama fallback (offline)

Usage:
    # With Groq (fast ~2s):
    set GROQ_API_KEY=your_key_here
    uvicorn backend.main:app --reload --port 8000

    # Without Groq (TinyLlama ~40s):
    uvicorn backend.main:app --reload --port 8000
"""

import sys, os, time, torch
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(str(Path(__file__).parent.parent / "scripts"))
from retrieve import APFRetriever

# ── CONFIG ────────────────────────────────────────────────────────────────────
GROQ_API_KEY  = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL    = "llama-3.1-8b-instant"   # fast + free on Groq
TINYLLAMA     = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
MAX_TOKENS    = 400
TEMPERATURE   = 0.3
TOP_K_CHUNKS  = 4

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
    "baby not moving","no movement","reduced movement","blurred vision",
    "severe headache","high blood pressure","hypertension","preeclampsia",
    "gestational diabetes","diabetes","epilepsy","seizure",
    "heart condition","heart disease","cardiac","blood clot","cancer",
    "tumour","tumor","thyroid","kidney disease","placenta previa",
    "incompetent cervix","cerclage","premature labour","preterm",
    "twins","triplets","miscarriage","ectopic","fell","fall",
    "accident","injured","fever","contractions","labour","labor",
    "swollen face","swollen hands",
]

SAFETY_RESPONSE = (
    "⚠️ Based on what you've described, I'm not able to provide exercise guidance at this time. "
    "Please contact your GP or midwife immediately, or call NHS 111 for urgent advice. "
    "Do not continue or start any physical activity until you have spoken with your healthcare team."
)

# ── STATE ─────────────────────────────────────────────────────────────────────
state = {"retriever": None, "llm": None, "provider": None, "ready": False}

# ── STARTUP ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n🚀 Starting APF Nancy Backend...")
    t0 = time.time()

    state["retriever"] = APFRetriever()

    if GROQ_API_KEY:
        try:
            from groq import Groq
            state["llm"]      = Groq(api_key=GROQ_API_KEY)
            state["provider"] = "groq"
            print(f"   ✅ Using Groq ({GROQ_MODEL}) — fast responses ~2s")
        except ImportError:
            print("   ⚠️  groq package not found. Run: pip install groq")
            print("   ↳  Falling back to TinyLlama...")
            state["provider"] = None
    else:
        print("   ℹ️  No GROQ_API_KEY found — using TinyLlama (slower ~40s)")
        print("   ℹ️  Set GROQ_API_KEY env var for faster responses")

    if state["provider"] != "groq":
        print(f"   Loading TinyLlama from cache...")
        from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
        tok   = AutoTokenizer.from_pretrained(TINYLLAMA)
        model = AutoModelForCausalLM.from_pretrained(
            TINYLLAMA, torch_dtype=torch.float32, device_map="cpu")
        state["llm"] = pipeline("text-generation", model=model, tokenizer=tok,
            max_new_tokens=MAX_TOKENS, temperature=TEMPERATURE,
            do_sample=True, pad_token_id=tok.eos_token_id, return_full_text=False)
        state["provider"] = "tinyllama"

    state["ready"] = True
    print(f"   ✅ Backend ready in {time.time()-t0:.1f}s (provider: {state['provider']})\n")
    yield
    print("   Shutting down...")

# ── APP ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Nancy — APF Chatbot", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ── MODELS ────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    question: str
    activity_filter: str = None

class ChatResponse(BaseModel):
    question: str; answer: str; safety_flag: bool
    sources: list; time_seconds: float; provider: str = ""

class HealthResponse(BaseModel):
    status: str; ready: bool; provider: str; chunks: int

# ── HELPERS ───────────────────────────────────────────────────────────────────
def safety_check(q): return any(kw in q.lower() for kw in SAFETY_KEYWORDS)

def build_prompt_groq(question, chunks):
    context = "\n\n".join([
        f"[Source {i+1} - {c['activity'].title()} | {c['section_label']} | Page {c['page']}]\n{c['content']}"
        for i,c in enumerate(chunks)
    ])
    return [
        {"role":"system","content": SYSTEM_PROMPT},
        {"role":"user","content": f"CONTEXT:\n{context}\n\nQUESTION: {question}"}
    ]

def build_prompt_tiny(question, chunks):
    context = "\n\n".join([
        f"[Source {i+1} - {c['activity'].title()} | {c['section_label']} | Page {c['page']}]\n{c['content']}"
        for i,c in enumerate(chunks)
    ])
    return (f"<|system|>\n{SYSTEM_PROMPT}</s>\n"
            f"<|user|>\nCONTEXT:\n{context}\n\nQUESTION: {question}</s>\n"
            f"<|assistant|>\n")

def generate(question, chunks):
    if state["provider"]=="groq":
        msgs = build_prompt_groq(question, chunks)
        resp = state["llm"].chat.completions.create(
            model=GROQ_MODEL, messages=msgs,
            max_tokens=MAX_TOKENS, temperature=TEMPERATURE)
        return resp.choices[0].message.content.strip()
    else:
        prompt = build_prompt_tiny(question, chunks)
        out    = state["llm"](prompt)
        answer = out[0]["generated_text"].strip()
        for tok in ["</s>","<|system|>","<|user|>","<|assistant|>"]:
            answer = answer.replace(tok,"").strip()
        return answer

# ── ENDPOINTS ─────────────────────────────────────────────────────────────────
@app.get("/api/health", response_model=HealthResponse)
async def health():
    chunks = state["retriever"].col.count() if state["retriever"] else 0
    return HealthResponse(status="ready" if state["ready"] else "loading",
                          ready=state["ready"], provider=state["provider"] or "",
                          chunks=chunks)

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    t0       = time.time()
    question = req.question.strip()

    if not question:
        return ChatResponse(question=question,
            answer="Please ask a question about pregnancy activity.",
            safety_flag=False, sources=[], time_seconds=0, provider="")

    if safety_check(question):
        return ChatResponse(question=question, answer=SAFETY_RESPONSE,
            safety_flag=True, sources=[], time_seconds=round(time.time()-t0,2),
            provider="safety_filter")

    retrieval = state["retriever"].retrieve(question, top_k=TOP_K_CHUNKS,
                    filter_activity=req.activity_filter)

    if not retrieval["results"]:
        return ChatResponse(question=question,
            answer="I don't have specific information about that in my knowledge base. "
                   "Please consult your GP or midwife for personalised guidance.",
            safety_flag=False, sources=[], time_seconds=round(time.time()-t0,2),
            provider=state["provider"] or "")

    chunks = retrieval["results"]
    answer = generate(question, chunks)
    sources= [{"activity":r["activity"],"section":r["section_label"],
               "source_file":r["source_file"],"page":r["page"],"score":r["score"]}
              for r in chunks]

    return ChatResponse(question=question, answer=answer, safety_flag=False,
        sources=sources, time_seconds=round(time.time()-t0,2),
        provider=state["provider"] or "")