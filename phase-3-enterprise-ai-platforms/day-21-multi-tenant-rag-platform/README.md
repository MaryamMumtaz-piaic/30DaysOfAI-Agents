# Day 21 — Multi-Tenant RAG Enterprise Platform

> **Phase 3 — Enterprise-Grade AI Platforms**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

A production multi-tenant RAG system. Companies sign up, upload private knowledge bases (PDFs, Docx, URLs, Notion), and get a branded AI assistant. Each tenant has isolated vector stores, custom personas, usage quotas, REST API access, and a full admin panel with user management and analytics.

## ✨ Key Features

- Multi-tenant architecture with complete data isolation
- Support for PDF, Word, URLs, Notion, and CSV uploads
- Per-tenant custom AI personas and system prompts
- REST API with JWT auth for external integration
- Usage analytics dashboard (queries, tokens, sources cited)

## 🛠️ Tech Stack

Python · LangChain · Chroma DB · FastAPI · HTML · Tailwind CSS · JavaScript · PostgreSQL · JWT · Docker

## ⚙️ Setup

```bash
cd phase-3-enterprise-ai-platforms/day-21-multi-tenant-rag-platform
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../../.env.example .env       # add your API keys
docker compose up --build
```

## 📌 Status

🚧 In development

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
