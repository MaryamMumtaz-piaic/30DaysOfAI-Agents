# Day 16 — AI Legal Contract Generation & Review System

> **Phase 2 — Multi-Agent Orchestration Systems**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

A 4-agent legal platform. Generate any contract type (NDA, SLA, employment, vendor agreement, partnership) or upload existing ones. Agents: **Contract Drafter** (jurisdiction-aware legal language), **Risk Reviewer** (clause risk scoring 1-10), **Negotiation Advisor** (strategic compromise suggestions), **Plain Language Translator** (jargon-free summaries for non-lawyers). Export as signed-ready PDF.

## ✨ Key Features

- 20+ contract type templates with jurisdiction options
- Clause-level risk scoring with color-coded highlights
- Negotiation strategy generation per risky clause
- Dual-view: legal language vs. plain English
- Digital signature-ready PDF export

## 🛠️ Tech Stack

Python · CrewAI · OpenAI GPT-4o · FastAPI · HTML · Tailwind CSS · JavaScript · PDF.js · ReportLab

## ⚙️ Setup

```bash
cd phase-2-multi-agent-systems/day-16-ai-legal-contract-system
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
