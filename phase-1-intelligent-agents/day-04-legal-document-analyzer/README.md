# Day 04 — AI Legal Document Analyzer & Risk Auditor

> **Phase 1 — Intelligent Standalone Agents**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Upload any legal document (contract, NDA, terms of service) and the agent performs clause-by-clause analysis, flags high-risk clauses in red, identifies missing standard protections, compares against legal best practices, and generates a full risk assessment report with recommended edits. Built with a PDF viewer + inline annotations UI.

## ✨ Key Features

- Clause-by-clause legal risk scoring (green / yellow / red)
- Overall risk gauge with clause-level breakdown charts
- Missing standard-protection detection
- Recommended redline edits with side-by-side original vs. improved wording
- PDF / TXT upload (drag-and-drop) plus paste-text input
- Live WebSocket progress streaming
- Downloadable PDF audit report

## 🛠️ Tech Stack

Python · OpenAI GPT-4o-mini · pypdf · FastAPI · WebSockets · ReportLab · HTML · Tailwind CSS · Chart.js · JavaScript

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

✅ Complete

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
