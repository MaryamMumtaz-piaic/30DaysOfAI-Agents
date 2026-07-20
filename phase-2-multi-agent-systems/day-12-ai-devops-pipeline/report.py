"""Render a DevOps PR analysis into a professional PDF report."""

from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
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

ACCENT = colors.HexColor("#0ea5e9")   # sky-500
INK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")

SEV_INK = {
    "critical": colors.HexColor("#7f1d1d"),
    "high": colors.HexColor("#991b1b"),
    "medium": colors.HexColor("#92400e"),
    "low": colors.HexColor("#3f6212"),
}
DECISION_BG = {
    "APPROVE": colors.HexColor("#16a34a"),
    "REQUEST CHANGES": colors.HexColor("#d97706"),
    "BLOCK": colors.HexColor("#dc2626"),
}
AGENTS = [
    ("quality", "Code Quality", "findings"),
    ("security", "Security", "findings"),
    ("coverage", "Test Coverage", "gaps"),
    ("performance", "Performance", "findings"),
]


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("T", parent=base["Title"], fontSize=21,
                                 textColor=ACCENT, spaceAfter=4),
        "subtitle": ParagraphStyle("S", parent=base["Normal"], fontSize=10,
                                    textColor=MUTED, spaceAfter=12),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], fontSize=14,
                             textColor=INK, spaceBefore=16, spaceAfter=6),
        "h3": ParagraphStyle("H3", parent=base["Heading3"], fontSize=11,
                             textColor=ACCENT, spaceBefore=8, spaceAfter=3),
        "body": ParagraphStyle("B", parent=base["Normal"], fontSize=10,
                               leading=15, alignment=TA_JUSTIFY, spaceAfter=6),
        "item": ParagraphStyle("I", parent=base["Normal"], fontSize=9.5,
                               leading=14, alignment=TA_LEFT),
        "cell": ParagraphStyle("C", parent=base["Normal"], fontSize=8.5, leading=11),
        "cellh": ParagraphStyle("CH", parent=base["Normal"], fontSize=8.5,
                                leading=11, textColor=colors.white),
        "verdict": ParagraphStyle("V", parent=base["Normal"], fontSize=15,
                                  textColor=colors.white, alignment=TA_CENTER),
        "meta": ParagraphStyle("M", parent=base["Normal"], fontSize=8.5, textColor=MUTED),
    }


def build_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=16 * mm, rightMargin=16 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title="PR Analysis Report",
    )
    st = _styles()
    flow: list = []

    analyses = data.get("analyses", {}) or {}
    decision = data.get("decision", {}) or {}
    stats = data.get("stats", {}) or {}
    ds = data.get("diff_stats", {}) or {}

    # Header
    flow.append(Paragraph(_esc(data.get("title", "Pull Request Analysis")), st["title"]))
    sub = data.get("pr_url") or (
        f'+{ds.get("additions",0)}/-{ds.get("deletions",0)} across {ds.get("files",0)} file(s)'
    )
    flow.append(Paragraph(_esc(sub), st["subtitle"]))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))

    # Decision banner
    dec = decision.get("decision", "REQUEST CHANGES")
    bg = DECISION_BG.get(dec, colors.HexColor("#d97706"))
    banner = Table(
        [[Paragraph(
            f'<b>{_esc(dec)}</b> &nbsp; — &nbsp; risk: {_esc(decision.get("risk","—"))} '
            f'&nbsp;·&nbsp; confidence {decision.get("confidence",0)}%', st["verdict"])]],
        colWidths=[178 * mm],
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    flow.append(Spacer(1, 8))
    flow.append(banner)

    # Score chips
    chips = [("Overall", f'{stats.get("overall_score",0)}/100')]
    for key, label, _ in AGENTS:
        chips.append((label, f'{analyses.get(key,{}).get("score",0)}'))
    chip_row = [[Paragraph(f'<b><font color="{ACCENT.hexval()}">{v}</font></b><br/>'
                           f'<font size="7" color="#64748b">{lbl}</font>', st["cell"])
                 for lbl, v in chips]]
    ct = Table(chip_row, colWidths=[35.6 * mm] * 5)
    ct.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    flow.append(Spacer(1, 8))
    flow.append(ct)

    # Decision detail
    if decision.get("rationale"):
        flow.append(Paragraph("Deployment Decision", st["h2"]))
        flow.append(Paragraph(_esc(decision["rationale"]), st["body"]))
        _bullets(flow, st, "Blocking issues", decision.get("blocking_issues"))
        _bullets(flow, st, "Required actions", decision.get("required_actions"))
        if decision.get("rollback_plan"):
            flow.append(Paragraph(f'<b>Rollback plan:</b> {_esc(decision["rollback_plan"])}', st["item"]))

    # Per-agent findings
    for key, label, fk in AGENTS:
        a = analyses.get(key, {}) or {}
        flow.append(Paragraph(f'{label} — {a.get("score",0)}/100', st["h2"]))
        if a.get("summary"):
            flow.append(Paragraph(_esc(a["summary"]), st["body"]))
        items = a.get(fk, []) or []
        if not items:
            flow.append(Paragraph("No issues flagged.", st["item"]))
        else:
            rows = [[Paragraph("<b>Sev</b>", st["cellh"]),
                     Paragraph("<b>Issue</b>", st["cellh"]),
                     Paragraph("<b>Detail</b>", st["cellh"]),
                     Paragraph("<b>Suggestion</b>", st["cellh"])]]
            for f in items:
                sev = str(f.get("severity", "")).lower()
                titlecell = f.get("title") or f.get("area") or "—"
                detail = f.get("detail", "")
                extra = f.get("cwe")
                if extra:
                    detail = f"[{extra}] {detail}"
                rows.append([
                    Paragraph(f'<font color="{SEV_INK.get(sev, MUTED).hexval()}">{sev}</font>', st["cell"]),
                    Paragraph(f'<b>{_esc(titlecell)}</b>', st["cell"]),
                    Paragraph(_esc(detail), st["cell"]),
                    Paragraph(_esc(f.get("suggestion", "")), st["cell"]),
                ])
            tbl = Table(rows, colWidths=[16 * mm, 40 * mm, 66 * mm, 56 * mm], repeatRows=1)
            tbl.setStyle(_grid(ACCENT))
            flow.append(tbl)
        if a.get("positives"):
            _bullets(flow, st, "Done well", a.get("positives"))

    # PR comment preview
    if decision.get("pr_comment"):
        flow.append(Paragraph("Suggested PR Comment", st["h2"]))
        flow.append(Paragraph(_esc(decision["pr_comment"]), st["body"]))

    flow.append(Spacer(1, 10))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))
    flow.append(Paragraph("Generated by the AI DevOps & CI/CD Intelligence Pipeline.", st["meta"]))

    doc.build(flow)
    return buf.getvalue()


def _grid(header_bg, alt: str = "#f0f9ff") -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(alt)]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ])


def _bullets(flow: list, st: dict, label: str, items) -> None:
    items = [x for x in (items or []) if x]
    if not items:
        return
    flow.append(Paragraph(label, st["h3"]))
    for it in items:
        flow.append(Paragraph(f'• {_esc(it)}', st["item"]))
        flow.append(Spacer(1, 1))


def _esc(s) -> str:
    return (str(s or "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
