# Day 06 — AI Trading Signal & Portfolio Analyzer Agent

> **Phase 1 — Intelligent Standalone Agents**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

An intelligent financial agent that analyzes real-time stock/crypto data, calculates technical indicators (RSI, MACD, Bollinger Bands), reads market sentiment from financial news, and generates BUY/SELL/HOLD signals with confidence scores. Live candlestick chart UI with real-time updates.

## ✨ Key Features

- Real market data (stocks & crypto) via Yahoo Finance (`yfinance`)
- Technical indicator calculations (RSI, MACD, EMA 20/50/200, Bollinger Bands)
- BUY / SELL / HOLD signals with confidence score, bull/bear case, and rationale
- Portfolio-level risk assessment and diversification advice (multi-symbol)
- Interactive candlestick charts with live WebSocket progress
- Downloadable PDF signals report

## 🛠️ Tech Stack

Python · OpenAI GPT-4o-mini · yfinance · FastAPI · WebSockets · ReportLab · HTML · Tailwind CSS · Chart.js (financial plugin) · JavaScript

> Enter tickers like `AAPL`, `NVDA` or crypto pairs like `BTC-USD`, `ETH-USD`. Add multiple symbols to trigger the portfolio assessment.

## ⚙️ Setup

```bash
cd phase-1-intelligent-agents/day-06-ai-trading-signal-agent
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
