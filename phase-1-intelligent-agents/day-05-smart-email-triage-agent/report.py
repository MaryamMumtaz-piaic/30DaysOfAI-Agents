"""Render an inbox triage run into a professional PDF report."""

from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ACCENT = colors.HexColor("#7c3aed")   # violet-600
INK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")

CAT_INK = {
    "urgent": colors.HexColor("#991b1b"),
    "important": colors.HexColor("#9a3412"),
    "normal": colors.HexColor("#1e40af"),
    "promotional": colors.HexColor("#3f6212"),
    "spam": colors.HexColor("#334155"),
}
CAT_BG = {
    "urgent": colors.HexColor("#fef2f2"),
    "important": colors.HexColor("#fff7ed"),
    "normal": colors.HexColor("#eff6ff"),
    "promotional": colors.HexColor("#f7fee7"),
    "spam": colors.HexColor("#f1f5f9"),
}


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("T", parent=base["Title"], fontSize=22,
                                 textColor=ACCENT, spaceAfter=4),
        "subtitle": ParagraphStyle("S", parent=base["Normal"], fontSize=10,
                                   textColor=MUTED, spaceAfter=12),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], fontSize=14,
                             textColor=INK, spaceBefore=16, spaceAfter=6),
        "cell": ParagraphStyle("C", parent=base["Normal"], fontSize=9, leading=12),
        "cellh": ParagraphStyle("CH", parent=base["Normal"], fontSize=9,
                                leading=12, textColor=colors.white),
        "reply": ParagraphStyle("R", parent=base["Normal"], fontSize=8.5,
                                leading=12, textColor=colors.HexColor("#334155")),
        "meta": ParagraphStyle("M", parent=base["Normal"], fontSize=8.5,
                               textColor=MUTED),
    }


def build_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title="Inbox Triage Report",
    )
    st = _styles()
    flow: list = []
    emails = data.get("emails", [])
    stats = data.get("stats", {}) or {}
    by_cat = stats.get("by_category", {}) or {}

    flow.append(Paragraph("Inbox Triage Report", st["title"]))
    flow.append(Paragraph(
        f"{stats.get('total', 0)} emails processed  ·  "
        f"{stats.get('action_required', 0)} need action  ·  "
        f"{stats.get('replies_drafted', 0)} replies drafted", st["subtitle"]))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))

    # Category chips
    order = ["urgent", "important", "normal", "promotional", "spam"]
    chips = [(c.capitalize(), by_cat.get(c, 0), CAT_INK[c].hexval()) for c in order]
    chip_row = [[Paragraph(f'<b><font color="{c}">{v}</font></b><br/>'
                           f'<font size="7" color="#64748b">{lbl}</font>', st["cell"])
                 for lbl, v, c in chips]]
    ct = Table(chip_row, colWidths=[34 * mm] * len(chips))
    ct.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    flow.append(Spacer(1, 6))
    flow.append(ct)

    # Priority queue table
    flow.append(Paragraph("Priority Queue", st["h2"]))
    rows = [[Paragraph("<b>#</b>", st["cellh"]),
             Paragraph("<b>Category</b>", st["cellh"]),
             Paragraph("<b>From / Subject</b>", st["cellh"]),
             Paragraph("<b>Summary</b>", st["cellh"]),
             Paragraph("<b>Pri</b>", st["cellh"])]]
    for i, e in enumerate(emails, 1):
        cat = str(e.get("category", "normal")).lower()
        flag = " ★" if e.get("action_required") else ""
        rows.append([
            Paragraph(str(i), st["cell"]),
            Paragraph(f'<font color="{CAT_INK.get(cat, INK).hexval()}"><b>{cat}</b></font>{flag}', st["cell"]),
            Paragraph(f'<b>{_esc(e.get("subject","(no subject)"))}</b><br/>'
                      f'<font size="7" color="#64748b">{_esc(e.get("from",""))}</font>', st["cell"]),
            Paragraph(_esc(e.get("summary", "")), st["cell"]),
            Paragraph(str(e.get("priority", 0)), st["cell"]),
        ])
    tbl = Table(rows, colWidths=[8 * mm, 26 * mm, 58 * mm, 66 * mm, 12 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f3ff")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    flow.append(tbl)

    # Drafted replies
    replies = [e for e in emails if e.get("draft_reply")]
    if replies:
        flow.append(Paragraph("Drafted Replies", st["h2"]))
        for e in replies:
            cat = str(e.get("category", "normal")).lower()
            head = Paragraph(
                f'<b>Re: {_esc(e.get("subject",""))}</b><br/>'
                f'<font size="8" color="#64748b">To: {_esc(e.get("from",""))}</font>', st["cell"])
            body = Paragraph(_esc(e.get("draft_reply", "")).replace("\n", "<br/>"), st["reply"])
            box = Table([[head], [body]], colWidths=[170 * mm])
            box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), CAT_BG.get(cat, colors.HexColor("#f8fafc"))),
                ("LINEBEFORE", (0, 0), (0, -1), 2.5, CAT_INK.get(cat, ACCENT)),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            flow.append(box)
            flow.append(Spacer(1, 5))

    flow.append(Spacer(1, 8))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))
    flow.append(Paragraph(
        "Generated by the Smart Email Triage Agent — review drafts before sending.", st["meta"]))

    doc.build(flow)
    return buf.getvalue()


def _esc(s) -> str:
    return (str(s or "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
