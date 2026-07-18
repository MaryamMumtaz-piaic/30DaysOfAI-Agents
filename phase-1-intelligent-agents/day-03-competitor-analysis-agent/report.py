"""Render a competitor-intelligence analysis into a professional PDF report."""

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

ACCENT = colors.HexColor("#0d9488")   # teal-600
INK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")


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
    }


def _bar(pct: int, color: colors.Color, width: float = 42 * mm) -> Table:
    pct = max(0, min(100, int(pct or 0)))
    filled = width * pct / 100
    empty = width - filled
    inner = Table([["", ""]], colWidths=[filled or 0.1, empty or 0.1], rowHeights=[5])
    inner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), color),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#e2e8f0")),
        ("LINEBELOW", (0, 0), (-1, -1), 0, colors.white),
        ("BOX", (0, 0), (-1, -1), 0, colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return inner


def build_pdf(niche: str, data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title=f"Competitor Intelligence — {niche}",
    )
    st = _styles()
    flow: list = []
    comps = data.get("competitors", [])

    # Header
    flow.append(Paragraph("Competitive Intelligence Report", st["title"]))
    flow.append(Paragraph(f"Niche: {niche}", st["subtitle"]))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))

    # Overview
    flow.append(Paragraph("Market Overview", st["h2"]))
    if data.get("overview"):
        flow.append(Paragraph(data["overview"], st["body"]))

    # Scoreboard table (price + feature scores with bars)
    if comps:
        flow.append(Paragraph("Scoreboard", st["h2"]))
        rows = [[
            Paragraph("<b>Competitor</b>", st["cellh"]),
            Paragraph("<b>Price competitiveness</b>", st["cellh"]),
            Paragraph("<b>Feature richness</b>", st["cellh"]),
            Paragraph("<b>Sentiment</b>", st["cellh"]),
        ]]
        for c in comps:
            ps = int(c.get("price_score") or 0)
            fs = int(c.get("feature_score") or 0)
            rows.append([
                Paragraph(str(c.get("name", "")), st["cell"]),
                _score_cell(ps, colors.HexColor("#14b8a6"), st),
                _score_cell(fs, colors.HexColor("#6366f1"), st),
                Paragraph(str(c.get("sentiment", "unknown")), st["cell"]),
            ])
        tbl = Table(rows, colWidths=[38 * mm, 52 * mm, 52 * mm, 26 * mm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f1f5f9")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        flow.append(tbl)

    # Per-competitor SWOT
    for c in comps:
        flow.append(Paragraph(str(c.get("name", "")), st["h3"]))
        if c.get("positioning"):
            flow.append(Paragraph(f"<i>{c['positioning']}</i>", st["meta"]))
            flow.append(Spacer(1, 2))
        swot = c.get("swot", {}) or {}
        quad = [[
            _swot_cell("Strengths", swot.get("strengths"), "#065f46", "#ecfdf5", st),
            _swot_cell("Weaknesses", swot.get("weaknesses"), "#991b1b", "#fef2f2", st),
        ], [
            _swot_cell("Opportunities", swot.get("opportunities"), "#1e40af", "#eff6ff", st),
            _swot_cell("Threats", swot.get("threats"), "#9a3412", "#fff7ed", st),
        ]]
        qt = Table(quad, colWidths=[86 * mm, 86 * mm])
        qt.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        flow.append(qt)
        if c.get("pricing"):
            flow.append(Paragraph(f"<b>Pricing:</b> {c['pricing']}", st["body"]))

    # Feature gaps
    if data.get("gaps"):
        flow.append(Paragraph("Feature Gaps & Opportunities", st["h2"]))
        flow.append(ListFlowable(
            [ListItem(Paragraph(g, st["item"]), leftIndent=8) for g in data["gaps"]],
            bulletType="bullet", bulletColor=ACCENT))

    # Recommendations
    if data.get("recommendations"):
        flow.append(Paragraph("Strategic Recommendations", st["h2"]))
        flow.append(ListFlowable(
            [ListItem(Paragraph(r, st["item"]), leftIndent=8)
             for r in data["recommendations"]],
            bulletType="bullet", bulletColor=colors.HexColor("#16a34a")))

    # Sources
    meta = data.get("competitors_meta", [])
    if meta:
        flow.append(Paragraph("Sources", st["h2"]))
        for i, m in enumerate(meta, 1):
            mark = "scraped" if m.get("scraped") else "not reachable"
            flow.append(Paragraph(
                f'[{i}] {m.get("name","")} — '
                f'<font color="#2563eb">{m.get("url","")}</font> ({mark})',
                st["meta"]))
            flow.append(Spacer(1, 2))

    doc.build(flow)
    return buf.getvalue()


def _score_cell(pct: int, color: colors.Color, st: dict) -> Table:
    label = Paragraph(f"<b>{pct}</b>/100", st["cell"])
    bar = _bar(pct, color)
    t = Table([[label], [bar]], colWidths=[46 * mm])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    return t


def _swot_cell(title: str, items: list, ink: str, bg: str, st: dict) -> Table:
    head = Paragraph(f'<b><font color="{ink}">{title}</font></b>', st["cell"])
    body_items = items or ["—"]
    lst = ListFlowable(
        [ListItem(Paragraph(str(x), st["cell"]), leftIndent=6) for x in body_items],
        bulletType="bullet", bulletColor=colors.HexColor(ink), start="•",
    )
    t = Table([[head], [lst]], colWidths=[80 * mm])
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
