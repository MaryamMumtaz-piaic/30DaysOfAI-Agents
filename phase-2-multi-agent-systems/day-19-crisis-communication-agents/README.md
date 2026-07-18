# Day 19 — AI Crisis Communication & Brand Protection Agent

> **Phase 2 — Multi-Agent Orchestration Systems**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

A 24/7 brand crisis management system. Input your company name. 5 agents continuously monitor: **Social Sentiment Tracker** (Twitter/X, Reddit real-time), **News Alert Agent** (brand mentions across 500+ sources), **Crisis Severity Classifier** (P0-P3 incident levels), **PR Response Drafter** (platform-specific press statements), **Stakeholder Communicator** (email templates for customers, investors, press). Real-time alert dashboard with escalation workflow.

## ✨ Key Features

- Real-time social media and news sentiment monitoring
- Automated P0-P3 crisis severity classification
- Platform-specific PR response generation within 60 seconds
- Multi-stakeholder communication templates
- Full escalation and approval workflow

## 🛠️ Tech Stack

Python · LangGraph · OpenAI SDK · Twitter API · Reddit API · FastAPI · HTML · Tailwind CSS · JavaScript · WebSockets

## ⚙️ Setup

```bash
cd phase-2-multi-agent-systems/day-19-crisis-communication-agents
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
