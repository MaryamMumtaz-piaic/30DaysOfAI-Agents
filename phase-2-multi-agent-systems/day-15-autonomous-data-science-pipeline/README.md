# Day 15 — Autonomous Data Science Pipeline Agent

> **Phase 2 — Multi-Agent Orchestration Systems**
> Part of the [30 Days of AI Agents Challenge](../../README.md) by **Maryam Mumtaz**

---

## 📖 Overview

Upload any CSV and pick a target column. A 6-agent pipeline autonomously runs the full ML workflow: **Data Profiler** (EDA, dtypes, missingness, correlations), **Data Cleaner** (dedupe, null imputation, outlier capping, junk-column drop), **Feature Engineer** (encoding, scaling, date-part extraction), **Model Selector** (trains and cross-validates 5 models on a common split), **Hyperparameter Tuner** (GridSearchCV on the leaderboard winner), and **Report Generator** (an LLM narrative + model card written from the real metrics). Classification vs regression is detected automatically, all model work is deterministic scikit-learn, and progress streams live over a WebSocket.

## ✨ Key Features

- End-to-end automated ML pipeline on any CSV — no code required
- Automatic task detection (classification vs regression) from the target
- Real EDA: dtypes, missingness, cardinality, and target correlations
- Multi-model training with a cross-validated leaderboard (5 models)
- GridSearchCV hyperparameter tuning of the winning model
- Model card with held-out test metrics, best params, and feature importances
- Full PDF ML report + live 6-agent progress dashboard

## 🛠️ Tech Stack

Python · OpenAI SDK · Scikit-learn · Pandas · NumPy · FastAPI · WebSockets · HTML · Tailwind CSS · Chart.js · ReportLab

## ⚙️ Setup

```bash
cd phase-2-multi-agent-systems/day-15-autonomous-data-science-pipeline
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
