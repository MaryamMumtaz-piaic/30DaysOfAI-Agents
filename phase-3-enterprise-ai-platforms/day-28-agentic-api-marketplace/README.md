# Day 28 — Agentic AI API Marketplace

> **Phase 3 — Enterprise-Grade AI Platforms**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

A marketplace where developers list and sell AI agent APIs. Sellers deploy agents as REST endpoints, buyers discover and test them in a live playground, and the platform handles auth, rate limiting, billing, and usage analytics. Full Stripe integration with revenue sharing. Think RapidAPI built exclusively for AI agents.

## ✨ Key Features

- Agent API listing with documentation auto-generation
- Live API playground for testing before purchasing
- Stripe subscription and usage-based billing
- API key management, rate limiting, and quota enforcement
- Seller revenue analytics and payout dashboard

## 🛠️ Tech Stack

Python · FastAPI · OpenAI SDK · HTML · Tailwind CSS · JavaScript · PostgreSQL · Stripe API · JWT · Docker

## ⚙️ Setup

```bash
cd phase-3-enterprise-ai-platforms/day-28-agentic-api-marketplace
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../../.env.example .env       # add your API keys
docker compose up --build
```

## 📌 Status

🚧 In development

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
