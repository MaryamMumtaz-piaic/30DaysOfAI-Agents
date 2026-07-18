# Day 01 — Autonomous Deep Research Agent

> **Phase 1 — Intelligent Standalone Agents**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

An autonomous agent that takes a research topic, spawns sub-queries, scrapes 10+ sources in parallel, cross-validates facts, detects contradictions, and generates a structured 5-page research report with citations, key insights, and a confidence score per claim. Includes a beautiful web UI to input queries and download PDF reports.

## ✨ Key Features

- Parallel multi-source web scraping with BeautifulSoup + Tavily
- Fact cross-validation and contradiction detection
- Auto-generated PDF report with citations
- Confidence scoring per extracted fact
- Real-time progress streaming via WebSockets

## 🛠️ Tech Stack

Python · OpenAI SDK · LangChain · Tavily · BeautifulSoup · FastAPI · HTML · Tailwind CSS · JavaScript · WebSockets · ReportLab

## ⚙️ Setup

```bash
cd phase-1-intelligent-agents/day-01-autonomous-research-agent
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
