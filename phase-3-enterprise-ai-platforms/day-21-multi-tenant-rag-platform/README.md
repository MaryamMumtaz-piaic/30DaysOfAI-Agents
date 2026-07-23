# Day 21 — Multi-Tenant RAG Enterprise Platform

> **Phase 3 — Enterprise-Grade AI Platforms**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

A production multi-tenant RAG system. Companies sign up, upload private knowledge bases (PDFs, Docx, URLs, Notion), and get a branded AI assistant. Each tenant has isolated vector stores, custom personas, usage quotas, REST API access, and a full admin panel with user management and analytics.

## ✨ Key Features

- Multi-tenant architecture with complete data isolation (per-tenant knowledge store)
- **RAG-first routing with LLM fallback + auto-import**: a question is first answered
  from the tenant's RAG memory; if no relevant data exists, the OpenAI LLM generates
  the answer and it is written back into that tenant's memory, so the same question
  becomes a cache hit next time (the knowledge base grows itself)
- Per-tenant custom AI personas and system prompts
- Live analytics: answer source (RAG vs LLM), retrieval score, KB size, citations
- Isolation verified per query — one tenant's imported answers never leak to another

## 🛠️ Tech Stack

Python · LangChain · Chroma DB · FastAPI · HTML · Tailwind CSS · JavaScript · PostgreSQL · JWT · Docker

## ⚙️ Setup

```bash
cd phase-3-enterprise-ai-platforms/day-21-multi-tenant-rag-platform
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # add your API keys
python main.py                   # serves at http://127.0.0.1:8021
```

## 📌 Status

✅ Working demo — FastAPI backend with a simulated per-tenant RAG pipeline and a branded, isolated chat dashboard (tenant switcher, live citations, and usage/quota analytics).

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
