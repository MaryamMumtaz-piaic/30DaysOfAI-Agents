# Day 27 — AI Learning Management System (LMS)

> **Phase 3 — Enterprise-Grade AI Platforms**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

A complete AI-powered LMS. Upload any course material (PDF, video transcript, slides). The AI generates structured course modules, quizzes per module, personalized learning paths per student based on performance history, detailed wrong-answer explanations, progress analytics, and final certificates. Includes both student and instructor dashboards.

## ✨ Key Features

- Auto-course generation from raw uploaded materials
- Adaptive quiz difficulty based on student performance history
- Personalized learning path per student (knowledge graph)
- Detailed wrong-answer explanations with concept reinforcement
- Analytics: completion rate, time-on-task, knowledge gap heatmap

## 🛠️ Tech Stack

Python · OpenAI SDK · LangChain · FastAPI · HTML · Tailwind CSS · JavaScript · SQLite · Chart.js

## ⚙️ Setup

```bash
cd phase-3-enterprise-ai-platforms/day-27-ai-learning-management-system
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
