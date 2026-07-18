"""Render a legal risk audit into a professional PDF report."""

from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ACCENT = colors.HexColor("#4f46e5")   # indigo-600
INK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")

RISK_INK = {
    "red": colors.HexColor("#991b1b"),
    "yellow": colors.HexColor("#92400e"),
    "green": colors.HexColor("#065f46"),
}
RISK_BG = {
    "red": colors.HexColor("#fef2f2"),
    "yellow": colors.HexColor("#fffbeb"),
    "green": colors.HexColor("#ecfdf5"),
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
        "h3": ParagraphStyle("H3", parent=base["Heading3"], fontSize=11.5,
                             textColor=ACCENT, spaceBefore=8, spaceAfter=3),
        "body": ParagraphStyle("B", parent=base["Normal"], fontSize=10,
                               leading=15, alignment=TA_JUSTIFY, spaceAfter=6),
        "item": ParagraphStyle("I", parent=base["Normal"], fontSize=9.5,
                               leading=14, alignment=TA_LEFT),
        "meta": ParagraphStyle("M", parent=base["Normal"], fontSize=8.5,
                               textColor=MUTED),
        "cell": ParagraphStyle("C", parent=base["Normal"], fontSize=9, leading=12),
        "cellh": ParagraphStyle("CH", parent=base["Normal"], fontSize=9,
                                leading=12, textColor=colors.white),
        "quote": ParagraphStyle("Q", parent=base["Normal"], fontSize=8.5,
                                leading=12, textColor=MUTED,
                                fontName="Helvetica-Oblique"),
    }


def _bar(pct: int, color: colors.Color, width: float = 42 * mm) -> Table:
    pct = max(0, min(100, int(pct or 0)))
    filled = width * pct / 100
    empty = width - filled
    inner = Table([["", ""]], colWidths=[filled or 0.1, empty or 0.1], rowHeights=[6])
    inner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), color),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#e2e8f0")),
        ("BOX", (0, 0), (-1, -1), 0, colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return inner


def _risk_color(score: int) -> colors.Color:
    if score >= 66:
        return colors.HexColor("#dc2626")
    if score >= 33:
        return colors.HexColor("#d97706")
    return colors.HexColor("#16a34a")


def build_pdf(doc_type: str, data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title=f"Legal Risk Audit — {doc_type}",
    )
    st = _styles()
    flow: list = []
    stats = data.get("stats", {}) or {}
    clauses = data.get("clauses", [])

    # Header
    flow.append(Paragraph("Legal Document Risk Audit", st["title"]))
    detected = data.get("doc_type", doc_type) or "Document"
    party = data.get("party_analyzed", "Signing party")
    flow.append(Paragraph(f"{detected}  ·  perspective: {party}", st["subtitle"]))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))

    # Overall risk gauge
    score = int(data.get("overall_risk_score") or 0)
    level = str(data.get("risk_level", "medium")).capitalize()
    flow.append(Paragraph("Overall Risk", st["h2"]))
    gauge = Table(
        [[Paragraph(f"<b>{score}</b>/100 &nbsp; ({level} risk)", st["cell"])],
         [_bar(score, _risk_color(score), width=150 * mm)]],
        colWidths=[150 * mm],
    )
    gauge.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    flow.append(gauge)

    # Stats row
    chips = [
        ("Clauses reviewed", stats.get("clauses_reviewed", 0), "#334155"),
        ("High risk", stats.get("red", 0), "#dc2626"),
        ("Negotiate", stats.get("yellow", 0), "#d97706"),
        ("Standard", stats.get("green", 0), "#16a34a"),
        ("Missing", stats.get("missing", 0), "#7c3aed"),
    ]
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

    # Summary
    if data.get("summary"):
        flow.append(Paragraph("Summary", st["h2"]))
        flow.append(Paragraph(data["summary"], st["body"]))

    # Red flags
    if data.get("red_flags"):
        flow.append(Paragraph("Key Red Flags", st["h2"]))
        flow.append(ListFlowable(
            [ListItem(Paragraph(str(f), st["item"]), leftIndent=8) for f in data["red_flags"]],
            bulletType="bullet", bulletColor=colors.HexColor("#dc2626")))

    # Clause-by-clause table
    if clauses:
        flow.append(Paragraph("Clause-by-Clause Analysis", st["h2"]))
        for c in clauses:
            risk = str(c.get("risk", "green")).lower()
            ink = RISK_INK.get(risk, RISK_INK["green"])
            bg = RISK_BG.get(risk, RISK_BG["green"])
            inner: list = [
                Paragraph(
                    f'<b>{c.get("title","Clause")}</b> &nbsp;'
                    f'<font color="{ink.hexval()}" size="8"><b>[{risk.upper()} '
                    f'· {int(c.get("risk_score") or 0)}/100]</b></font>',
                    st["cell"]),
            ]
            if c.get("excerpt"):
                inner.append(Paragraph(f'“{c["excerpt"]}”', st["quote"]))
            if c.get("issue"):
                inner.append(Paragraph(f'<b>Issue:</b> {c["issue"]}', st["cell"]))
            if c.get("recommendation"):
                inner.append(Paragraph(f'<b>Fix:</b> {c["recommendation"]}', st["cell"]))
            box = Table([[inner]], colWidths=[170 * mm])
            box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("LINEBEFORE", (0, 0), (0, -1), 2.5, ink),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            flow.append(box)
            flow.append(Spacer(1, 4))

    # Missing clauses
    missing = data.get("missing_clauses", [])
    if missing:
        flow.append(Paragraph("Missing Standard Protections", st["h2"]))
        rows = [[Paragraph("<b>Clause</b>", st["cellh"]),
                 Paragraph("<b>Importance</b>", st["cellh"]),
                 Paragraph("<b>Why it matters</b>", st["cellh"])]]
        for m in missing:
            rows.append([
                Paragraph(str(m.get("name", "")), st["cell"]),
                Paragraph(str(m.get("importance", "")).capitalize(), st["cell"]),
                Paragraph(str(m.get("rationale", "")), st["cell"]),
            ])
        tbl = Table(rows, colWidths=[48 * mm, 24 * mm, 98 * mm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f5f3ff")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        flow.append(tbl)

    # Recommended edits
    edits = data.get("recommended_edits", [])
    if edits:
        flow.append(Paragraph("Recommended Redline Edits", st["h2"]))
        for e in edits:
            flow.append(Paragraph(str(e.get("clause", "Edit")), st["h3"]))
            quad = [[
                _edit_cell("Original", e.get("original"), "#991b1b", "#fef2f2", st),
                _edit_cell("Suggested", e.get("improved"), "#065f46", "#ecfdf5", st),
            ]]
            qt = Table(quad, colWidths=[85 * mm, 85 * mm])
            qt.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            flow.append(qt)
            if e.get("rationale"):
                flow.append(Paragraph(f'<b>Rationale:</b> {e["rationale"]}', st["body"]))

    flow.append(Spacer(1, 10))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))
    flow.append(Paragraph(
        "This automated audit is for informational purposes only and is not a "
        "substitute for advice from a licensed attorney.", st["meta"]))

    doc.build(flow)
    return buf.getvalue()


def _edit_cell(title: str, body: str, ink: str, bg: str, st: dict) -> Table:
    head = Paragraph(f'<b><font color="{ink}">{title}</font></b>', st["cell"])
    txt = Paragraph(str(body or "—"), st["cell"])
    t = Table([[head], [txt]], colWidths=[79 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t
