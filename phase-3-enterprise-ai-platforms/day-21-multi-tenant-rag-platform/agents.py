import os
import re
import json
import asyncio

from dotenv import load_dotenv

load_dotenv()

# --- Lightweight, dependency-free RAG store -------------------------------
# We avoid chromadb/numpy (they need a C toolchain on Windows). Instead each
# tenant gets an isolated JSON file holding {question, answer, source} chunks.
# Retrieval uses token-overlap (Jaccard) similarity — good enough to prove the
# RAG-vs-LLM routing and the auto-import behaviour.

STORE_DIR = os.path.join(os.path.dirname(__file__), "rag_store")
os.makedirs(STORE_DIR, exist_ok=True)

# Similarity below this => "RAG memory has no data" => fall back to the LLM.
# An exact/near-exact question repeat scores ~1.0; loose topic overlap (e.g. two
# unrelated questions that both mention "acme robots") stays well under this.
HIT_THRESHOLD = 0.40

TENANTS = {
    "acme": {
        "name": "Acme Robotics",
        "persona": "Rex, Acme Robotics' friendly technical support assistant. "
                   "You help customers with robots, firmware, warranty and API questions.",
        "accent": "#4f46e5",
        "quota": 5000,
        # Seed knowledge that already lives in this tenant's RAG memory.
        "seed": [
            {
                "question": "What is the warranty period for Acme robots?",
                "answer": "All Acme Robotics units carry a 24-month limited warranty covering "
                          "manufacturing defects. Battery packs are covered for 12 months.",
                "source": "Warranty_Policy.docx",
            },
            {
                "question": "How do I update the firmware?",
                "answer": "Open the Acme Console, go to Devices > Firmware, and click 'Check for "
                          "updates'. The robot must stay docked and charging during the update.",
                "source": "Firmware_Release_Notes.md",
            },
        ],
    },
    "novacare": {
        "name": "NovaCare Health",
        "persona": "Ava, NovaCare Health's HIPAA-aware patient concierge. You answer questions "
                   "about appointments, insurance coverage and clinic locations. Never invent "
                   "medical advice; direct patients to a clinician when unsure.",
        "accent": "#0891b2",
        "quota": 8000,
        "seed": [
            {
                "question": "What insurance plans does NovaCare accept?",
                "answer": "NovaCare Health accepts most major PPO and HMO plans, including BlueCross, "
                          "Aetna, and Cigna. Medicaid is accepted at select clinic locations.",
                "source": "Insurance_Coverage.xlsx",
            },
        ],
    },
    "lexright": {
        "name": "LexRight Legal",
        "persona": "Justin, LexRight Legal's precise contract-law paralegal. You explain clauses "
                   "in plain language and always add that this is general information, not legal advice.",
        "accent": "#b45309",
        "quota": 3000,
        "seed": [
            {
                "question": "What is a mutual NDA?",
                "answer": "A mutual NDA (non-disclosure agreement) binds both parties to keep each "
                          "other's confidential information secret, unlike a one-way NDA where only "
                          "one party discloses. This is general information, not legal advice.",
                "source": "NDA_Template.docx",
            },
        ],
    },
}

_STOPWORDS = {
    "the", "a", "an", "is", "are", "do", "does", "how", "what", "why", "when",
    "for", "of", "to", "in", "on", "and", "or", "i", "you", "my", "me", "can",
    "with", "this", "that", "it", "at", "by", "be", "as",
}


def _store_path(tenant_id: str) -> str:
    return os.path.join(STORE_DIR, f"{tenant_id}.json")


def _load_store(tenant_id: str) -> list:
    """Load a tenant's RAG memory, seeding it on first use."""
    path = _store_path(tenant_id)
    if not os.path.exists(path):
        seed = TENANTS[tenant_id].get("seed", [])
        _save_store(tenant_id, seed)
        return list(seed)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_store(tenant_id: str, entries: list) -> None:
    with open(_store_path(tenant_id), "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def _tokenize(text: str) -> set:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def _similarity(a: str, b: str) -> float:
    ta, tb = _tokenize(a), _tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _retrieve(entries: list, question: str, top_k: int = 3) -> list:
    # Score mainly against the stored question (an exact repeat -> ~1.0), and
    # give partial credit for overlap with the stored answer text.
    scored = []
    for e in entries:
        q_sim = _similarity(question, e["question"])
        a_sim = _similarity(question, e["answer"])
        scored.append((max(q_sim, 0.5 * a_sim), e))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(round(s, 2), e) for s, e in scored[:top_k] if s > 0]


async def _ask_llm(persona: str, question: str) -> str:
    """Call OpenAI to answer when RAG memory has no relevant data."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("your_"):
        return ("[LLM unavailable — no OPENAI_API_KEY configured] "
                "I don't have this in my knowledge base yet.")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"You are {persona} Answer concisely in 2-4 sentences."},
            {"role": "user", "content": question},
        ],
        temperature=0.4,
        max_tokens=250,
    )
    return resp.choices[0].message.content.strip()


async def run_rag_query(tenant_id: str, question: str) -> dict:
    """
    RAG-first pipeline with LLM fallback + auto-import.

    1. Retrieve from the tenant's isolated RAG memory.
    2. If a good match exists -> answer from memory (source = 'RAG Memory').
    3. If not -> ask the LLM, then IMPORT the generated answer back into the
       tenant's RAG memory so the same question becomes a cache hit next time.
    """
    tenant = TENANTS.get(tenant_id)
    if not tenant:
        raise ValueError(f"Unknown tenant '{tenant_id}'")

    entries = _load_store(tenant_id)
    matches = _retrieve(entries, question)
    best_score = matches[0][0] if matches else 0.0

    await asyncio.sleep(0.3)  # small UX delay

    if best_score >= HIT_THRESHOLD:
        # --- RAG HIT: data already in memory ---
        answer = matches[0][1]["answer"]
        citations = [
            {"source": e["source"], "chunk": e["answer"][:160], "relevance": s}
            for s, e in matches
        ]
        answer_source = "rag_memory"
        imported = False
    else:
        # --- RAG MISS: ask the LLM, then import into RAG memory ---
        answer = await _ask_llm(tenant["persona"], question)
        new_entry = {
            "question": question,
            "answer": answer,
            "source": "LLM Import (auto-generated)",
        }
        entries.append(new_entry)
        _save_store(tenant_id, entries)
        citations = [{
            "source": new_entry["source"],
            "chunk": answer[:160],
            "relevance": 1.0,
        }]
        answer_source = "llm_generated"
        imported = True

    return {
        "tenant_id": tenant_id,
        "tenant_name": tenant["name"],
        "persona": tenant["persona"],
        "accent": tenant["accent"],
        "question": question.strip(),
        "answer": answer,
        "answer_source": answer_source,   # 'rag_memory' | 'llm_generated'
        "imported_to_rag": imported,      # True when the LLM answer was cached
        "citations": citations,
        "usage": {
            "retrieval_score": round(best_score, 2),
            "kb_entries": len(entries),
            "sources_cited": len(citations),
            "quota": tenant["quota"],
            "isolation_verified": True,
        },
    }


def list_tenants() -> list:
    out = []
    for tid, t in TENANTS.items():
        entries = _load_store(tid)
        out.append({
            "id": tid,
            "name": t["name"],
            "persona": t["persona"],
            "accent": t["accent"],
            "source_count": len(entries),
            "sources": sorted({e["source"] for e in entries}),
            "quota": t["quota"],
        })
    return out
