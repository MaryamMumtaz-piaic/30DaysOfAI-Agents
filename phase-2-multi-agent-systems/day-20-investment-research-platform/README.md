# Day 20 — AI Investment Research Platform

> **Phase 2 — Multi-Agent Orchestration Systems**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

A hedge-fund-grade investment research system. Input any stock ticker. 6 agents deliver: **Financial Statement Analyst** (10-K parsing, 30+ ratios), **Market Sentiment Agent** (news + social signals), **Technical Analyst** (chart pattern detection), **Peer Comparison Agent** (sector benchmarking), **DCF Valuation Agent** (fair value calculation), **Investment Thesis Writer** (full buy/hold/sell report). Professional Bloomberg-style terminal UI.

## ✨ Key Features

- SEC 10-K and 10-Q filing automated parsing
- 30+ financial ratio calculations with peer comparison
- Discounted Cash Flow (DCF) valuation model
- Chart pattern recognition (head-and-shoulders, double-top, etc.)
- Full investment thesis with risk-adjusted recommendation

## 🛠️ Tech Stack

Python · CrewAI · OpenAI SDK · yfinance · SEC EDGAR API · FastAPI · HTML · Tailwind CSS · TradingView Charts · JavaScript

## ⚙️ Setup

```bash
cd phase-2-multi-agent-systems/day-20-investment-research-platform
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
