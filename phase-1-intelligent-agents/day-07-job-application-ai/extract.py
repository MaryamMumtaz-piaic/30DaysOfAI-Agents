"""Extract plain text from an uploaded resume (PDF or text)."""

from __future__ import annotations

import io


def extract_text(filename: str, raw: bytes) -> str:
    """Return the document's text. Supports .pdf, .txt, and .md."""
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        return _from_pdf(raw)
    return raw.decode("utf-8", errors="ignore")


def _from_pdf(raw: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(raw))
    parts: list[str] = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            continue
    text = "\n".join(parts)
    return " ".join(text.split())
