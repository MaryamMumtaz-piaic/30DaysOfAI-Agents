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

## ⚙️ Setup

```bash
cd phase-1-intelligent-agents/day-03-competitor-analysis-agent
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
