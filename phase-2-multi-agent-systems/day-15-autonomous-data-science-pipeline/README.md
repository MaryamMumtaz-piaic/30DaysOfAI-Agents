# Day 15 — Autonomous Data Science Pipeline Agent

> **Phase 2 — Multi-Agent Orchestration Systems**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Upload any raw dataset. A 6-agent pipeline autonomously handles the full ML workflow: **Data Profiler** (EDA + statistics), **Data Cleaner** (nulls, outliers, encoding), **Feature Engineer** (new features + selection), **Model Selector** (trains and compares 5 models), **Hyperparameter Tuner** (Optuna), **Report Generator** (full ML report with charts and model card).

## ✨ Key Features

- End-to-end automated ML pipeline on any CSV
- Automatic EDA with 20+ statistical visualizations
- Multi-model training and comparison leaderboard
- Optuna hyperparameter optimization
- Full PDF ML report with model card generation

## 🛠️ Tech Stack

Python · LangGraph · OpenAI SDK · Scikit-learn · Optuna · Pandas · Streamlit · Matplotlib · Seaborn

## ⚙️ Setup

```bash
cd phase-2-multi-agent-systems/day-15-autonomous-data-science-pipeline
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../../.env.example .env       # add your API keys
streamlit run app.py
```

## 📌 Status

🚧 In development

---

*Built by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
