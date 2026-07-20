"""Real Gmail connectivity via IMAP (read) and SMTP (send).

Uses a Gmail *App Password* (not the normal account password). To create one:
  1. Enable 2-Step Verification on the Google account.
  2. Go to https://myaccount.google.com/apppasswords and generate a 16-char password.

Credentials are supplied by the user at runtime and are never persisted to disk.
"""

from __future__ import annotations

import email
import imaplib
import smtplib
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import parseaddr

IMAP_HOST = "imap.gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

MAX_BODY_CHARS = 8000


class GmailError(Exception):
    """Raised for connection / auth / fetch / send failures with a friendly message."""


def _decode(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _extract_body(msg: email.message.Message) -> str:
    """Prefer a plain-text part; fall back to stripped HTML."""
    plain, html = "", ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get("Content-Disposition", "").startswith("attachment"):
                continue
            ctype = part.get_content_type()
            try:
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                charset = part.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
            except Exception:
                continue
            if ctype == "text/plain" and not plain:
                plain = text
            elif ctype == "text/html" and not html:
                html = text
    else:
        try:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or "utf-8"
            plain = payload.decode(charset, errors="replace") if payload else ""
        except Exception:
            plain = ""

    body = plain or _strip_html(html)
    return body.strip()[:MAX_BODY_CHARS]


def _strip_html(html: str) -> str:
    import re

    if not html:
        return ""
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n\s*\n\s*\n+", "\n\n", text).strip()


def fetch_unread(user: str, password: str, limit: int = 15) -> list[dict]:
    """Fetch the most recent UNSEEN messages without marking them as read."""
    try:
        imap = imaplib.IMAP4_SSL(IMAP_HOST)
    except Exception as exc:
        raise GmailError(f"Could not reach Gmail IMAP server: {exc}") from exc

    try:
        try:
            imap.login(user, password)
        except imaplib.IMAP4.error as exc:
            raise GmailError(
                "Login failed. Make sure you're using a Gmail App Password "
                "(16 chars, no spaces) and that 2-Step Verification is on."
            ) from exc

        imap.select("INBOX")
        status, data = imap.search(None, "UNSEEN")
        if status != "OK":
            raise GmailError("Could not search the inbox.")

        ids = data[0].split()
        if not ids:
            return []

        ids = ids[-limit:][::-1]  # newest first, capped
        emails: list[dict] = []
        for num in ids:
            # BODY.PEEK does not set the \Seen flag.
            status, msg_data = imap.fetch(num, "(BODY.PEEK[])")
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            emails.append(
                {
                    "id": num.decode() if isinstance(num, bytes) else str(num),
                    "from": _decode(msg.get("From")),
                    "subject": _decode(msg.get("Subject")),
                    "received": _decode(msg.get("Date")),
                    "body": _extract_body(msg),
                    "message_id": msg.get("Message-ID", ""),
                }
            )
        return emails
    finally:
        try:
            imap.logout()
        except Exception:
            pass


def send_reply(
    user: str,
    password: str,
    to: str,
    subject: str,
    body: str,
    in_reply_to: str = "",
) -> None:
    """Send a plain-text reply from the connected account via Gmail SMTP."""
    recipient = parseaddr(to)[1] or to
    if not recipient:
        raise GmailError("No recipient address to send to.")

    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = recipient
    msg["Subject"] = subject or "(no subject)"
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
    except smtplib.SMTPAuthenticationError as exc:
        raise GmailError(
            "SMTP login failed — check your App Password."
        ) from exc
    except Exception as exc:
        raise GmailError(f"Could not send the reply: {exc}") from exc
