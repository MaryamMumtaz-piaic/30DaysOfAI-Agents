"""Deterministic security checks that don't need an LLM.

- HTTP security-header analysis for a live URL.
- Regex-based detection of exposed secrets / API keys in source code.

These findings are combined with the LLM's OWASP analysis in agent.py.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

# --- HTTP security headers we expect a hardened site to send ---------------

SECURITY_HEADERS = {
    "strict-transport-security": {
        "title": "HTTP Strict Transport Security (HSTS)",
        "severity": "high",
        "why": "Without HSTS, browsers may connect over plain HTTP, exposing traffic to downgrade/MITM attacks.",
        "fix": "Add 'Strict-Transport-Security: max-age=63072000; includeSubDomains; preload'.",
    },
    "content-security-policy": {
        "title": "Content Security Policy (CSP)",
        "severity": "high",
        "why": "A missing CSP makes cross-site scripting (XSS) far easier to exploit.",
        "fix": "Define a restrictive Content-Security-Policy limiting script/style/connect sources.",
    },
    "x-frame-options": {
        "title": "X-Frame-Options",
        "severity": "medium",
        "why": "Without it the page can be framed by attackers, enabling clickjacking.",
        "fix": "Send 'X-Frame-Options: DENY' (or use CSP frame-ancestors).",
    },
    "x-content-type-options": {
        "title": "X-Content-Type-Options",
        "severity": "medium",
        "why": "Missing nosniff lets browsers MIME-sniff responses, enabling some XSS vectors.",
        "fix": "Send 'X-Content-Type-Options: nosniff'.",
    },
    "referrer-policy": {
        "title": "Referrer-Policy",
        "severity": "low",
        "why": "Without a referrer policy, full URLs (possibly with tokens) can leak to third parties.",
        "fix": "Send 'Referrer-Policy: strict-origin-when-cross-origin'.",
    },
    "permissions-policy": {
        "title": "Permissions-Policy",
        "severity": "low",
        "why": "No permissions policy means powerful browser features aren't restricted.",
        "fix": "Send a 'Permissions-Policy' disabling unused features (camera, geolocation, etc.).",
    },
}

# Headers that leak stack details and should be removed/obscured.
INFO_LEAK_HEADERS = ("server", "x-powered-by", "x-aspnet-version", "x-aspnetmvc-version")


# --- Secret patterns -------------------------------------------------------

SECRET_PATTERNS: list[tuple[str, str]] = [
    ("AWS Access Key ID", r"AKIA[0-9A-Z]{16}"),
    ("AWS Secret Access Key", r"(?i)aws_secret_access_key\s*[=:]\s*['\"]?[A-Za-z0-9/+=]{40}"),
    ("Google API Key", r"AIza[0-9A-Za-z\-_]{35}"),
    ("OpenAI API Key", r"sk-[A-Za-z0-9]{20,}"),
    ("Anthropic API Key", r"sk-ant-[A-Za-z0-9\-_]{20,}"),
    ("GitHub Token", r"gh[pousr]_[A-Za-z0-9]{36,}"),
    ("Slack Token", r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    ("Stripe Secret Key", r"sk_live_[0-9a-zA-Z]{24,}"),
    ("Private Key Block", r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
    ("JWT", r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ("Generic Secret Assignment",
     r"(?i)(?:password|passwd|pwd|secret|api[_-]?key|token|access[_-]?key)\s*[=:]\s*['\"][^'\"\s]{6,}['\"]"),
    ("Hardcoded Connection String",
     r"(?i)(?:mongodb(?:\+srv)?|postgres(?:ql)?|mysql|redis)://[^\s'\"]+:[^\s'\"]+@"),
]


def normalize_url(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    return raw


def scan_headers(url: str) -> dict:
    """Fetch the URL and evaluate its transport + header security posture.

    Returns {'url','final_url','status','https','findings':[...],'present':{...}}.
    """
    import httpx

    findings: list[dict] = []
    headers_seen: dict[str, str] = {}

    try:
        with httpx.Client(
            timeout=15, follow_redirects=True,
            headers={"User-Agent": "SecurityAuditAgent/1.0 (defensive scan)"},
        ) as client:
            resp = client.get(url)
    except Exception as exc:
        raise RuntimeError(f"Could not reach {url}: {exc}") from exc

    headers_seen = {k.lower(): v for k, v in resp.headers.items()}
    final_url = str(resp.url)
    is_https = urlparse(final_url).scheme == "https"

    if not is_https:
        findings.append({
            "title": "Site not served over HTTPS",
            "severity": "critical",
            "category": "Transport Security",
            "detail": f"The final URL is {final_url}. Traffic is unencrypted.",
            "fix": "Serve all traffic over HTTPS and redirect HTTP to HTTPS.",
        })

    # Missing security headers.
    for key, meta in SECURITY_HEADERS.items():
        if key not in headers_seen:
            # HSTS only meaningful over HTTPS.
            if key == "strict-transport-security" and not is_https:
                continue
            findings.append({
                "title": f"Missing header: {meta['title']}",
                "severity": meta["severity"],
                "category": "HTTP Headers",
                "detail": meta["why"],
                "fix": meta["fix"],
            })

    # Info-leak headers present.
    for key in INFO_LEAK_HEADERS:
        if key in headers_seen and headers_seen[key].strip():
            findings.append({
                "title": f"Information disclosure header: {key}",
                "severity": "low",
                "category": "Information Disclosure",
                "detail": f"'{key}: {headers_seen[key]}' reveals server/stack details useful to attackers.",
                "fix": f"Remove or obfuscate the '{key}' response header.",
            })

    # Insecure cookies.
    for raw_cookie in resp.headers.get_list("set-cookie") if hasattr(resp.headers, "get_list") else []:
        low = raw_cookie.lower()
        name = raw_cookie.split("=", 1)[0].strip()
        missing = [flag for flag in ("secure", "httponly") if flag not in low]
        if missing:
            findings.append({
                "title": f"Cookie '{name}' missing {', '.join(missing)} flag(s)",
                "severity": "medium",
                "category": "Session Security",
                "detail": "Cookies without Secure/HttpOnly can be stolen via XSS or sent over HTTP.",
                "fix": "Set the Secure and HttpOnly flags (and SameSite) on session cookies.",
            })

    present = {k: (k in headers_seen) for k in SECURITY_HEADERS}
    return {
        "url": url,
        "final_url": final_url,
        "status": resp.status_code,
        "https": is_https,
        "findings": findings,
        "present": present,
    }


def scan_secrets(code: str) -> list[dict]:
    """Regex-scan source code for exposed secrets. Returns finding dicts."""
    findings: list[dict] = []
    lines = code.splitlines()
    seen: set[tuple[str, int]] = set()

    for label, pattern in SECRET_PATTERNS:
        for m in re.finditer(pattern, code):
            line_no = code.count("\n", 0, m.start()) + 1
            key = (label, line_no)
            if key in seen:
                continue
            seen.add(key)
            snippet = lines[line_no - 1].strip() if line_no - 1 < len(lines) else m.group(0)
            findings.append({
                "title": f"Exposed secret: {label}",
                "severity": "critical",
                "category": "Exposed Secrets",
                "detail": f"Line {line_no}: {_redact(snippet)}",
                "line": line_no,
                "fix": "Remove the secret from source, rotate it immediately, and load it from an "
                       "environment variable or secrets manager.",
            })
    return findings


def _redact(text: str, keep: int = 4) -> str:
    """Mask long tokens so the report never re-exposes the full secret."""
    def mask(m: re.Match) -> str:
        tok = m.group(0)
        return tok[:keep] + "…" + tok[-2:] if len(tok) > keep + 6 else "***"

    text = text[:200]
    return re.sub(r"[A-Za-z0-9/+=_\-]{12,}", mask, text)
