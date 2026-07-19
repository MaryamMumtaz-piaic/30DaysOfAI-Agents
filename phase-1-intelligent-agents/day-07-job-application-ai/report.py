"""Render a job-application package into a professional PDF report."""

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
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ACCENT = colors.HexColor("#7c3aed")   # violet-600
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
        "cell": ParagraphStyle("C", parent=base["Normal"], fontSize=9, leading=12),
        "qa": ParagraphStyle("QA", parent=base["Normal"], fontSize=9.5, leading=14,
                             alignment=TA_LEFT, spaceAfter=2),
        "meta": ParagraphStyle("M", parent=base["Normal"], fontSize=8.5, textColor=MUTED),
    }


def _bar(pct: int, color: colors.Color, width: float = 150 * mm) -> Table:
    pct = max(0, min(100, int(pct or 0)))
    filled = width * pct / 100
    empty = width - filled
    inner = Table([["", ""]], colWidths=[filled or 0.1, empty or 0.1], rowHeights=[7])
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


def _chips(items: list, ink: str, bg: str, st: dict) -> Table | Paragraph:
    items = [str(x) for x in (items or []) if x]
    if not items:
        return Paragraph("—", st["meta"])
    cells = [Paragraph(f'<font color="{ink}">{x}</font>', st["cell"]) for x in items]
    # 3 chips per row.
    rows = [cells[i:i + 3] for i in range(0, len(cells), 3)]
    for r in rows:
        while len(r) < 3:
            r.append(Paragraph("", st["cell"]))
    t = Table(rows, colWidths=[56 * mm] * 3)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
        ("GRID", (0, 0), (-1, -1), 3, colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def build_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title="Job Application Package",
    )
    st = _styles()
    flow: list = []
    jd = data.get("job", {}) or {}
    match = data.get("match", {}) or {}
    rewrite = data.get("resume_rewrite", {}) or {}
    cover = data.get("cover_letter", {}) or {}
    interview = data.get("interview", []) or []

    # Header
    flow.append(Paragraph("Job Application Package", st["title"]))
    role = jd.get("title", "the role")
    company = jd.get("company", "")
    flow.append(Paragraph(f"{role}{(' · ' + company) if company else ''}", st["subtitle"]))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))

    # Match score
    score = int(match.get("match_score") or 0)
    color = colors.HexColor("#16a34a") if score >= 70 else colors.HexColor("#d97706") if score >= 45 else colors.HexColor("#dc2626")
    flow.append(Paragraph("Match Score", st["h2"]))
    gauge = Table(
        [[Paragraph(f'<b>{score}%</b> — {match.get("verdict","")}', st["cell"])],
         [_bar(score, color)]],
        colWidths=[150 * mm])
    gauge.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    flow.append(gauge)

    if match.get("strengths"):
        flow.append(Paragraph("Strengths", st["h3"]))
        flow.append(ListFlowable(
            [ListItem(Paragraph(s, st["item"]), leftIndent=8) for s in match["strengths"]],
            bulletType="bullet", bulletColor=colors.HexColor("#16a34a")))

    if match.get("missing_keywords"):
        flow.append(Paragraph("Missing Keywords", st["h3"]))
        flow.append(_chips(match["missing_keywords"], "#991b1b", "#fef2f2", st))

    if match.get("gaps"):
        flow.append(Paragraph("Gap Analysis", st["h3"]))
        for g in match["gaps"]:
            flow.append(Paragraph(
                f'<b>{g.get("gap","")}</b> — {g.get("fix","")}', st["item"]))
            flow.append(Spacer(1, 2))

    if match.get("ats_tips"):
        flow.append(Paragraph("ATS Tips", st["h3"]))
        flow.append(ListFlowable(
            [ListItem(Paragraph(t, st["item"]), leftIndent=8) for t in match["ats_tips"]],
            bulletType="bullet", bulletColor=ACCENT))

    # Rewritten resume
    flow.append(PageBreak())
    flow.append(Paragraph("Optimized Resume", st["h2"]))
    if rewrite.get("professional_summary"):
        flow.append(Paragraph("Professional Summary", st["h3"]))
        flow.append(Paragraph(rewrite["professional_summary"], st["body"]))
    if rewrite.get("skills"):
        flow.append(Paragraph("Prioritized Skills", st["h3"]))
        flow.append(_chips(rewrite["skills"], "#3730a3", "#eef2ff", st))
    if rewrite.get("experience_bullets"):
        flow.append(Paragraph("Experience (rewritten)", st["h3"]))
        flow.append(ListFlowable(
            [ListItem(Paragraph(b, st["item"]), leftIndent=8) for b in rewrite["experience_bullets"]],
            bulletType="bullet", bulletColor=ACCENT))
    if rewrite.get("keywords_added"):
        flow.append(Paragraph("Keywords Surfaced", st["h3"]))
        flow.append(_chips(rewrite["keywords_added"], "#065f46", "#ecfdf5", st))

    # Cover letter
    flow.append(PageBreak())
    flow.append(Paragraph("Cover Letter", st["h2"]))
    if cover.get("greeting"):
        flow.append(Paragraph(cover["greeting"], st["body"]))
    for para in str(cover.get("body", "")).split("\n\n"):
        if para.strip():
            flow.append(Paragraph(para.strip().replace("\n", "<br/>"), st["body"]))
    if cover.get("closing"):
        flow.append(Paragraph(str(cover["closing"]).replace("\n", "<br/>"), st["body"]))

    # Interview prep
    if interview:
        flow.append(PageBreak())
        flow.append(Paragraph(f"Interview Preparation ({len(interview)} questions)", st["h2"]))
        for i, q in enumerate(interview, 1):
            flow.append(Paragraph(
                f'<b>{i}. {q.get("question","")}</b> '
                f'<font size="8" color="#7c3aed">[{q.get("category","")}]</font>', st["qa"]))
            if q.get("ideal_answer"):
                flow.append(Paragraph(f'<i>{q["ideal_answer"]}</i>', st["qa"]))
            if q.get("tip"):
                flow.append(Paragraph(f'<font color="#64748b" size="8">Tip: {q["tip"]}</font>', st["qa"]))
            flow.append(Spacer(1, 6))

    flow.append(Spacer(1, 8))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))
    flow.append(Paragraph(
        "Generated by the AI Job Application Agent. Review and personalize before submitting.", st["meta"]))

    doc.build(flow)
    return buf.getvalue()
