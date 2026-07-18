# Contributing to 30 Days of AI Agents

First off — thank you for taking the time to contribute! 🎉 This repository is an open-source collection of 30 production-grade AI agent projects, and community contributions are welcome.

---

## 🧭 Ways to Contribute

- 🐛 **Report bugs** — open an issue describing the problem and how to reproduce it
- 💡 **Suggest features or improvements** — open an issue with the `enhancement` label
- 📝 **Improve documentation** — fix typos, clarify setup steps, add examples
- 🔧 **Submit code** — bug fixes, new features, or optimizations for any of the 30 projects

---

## 🚀 Getting Started

1. **Fork** the repository
2. **Clone** your fork:
   ```bash
   git clone https://github.com/<your-username>/30DaysOfAI-Agents.git
   cd 30DaysOfAI-Agents
   ```
3. **Create a branch** for your change:
   ```bash
   git checkout -b feat/day-01-add-pdf-export
   ```
4. **Set up the project** you're working on (each day folder has its own README with setup steps)
5. **Never commit secrets** — copy `.env.example` to `.env` and keep your keys out of git

---

## 🌿 Branch Naming

| Type | Prefix | Example |
|---|---|---|
| Feature | `feat/` | `feat/day-06-add-macd-indicator` |
| Bug fix | `fix/` | `fix/day-04-pdf-parsing-crash` |
| Docs | `docs/` | `docs/update-day-11-readme` |
| Refactor | `refactor/` | `refactor/day-21-vector-store` |

---

## ✅ Commit Messages

Use clear, present-tense messages that explain the *why*:

```
feat(day-03): add sentiment analysis to competitor reviews
fix(day-08): handle empty OCR results gracefully
docs: clarify Docker setup for Phase 3
```

---

## 🔀 Pull Request Process

1. Make sure your code runs and does not break existing functionality
2. Keep PRs focused — one logical change per PR
3. Update the relevant day's `README.md` if behavior changes
4. Do **not** include `.env` files, API keys, or large binaries
5. Open the PR against the `main` branch with a clear description of what and why

A maintainer will review your PR, request changes if needed, and merge once approved.

---

## 📜 Code of Conduct

By participating, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please be respectful and constructive.

---

## 🔒 Security

Found a security vulnerability? **Do not open a public issue.** Please follow the process in [SECURITY.md](SECURITY.md).

---

*Maintained by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
