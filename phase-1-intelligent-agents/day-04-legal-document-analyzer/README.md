# Day 04 — AI Legal Document Analyzer & Risk Auditor

> **Phase 1 — Intelligent Standalone Agents**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Upload any legal document (contract, NDA, terms of service) and the agent performs clause-by-clause analysis, flags high-risk clauses in red, identifies missing standard protections, compares against legal best practices, and generates a full risk assessment report with recommended edits. Built with a PDF viewer + inline annotations UI.

## ✨ Key Features

- Clause-by-clause legal risk scoring
- Red/yellow/green risk flagging system
- Missing clause detection
- Recommended contract edits with legal rationale
- Side-by-side original vs. improved document view

## 🛠️ Tech Stack

Python · OpenAI GPT-4o · PyPDF2 · FastAPI · HTML · Tailwind CSS · JavaScript · PDF.js · Pydantic

## ⚙️ Setup

```bash
cd phase-1-intelligent-agents/day-04-legal-document-analyzer
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../../.env.example .env       # add your API keys
uvicorn main:app --reload
```

## 📌 Status

🚧 In development

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
