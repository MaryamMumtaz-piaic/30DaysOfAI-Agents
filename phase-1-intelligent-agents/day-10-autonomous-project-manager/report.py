"""Render an autonomous project plan into a professional PDF report."""

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

PRIORITY_INK = {
    "high": colors.HexColor("#991b1b"),
    "medium": colors.HexColor("#92400e"),
    "low": colors.HexColor("#3f6212"),
}
RISK_INK = {"high": colors.HexColor("#991b1b"), "medium": colors.HexColor("#92400e"),
            "low": colors.HexColor("#3f6212")}


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
        "cell": ParagraphStyle("C", parent=base["Normal"], fontSize=8.5, leading=11),
        "cellh": ParagraphStyle("CH", parent=base["Normal"], fontSize=8.5,
                                leading=11, textColor=colors.white),
        "meta": ParagraphStyle("M", parent=base["Normal"], fontSize=8.5, textColor=MUTED),
    }


def build_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=16 * mm, rightMargin=16 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title="Project Plan",
    )
    st = _styles()
    flow: list = []
    stats = data.get("stats", {}) or {}
    tasks = data.get("tasks", [])

    # Header
    flow.append(Paragraph(data.get("title", "Project Plan"), st["title"]))
    flow.append(Paragraph(data.get("objective", ""), st["subtitle"]))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))

    # Stat chips
    chips = [
        ("Phases", stats.get("phases", 0)),
        ("Tasks", stats.get("tasks", 0)),
        ("Story points", stats.get("total_points", 0)),
        ("Duration", f"~{stats.get('duration_days', 0)}d"),
    ]
    chip_row = [[Paragraph(f'<b><font color="{ACCENT.hexval()}">{v}</font></b><br/>'
                           f'<font size="7" color="#64748b">{lbl}</font>', st["cell"])
                 for lbl, v in chips]]
    ct = Table(chip_row, colWidths=[42 * mm] * 4)
    ct.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    flow.append(Spacer(1, 6))
    flow.append(ct)

    # Roles
    if data.get("roles"):
        flow.append(Paragraph("Team Roles", st["h2"]))
        flow.append(Paragraph(", ".join(str(r) for r in data["roles"]), st["body"]))

    # Phases
    if data.get("phases"):
        flow.append(Paragraph("Phases", st["h2"]))
        for i, p in enumerate(data["phases"], 1):
            flow.append(Paragraph(
                f'<b>{i}. {_esc(p.get("name",""))}</b> — {_esc(p.get("goal",""))}', st["item"]))
            flow.append(Spacer(1, 2))

    # Tasks table
    if tasks:
        cp = set(data.get("critical_path", []))
        flow.append(Paragraph("Tasks & Estimates", st["h2"]))
        rows = [[Paragraph("<b>ID</b>", st["cellh"]),
                 Paragraph("<b>Task</b>", st["cellh"]),
                 Paragraph("<b>Phase</b>", st["cellh"]),
                 Paragraph("<b>Role</b>", st["cellh"]),
                 Paragraph("<b>Pri</b>", st["cellh"]),
                 Paragraph("<b>SP</b>", st["cellh"]),
                 Paragraph("<b>Days</b>", st["cellh"]),
                 Paragraph("<b>Deps</b>", st["cellh"])]]
        for t in tasks:
            star = " ★" if t["id"] in cp else ""
            pr = t.get("priority", "medium")
            rows.append([
                Paragraph(f'{_esc(t["id"])}{star}', st["cell"]),
                Paragraph(f'<b>{_esc(t.get("name",""))}</b>', st["cell"]),
                Paragraph(_esc(t.get("phase", "")), st["cell"]),
                Paragraph(_esc(t.get("role", "")), st["cell"]),
                Paragraph(f'<font color="{PRIORITY_INK.get(pr, MUTED).hexval()}">{pr}</font>', st["cell"]),
                Paragraph(str(t.get("story_points", "")), st["cell"]),
                Paragraph(f'd{t.get("start_offset_days",0)}+{t.get("estimate_days",0)}', st["cell"]),
                Paragraph(_esc(", ".join(t.get("depends_on", [])) or "—"), st["cell"]),
            ])
        tbl = Table(rows, colWidths=[14 * mm, 46 * mm, 30 * mm, 30 * mm, 16 * mm, 10 * mm, 18 * mm, 14 * mm],
                    repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef2ff")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ]))
        flow.append(tbl)
        flow.append(Paragraph("★ = on the critical path · SP = story points · d = start day + duration", st["meta"]))

    # Milestones
    if data.get("milestones"):
        flow.append(Paragraph("Milestones", st["h2"]))
        for m in data["milestones"]:
            flow.append(Paragraph(f'Day {m.get("day",0)} — {_esc(m.get("name",""))}', st["item"]))
            flow.append(Spacer(1, 2))

    # Risks
    if data.get("risks"):
        flow.append(Paragraph("Risk Assessment", st["h2"]))
        rows = [[Paragraph("<b>Risk</b>", st["cellh"]),
                 Paragraph("<b>Likelihood</b>", st["cellh"]),
                 Paragraph("<b>Impact</b>", st["cellh"]),
                 Paragraph("<b>Mitigation</b>", st["cellh"])]]
        for r in data["risks"]:
            lk = str(r.get("likelihood", "")).lower()
            im = str(r.get("impact", "")).lower()
            rows.append([
                Paragraph(_esc(r.get("risk", "")), st["cell"]),
                Paragraph(f'<font color="{RISK_INK.get(lk, MUTED).hexval()}">{lk}</font>', st["cell"]),
                Paragraph(f'<font color="{RISK_INK.get(im, MUTED).hexval()}">{im}</font>', st["cell"]),
                Paragraph(_esc(r.get("mitigation", "")), st["cell"]),
            ])
        tbl = Table(rows, colWidths=[54 * mm, 22 * mm, 20 * mm, 82 * mm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dc2626")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fef2f2")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ]))
        flow.append(tbl)

    flow.append(Spacer(1, 10))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))
    flow.append(Paragraph("Generated by the Autonomous AI Project Manager.", st["meta"]))

    doc.build(flow)
    return buf.getvalue()


def _esc(s) -> str:
    return (str(s or "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
