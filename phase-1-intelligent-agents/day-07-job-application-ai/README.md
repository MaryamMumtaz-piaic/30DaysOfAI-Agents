# Day 07 — AI Job Application Automation Agent

> **Phase 1 — Intelligent Standalone Agents**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Upload your resume and a job description. The agent reverse-engineers the job requirements, rewrites your resume to match ATS keywords, generates a tailored cover letter, prepares 20 likely interview questions with ideal answers, and scores your overall match percentage. Full multi-step UI with PDF export.

## ✨ Key Features

- Reverse-engineers the job into ATS keywords, responsibilities & soft skills
- Match score with matched/missing keywords, strengths, and gap analysis
- Resume rewrite (summary, prioritized skills, achievement bullets) — no fabrication
- Personalized cover letter with one-click copy
- Role-specific interview Q&A prep (5–25 questions) with sample answers & tips
- Resume PDF/TXT upload plus paste-in; downloadable full-package PDF

## 🛠️ Tech Stack

Python · OpenAI GPT-4o-mini · pypdf · FastAPI · WebSockets · ReportLab · HTML · Tailwind CSS · Chart.js · JavaScript

## ⚙️ Setup

```bash
cd phase-1-intelligent-agents/day-07-job-application-ai
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
