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

## 🗂️ Project Structure

```
day-01-autonomous-research-agent/
├── main.py            # FastAPI app: web UI, WebSocket streaming, PDF route
├── agent.py           # Research pipeline (decompose → search → scrape → synthesize → score)
├── report.py          # ReportLab PDF generator
├── requirements.txt
├── .env.example
└── static/
    └── index.html     # Tailwind UI with live progress + PDF download
```

## 🔬 How It Works

1. **Decompose** — the topic is split into 4–6 focused sub-queries (OpenAI)
2. **Search** — each sub-query is searched via Tavily; duplicates are removed
3. **Scrape** — the top 10 sources are fetched in parallel (httpx) and cleaned (BeautifulSoup)
4. **Synthesize** — claims, insights, and contradictions are extracted from the corpus
5. **Score** — each claim gets a confidence score based on independent source support
6. **Report** — results stream live to the browser and export as a cited PDF

## ⚙️ Setup

```bash 
cd phase-1-intelligent-agents/day-01-autonomous-research-agent
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # add your OPENAI_API_KEY and TAVILY_API_KEY
uvicorn main:app --reload
```

Then open **http://localhost:8000** and enter a research topic.

## 🔑 Required API Keys

| Key | Where to get it |
|---|---|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `TAVILY_API_KEY` | https://app.tavily.com/ |

## 📌 Status

✅ Functional — end-to-end research, live streaming, and PDF export working

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
