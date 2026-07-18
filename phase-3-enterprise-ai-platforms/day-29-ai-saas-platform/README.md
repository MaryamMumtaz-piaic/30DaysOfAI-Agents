# Day 29 — Full AI SaaS Platform (Multi-Feature)

> **Phase 3 — Enterprise-Grade AI Platforms**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

A production-ready AI SaaS with full auth (register/login/Google OAuth), three subscription tiers (Free/Pro/Enterprise with feature gating), and 10 specialized AI tools: AI Writer, Image Analyzer, Code Reviewer, Document Summarizer, SEO Analyzer, Resume Builder, Email Drafter, Data Analyzer, Chat Agent, and API Generator. Complete billing, user management, and admin panel with revenue analytics.

## ✨ Key Features

- Full auth system with Google and GitHub OAuth
- 3-tier subscription with Stripe billing and webhook handling
- 10 production-grade AI tools with tier-based access
- Admin panel with user management and MRR analytics
- Token usage tracking and quota enforcement per user

## 🛠️ Tech Stack

Python · OpenAI SDK · LangChain · FastAPI · HTML · Tailwind CSS · JavaScript · PostgreSQL · Stripe · OAuth2 · Docker

## ⚙️ Setup

```bash
cd phase-3-enterprise-ai-platforms/day-29-ai-saas-platform
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
