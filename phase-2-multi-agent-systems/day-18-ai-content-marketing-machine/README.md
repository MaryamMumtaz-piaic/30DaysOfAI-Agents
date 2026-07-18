# Day 18 — AI Content Marketing Machine

> **Phase 2 — Multi-Agent Orchestration Systems**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

A fully automated content marketing system. Input brand guidelines and a weekly topic. 6 agents produce: **SEO Keyword Researcher** (intent + competition analysis), **Long-Form Blog Writer** (3,000-word SEO article), **Social Media Adaptor** (LinkedIn, Twitter/X, Instagram variants), **Email Newsletter Writer** (with A/B subject lines), **Meta Ad Copy Generator**, **Analytics Predictor** (projected CTR/reach). Auto-publishing scheduler.

## ✨ Key Features

- SEMrush-level keyword research and intent mapping
- 3,000-word SEO-optimized blog post generation
- Platform-specific social content variants
- Email newsletter with 3 A/B subject line options
- Content calendar generation with one click

## 🛠️ Tech Stack

Python · CrewAI · LangChain · OpenAI SDK · FastAPI · HTML · Tailwind CSS · JavaScript · Celery + Redis

## ⚙️ Setup

```bash
cd phase-2-multi-agent-systems/day-18-ai-content-marketing-machine
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
