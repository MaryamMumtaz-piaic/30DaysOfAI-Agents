"""Render a ResearchResult into a structured, citation-rich PDF report."""

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
)

from agent import ResearchResult


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    accent = colors.HexColor("#7c3aed")
    return {
        "title": ParagraphStyle(
            "T", parent=base["Title"], fontSize=22, textColor=accent, spaceAfter=6
        ),
        "subtitle": ParagraphStyle(
            "S", parent=base["Normal"], fontSize=10,
            textColor=colors.HexColor("#6b7280"), spaceAfter=14,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontSize=14,
            textColor=colors.HexColor("#111827"), spaceBefore=16, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "B", parent=base["Normal"], fontSize=10.5, leading=16,
            alignment=TA_JUSTIFY, spaceAfter=8,
        ),
        "item": ParagraphStyle(
            "I", parent=base["Normal"], fontSize=10.5, leading=15, alignment=TA_LEFT,
        ),
        "meta": ParagraphStyle(
            "M", parent=base["Normal"], fontSize=8.5,
            textColor=colors.HexColor("#6b7280"),
        ),
    }


def _confidence_color(conf: float) -> colors.Color:
    if conf >= 0.75:
        return colors.HexColor("#16a34a")
    if conf >= 0.55:
        return colors.HexColor("#ca8a04")
    return colors.HexColor("#dc2626")


def build_pdf(result: ResearchResult) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"Research Report — {result.topic}",
    )
    st = _styles()
    flow: list = []

    flow.append(Paragraph("Autonomous Research Report", st["title"]))
    flow.append(Paragraph(result.topic, st["subtitle"]))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e5e7eb")))

    # Executive summary
    flow.append(Paragraph("Executive Summary", st["h2"]))
    for para in result.summary.split("\n"):
        if para.strip():
            flow.append(Paragraph(para.strip(), st["body"]))

    # Key insights
    if result.key_insights:
        flow.append(Paragraph("Key Insights", st["h2"]))
        flow.append(
            ListFlowable(
                [ListItem(Paragraph(i, st["item"]), leftIndent=8)
                 for i in result.key_insights],
                bulletType="bullet", bulletColor=colors.HexColor("#7c3aed"),
            )
        )

    # Validated claims with confidence
    if result.claims:
        flow.append(Paragraph("Validated Claims &amp; Confidence", st["h2"]))
        for c in result.claims:
            pct = int(c.confidence * 100)
            col = "#" + _confidence_color(c.confidence).hexval()[2:]
            badge = f'<font color="{col}"><b>[{pct}% confidence]</b></font>'
            flow.append(Paragraph(f"{badge} {c.text}", st["body"]))
            if c.supporting_sources:
                cites = ", ".join(c.supporting_sources)
                flow.append(Paragraph(f"Sources: {cites}", st["meta"]))
            flow.append(Spacer(1, 4))

    # Contradictions
    if result.contradictions:
        flow.append(Paragraph("Detected Contradictions", st["h2"]))
        flow.append(
            ListFlowable(
                [ListItem(Paragraph(x, st["item"]), leftIndent=8)
                 for x in result.contradictions],
                bulletType="bullet", bulletColor=colors.HexColor("#dc2626"),
            )
        )

    # Sources / bibliography
    flow.append(Paragraph("Sources", st["h2"]))
    for i, s in enumerate(result.sources, 1):
        mark = "✓" if s.scraped else "○"
        flow.append(
            Paragraph(
                f"[{i}] {mark} {s.title}<br/>"
                f'<font color="#2563eb">{s.url}</font>',
                st["meta"],
            )
        )
        flow.append(Spacer(1, 3))

    doc.build(flow)
    return buf.getvalue()
