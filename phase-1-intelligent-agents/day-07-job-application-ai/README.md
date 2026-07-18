# Day 07 — AI Job Application Automation Agent

> **Phase 1 — Intelligent Standalone Agents**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Upload your resume and a job description. The agent reverse-engineers the job requirements, rewrites your resume to match ATS keywords, generates a tailored cover letter, prepares 20 likely interview questions with ideal answers, and scores your overall match percentage. Full multi-step UI with PDF export.

## ✨ Key Features

- ATS keyword extraction from job descriptions
- Resume rewriting to maximize ATS score
- Personalized cover letter generation
- Interview Q&A preparation (role-specific)
- Match score with gap analysis and improvement tips

## 🛠️ Tech Stack

Python · OpenAI SDK · PyPDF2 · FastAPI · HTML · Tailwind CSS · JavaScript · jsPDF

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

🚧 In development

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
