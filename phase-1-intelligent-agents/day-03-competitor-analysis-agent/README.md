# Day 03 — Real-Time Competitor Intelligence Agent

> **Phase 1 — Intelligent Standalone Agents**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Input your business niche and competitors. The agent autonomously scrapes their websites, LinkedIn, pricing pages, and reviews, then generates a complete competitive intelligence report: SWOT matrix, pricing comparison, feature gaps, and strategic recommendations. Live dashboard with auto-refresh.

## ✨ Key Features

- Autonomous multi-site web scraping
- Automated SWOT analysis generation
- Pricing and feature matrix comparison
- Sentiment analysis from customer reviews
- Strategy recommendation engine

## 🛠️ Tech Stack

Python · LangChain · Playwright · OpenAI SDK · FastAPI · HTML · Tailwind CSS · Chart.js · JavaScript

## 🗂️ Project Structure

```
day-03-competitor-analysis-agent/
├── main.py            # FastAPI app: web UI + WebSocket streaming
├── agent.py           # Scrape competitors → OpenAI SWOT / pricing / strategy
├── requirements.txt
├── .env.example
└── static/
    └── index.html     # Dashboard UI with Chart.js (light theme, navbar/footer)
```

## 🔬 How It Works

1. Enter your **niche** and one or more **competitor URLs** (or click "Load example")
2. The agent scrapes each homepage **in parallel** and tries to find each pricing page
3. OpenAI analyzes the scraped text and returns a **per-competitor SWOT**, a
   **pricing & feature comparison**, **sentiment**, **feature gaps**, and
   **strategic recommendations** for you
4. The dashboard renders SWOT cards, a bar chart (price vs feature scores), a
   radar chart, and a feature-comparison table — with live progress over WebSockets

## ⚙️ Setup

```bash
cd phase-1-intelligent-agents/day-03-competitor-analysis-agent
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # add your OPENAI_API_KEY
uvicorn main:app --reload
```

Then open **http://localhost:8000**, enter your niche + competitor sites, and analyze.

## 🔑 Required API Key

| Key | Where to get it |
|---|---|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |

## 📌 Status

✅ Functional — parallel scraping, SWOT, pricing/feature charts, and live streaming working

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
