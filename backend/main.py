# -*- coding: utf-8 -*-
"""
backend/main.py
===============
APF Chatbot - FastAPI Backend

Endpoints:
  GET  /api/health     - check if API is running
  POST /api/chat       - ask Nancy a question
  POST /api/screening  - run GAQ-P screening check

Usage:
    uvicorn backend.main:app --reload --port 8000
"""

import sys
import time
import torch
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add scripts to path for imports
sys.path.append(str(Path(__file__).parent.parent / "scripts"))
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
    "chest pain", "chest tightness", "heart pain", "palpitations",
    "shortness of breath", "bleeding", "vaginal bleeding",
    "amniotic fluid", "waters broke", "dizziness", "dizzy", "faint",
    "fainting", "lightheaded", "severe pain", "abdominal pain", "pelvic pain",
    "baby not moving", "no movement", "reduced movement",
    "blurred vision", "severe headache", "high blood pressure",
    "hypertension", "preeclampsia", "gestational diabetes", "diabetes",
    "epilepsy", "seizure", "heart condition", "heart disease", "cardiac",
    "blood clot", "cancer", "tumour", "tumor", "thyroid", "kidney disease",
    "placenta previa", "incompetent cervix", "cerclage", "premature labour",
    "preterm", "twins", "triplets", "miscarriage", "ectopic",
    "fell", "fall", "accident", "injured", "fever", "contractions",
    "labour", "labor", "swollen face", "swollen hands",
]

SAFETY_RESPONSE = (
    "⚠️ Based on what you've described, I'm not able to provide exercise "
    "guidance at this time. Please contact your GP or midwife immediately, "
    "or call NHS 111 for urgent advice. Do not continue or start any physical "
    "activity until you have spoken with your healthcare team."
)

# ── GLOBAL STATE ──────────────────────────────────────────────────────────────
# Models loaded once at startup, reused for all requests

state = {
    "retriever": None,
    "llm"      : None,
    "ready"    : False,
}

# ── STARTUP / SHUTDOWN ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models on startup."""
    print("\n🚀 Starting APF Nancy Backend...")
    print("   Loading RAG components...")

    t0 = time.time()

    # Load retriever
    state["retriever"] = APFRetriever()

    # Load LLM
    print(f"   Loading LLM: {LLM_MODEL}")
    tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        LLM_MODEL,
        torch_dtype=torch.float32,
        device_map="cpu",
    )
    state["llm"] = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=MAX_NEW_TOKENS,
        temperature=TEMPERATURE,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
        return_full_text=False,
    )

    state["ready"] = True
    print(f"   ✅ Backend ready in {time.time()-t0:.1f}s\n")

    yield  # App runs here

    print("   Shutting down...")


# ── APP ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Nancy — APF Pregnancy Activity Chatbot",
    description="RAG-powered pregnancy activity guide by the Active Pregnancy Foundation",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow Streamlit to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── MODELS ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str
    activity_filter: str = None   # optional: filter by activity e.g. "cycling"

class ChatResponse(BaseModel):
    question    : str
    answer      : str
    safety_flag : bool
    sources     : list
    time_seconds: float

class HealthResponse(BaseModel):
    status  : str
    ready   : bool
    model   : str
    chunks  : int

# ── HELPERS ───────────────────────────────────────────────────────────────────

def safety_check(query: str) -> bool:
    q = query.lower()
    return any(kw in q for kw in SAFETY_KEYWORDS)


def build_prompt(question: str, chunks: list) -> str:
    context = "\n\n".join([
        f"[Source {i+1} - {c['activity'].title()} | "
        f"{c['section_label']} | Page {c['page']}]\n{c['content']}"
        for i, c in enumerate(chunks)
    ])
    return (
        f"<|system|>\n{SYSTEM_PROMPT}</s>\n"
        f"<|user|>\nCONTEXT:\n{context}\n\n"
        f"QUESTION: {question}</s>\n"
        f"<|assistant|>\n"
    )


def clean_answer(text: str) -> str:
    for tok in ["</s>", "<|system|>", "<|user|>", "<|assistant|>"]:
        text = text.replace(tok, "")
    return text.strip()


# ── ENDPOINTS ─────────────────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Check if the API is running and ready."""
    chunks = state["retriever"].col.count() if state["retriever"] else 0
    return HealthResponse(
        status = "ready" if state["ready"] else "loading",
        ready  = state["ready"],
        model  = LLM_MODEL,
        chunks = chunks,
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Ask Nancy a question about pregnancy activity.
    Returns answer, sources, and safety flag.
    """
    t0 = time.time()
    question = req.question.strip()

    if not question:
        return ChatResponse(
            question    = question,
            answer      = "Please ask a question about pregnancy activity.",
            safety_flag = False,
            sources     = [],
            time_seconds= 0,
        )

    # ── Safety check ──────────────────────────────────────────────────────────
    if safety_check(question):
        return ChatResponse(
            question    = question,
            answer      = SAFETY_RESPONSE,
            safety_flag = True,
            sources     = [],
            time_seconds= round(time.time() - t0, 2),
        )

    # ── Retrieve ──────────────────────────────────────────────────────────────
    retrieval = state["retriever"].retrieve(
        question,
        top_k           = TOP_K_CHUNKS,
        filter_activity = req.activity_filter,
    )

    if not retrieval["results"]:
        return ChatResponse(
            question    = question,
            answer      = (
                "I don't have specific information about that in my knowledge base. "
                "Please consult your GP or midwife for personalised guidance."
            ),
            safety_flag = False,
            sources     = [],
            time_seconds= round(time.time() - t0, 2),
        )

    # ── Generate ──────────────────────────────────────────────────────────────
    chunks = retrieval["results"]
    prompt = build_prompt(question, chunks)
    output = state["llm"](prompt)
    answer = clean_answer(output[0]["generated_text"])

    # ── Sources ───────────────────────────────────────────────────────────────
    sources = [
        {
            "activity"    : r["activity"],
            "section"     : r["section_label"],
            "source_file" : r["source_file"],
            "page"        : r["page"],
            "score"       : r["score"],
        }
        for r in chunks
    ]

    return ChatResponse(
        question    = question,
        answer      = answer,
        safety_flag = False,
        sources     = sources,
        time_seconds= round(time.time() - t0, 2),
    )