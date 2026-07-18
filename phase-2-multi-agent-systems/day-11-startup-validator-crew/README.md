# Day 11 — AI Startup Validator Crew

> **Phase 2 — Multi-Agent Orchestration Systems**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

A 6-agent startup validation system. Input your startup idea and receive a complete venture-capital-style analysis. Agents: **Market Researcher** (TAM/SAM/SOM), **Competitor Scout** (existing solutions), **Financial Modeler** (revenue projections), **Risk Analyst** (PESTLE), **Pitch Writer** (investor pitch), and **Go/No-Go Scorer**. Generates a full 20-page startup validation report with investor-ready pitch deck.

## ✨ Key Features

- 6 specialized CrewAI agents with distinct expert roles
- Real market data via live web scraping
- Full financial projection modeling (3-year forecast)
- PESTLE risk framework analysis
- Investor-ready pitch deck generation in PDF
- Final go/no-go investment score with rationale

## 🛠️ Tech Stack

Python · CrewAI · LangChain · OpenAI SDK · FastAPI · HTML · Tailwind CSS · Playwright · ReportLab

## ⚙️ Setup

```bash
cd phase-2-multi-agent-systems/day-11-startup-validator-crew
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
