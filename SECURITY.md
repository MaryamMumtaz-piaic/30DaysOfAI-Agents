# Security Policy

## Supported Versions

This repository is an active, in-progress learning and portfolio project. Security fixes are applied to the latest state of the `main` branch.

| Version | Supported |
|---|---|
| `main` (latest) | ✅ |
| Older commits | ❌ |

## Reporting a Vulnerability

If you discover a security vulnerability in any of the 30 projects, **please do not open a public GitHub issue.** Public disclosure before a fix is available can put users at risk.

Instead, report it privately:

- 📧 **Email:** maryamqureshimumtazm.a@gmail.com
- Use a subject line starting with `[SECURITY]`

Please include:

1. A description of the vulnerability and its potential impact
2. The affected project (e.g., `day-09-ai-cybersecurity-audit`)
3. Step-by-step instructions to reproduce
4. Any proof-of-concept code, logs, or screenshots
5. Suggested remediation, if you have one

## What to Expect

- **Acknowledgement** within 72 hours of your report
- An initial assessment and severity classification
- Regular updates on remediation progress
- Public credit for the discovery once the issue is resolved (unless you prefer to remain anonymous)

## Scope

Because these projects integrate with external APIs and handle user input, the following are especially in scope:

- Exposed API keys, secrets, or credentials committed to the repo
- Injection vulnerabilities (SQL, command, prompt injection)
- Authentication and authorization flaws (JWT, OAuth, RBAC)
- Insecure file upload handling
- Cross-site scripting (XSS) and CSRF in the web UIs

## Best Practices for Users

- **Never commit your `.env` file** — it is git-ignored by default
- Rotate any API key that may have been exposed
- Keep dependencies up to date (`pip install -U -r requirements.txt`)
- Run projects in isolated environments when handling sensitive data

---

*Maintained by Maryam Mumtaz — AI Engineer & Founder, Marsa Empower*
