# Day 06 — AI Trading Signal & Portfolio Analyzer Agent

> **Phase 1 — Intelligent Standalone Agents**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

An intelligent financial agent that analyzes real-time stock/crypto data, calculates technical indicators (RSI, MACD, Bollinger Bands), reads market sentiment from financial news, and generates BUY/SELL/HOLD signals with confidence scores. Live candlestick chart UI with real-time updates.

## ✨ Key Features

- Real-time market data via Yahoo Finance and CoinGecko API
- Technical indicator calculations (RSI, MACD, EMA, Bollinger Bands)
- Financial news sentiment analysis
- BUY/SELL/HOLD signal generation with rationale
- Portfolio risk assessment and diversification advice

## 🛠️ Tech Stack

Python · OpenAI SDK · yfinance · FastAPI · HTML · Tailwind CSS · TradingView Lightweight Charts · JavaScript

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

🚧 In development

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
