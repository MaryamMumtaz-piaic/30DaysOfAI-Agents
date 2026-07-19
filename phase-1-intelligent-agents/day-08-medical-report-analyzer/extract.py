"""Extract content from an uploaded medical report (PDF, image, or text).

PDFs and text files are turned into plain text. Images are base64-encoded as a
data URL so the agent can read them with GPT-4o vision (no Tesseract needed).
"""

from __future__ import annotations

import base64
import io

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")
IMAGE_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
}


def extract(filename: str, raw: bytes) -> dict:
    """Return {'kind': 'text'|'image', 'text': str, 'image_url': str}."""
    name = (filename or "").lower()

    if name.endswith(".pdf"):
        text = _from_pdf(raw)
        return {"kind": "text", "text": text, "image_url": ""}

    if name.endswith(IMAGE_EXTS):
        ext = name[name.rfind("."):]
        mime = IMAGE_MIME.get(ext, "image/png")
        b64 = base64.b64encode(raw).decode("ascii")
        return {"kind": "image", "text": "", "image_url": f"data:{mime};base64,{b64}"}

    # Plain text / markdown.
    return {"kind": "text", "text": raw.decode("utf-8", errors="ignore"), "image_url": ""}


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
