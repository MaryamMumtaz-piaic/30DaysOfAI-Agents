"""Render an autonomous ML pipeline run into a professional PDF report + model card."""

from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
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
        "meta": ParagraphStyle("M", parent=base["Normal"], fontSize=8.5, textColor=MUTED),
    }


def build_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
        title="ML Pipeline Report",
    )
    st = _styles()
    flow: list = []

    profile = data.get("profile", {}) or {}
    cleaning = data.get("cleaning", {}) or {}
    feats = data.get("features", {}) or {}
    leaderboard = data.get("leaderboard", []) or []
    card = data.get("model_card", {}) or {}
    insights = data.get("insights", {}) or {}
    stats = data.get("stats", {}) or {}
    task_type = data.get("task_type", "")

    # Header
    flow.append(Paragraph("Autonomous ML Pipeline Report", st["title"]))
    flow.append(Paragraph(
        f'Target: <b>{_esc(data.get("target",""))}</b> · {task_type} · '
        f'{profile.get("rows","?")} rows × {profile.get("cols","?")} columns', st["subtitle"]))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))

    # KPI chips
    chips = [
        ("Best model", stats.get("best_model", "—")),
        (f'Test {stats.get("best_metric","score")}', stats.get("best_score", "—")),
        ("Features used", stats.get("features_used", 0)),
        ("Rows", stats.get("rows", 0)),
    ]
    chip_row = [[Paragraph(f'<b><font color="{ACCENT.hexval()}">{v}</font></b><br/>'
                           f'<font size="7" color="#64748b">{lbl}</font>', st["cell"])
                 for lbl, v in chips]]
    ct = Table(chip_row, colWidths=[45 * mm] * 4)
    ct.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    flow.append(Spacer(1, 8))
    flow.append(ct)

    # Executive summary
    if insights.get("summary"):
        flow.append(Paragraph("Executive Summary", st["h2"]))
        flow.append(Paragraph(_esc(insights["summary"]), st["body"]))
        _bullets(flow, st, "Key findings", insights.get("findings"))
        _bullets(flow, st, "Recommendations", insights.get("recommendations"))

    # Data profile
    flow.append(Paragraph("Data Profile", st["h2"]))
    flow.append(Paragraph(
        f'{profile.get("rows",0)} rows, {profile.get("cols",0)} columns · '
        f'{profile.get("total_missing",0)} missing cells · '
        f'{profile.get("duplicate_rows",0)} duplicate rows.', st["item"]))
    cols = profile.get("columns", [])
    if cols:
        rows = [[Paragraph("<b>Column</b>", st["cellh"]), Paragraph("<b>Type</b>", st["cellh"]),
                 Paragraph("<b>Missing</b>", st["cellh"]), Paragraph("<b>Unique</b>", st["cellh"]),
                 Paragraph("<b>Summary</b>", st["cellh"])]]
        for c in cols[:30]:
            if c.get("kind") == "numeric":
                summ = f'μ={c.get("mean")} σ={c.get("std")} [{c.get("min")}, {c.get("max")}]'
            else:
                tv = ", ".join(f'{t["value"]}({t["count"]})' for t in c.get("top_values", [])[:3])
                summ = tv
            rows.append([
                Paragraph(f'<b>{_esc(c["name"])}</b>', st["cell"]),
                Paragraph(_esc(c["dtype"]), st["cell"]),
                Paragraph(f'{c["missing_pct"]}%', st["cell"]),
                Paragraph(str(c["unique"]), st["cell"]),
                Paragraph(_esc(summ), st["cell"]),
            ])
        tbl = Table(rows, colWidths=[38 * mm, 20 * mm, 18 * mm, 18 * mm, 86 * mm], repeatRows=1)
        tbl.setStyle(_grid(ACCENT))
        flow.append(Spacer(1, 4))
        flow.append(tbl)

    # Correlations
    if profile.get("correlations"):
        flow.append(Paragraph("Top correlations with target", st["h3"]))
        corr = " · ".join(f'{c["feature"]}: {c["corr"]}' for c in profile["correlations"])
        flow.append(Paragraph(_esc(corr), st["item"]))

    # Cleaning
    flow.append(Paragraph("Data Cleaning", st["h2"]))
    for line in cleaning.get("log", []):
        flow.append(Paragraph(f'• {_esc(line)}', st["item"]))
        flow.append(Spacer(1, 1))

    # Feature engineering
    flow.append(Paragraph("Feature Engineering", st["h2"]))
    flow.append(Paragraph(
        f'{feats.get("n_features_in",0)} input columns → '
        f'<b>{feats.get("n_features_out",0)}</b> model features. '
        f'{len(feats.get("numeric",[]))} numeric, {len(feats.get("categorical",[]))} categorical.',
        st["item"]))
    if feats.get("engineered"):
        flow.append(Paragraph("Engineered: " + _esc("; ".join(feats["engineered"])), st["item"]))

    # Leaderboard
    flow.append(Paragraph("Model Leaderboard", st["h2"]))
    if leaderboard:
        metric = leaderboard[0].get("primary_metric", "score")
        rows = [[Paragraph("<b>#</b>", st["cellh"]), Paragraph("<b>Model</b>", st["cellh"]),
                 Paragraph("<b>CV score</b>", st["cellh"]),
                 Paragraph(f"<b>Test {metric}</b>", st["cellh"]),
                 Paragraph("<b>Other metrics</b>", st["cellh"])]]
        for i, m in enumerate(leaderboard, 1):
            other = " · ".join(f'{k}={v}' for k, v in (m.get("metrics", {}) or {}).items()
                               if k not in ("accuracy", "r2"))
            star = " ★" if i == 1 else ""
            rows.append([
                Paragraph(f'{i}{star}', st["cell"]),
                Paragraph(f'<b>{_esc(m["name"])}</b>', st["cell"]),
                Paragraph(f'{m.get("cv_score")} ± {m.get("cv_std")}', st["cell"]),
                Paragraph(str(m.get("primary_score")), st["cell"]),
                Paragraph(_esc(other), st["cell"]),
            ])
        tbl = Table(rows, colWidths=[12 * mm, 44 * mm, 34 * mm, 28 * mm, 62 * mm], repeatRows=1)
        tbl.setStyle(_grid(ACCENT))
        flow.append(tbl)
        flow.append(Paragraph("★ = selected for tuning · ranked by cross-validation score", st["meta"]))

    # Model card
    flow.append(Paragraph("Model Card (tuned)", st["h2"]))
    mc_rows = [
        ["Model", card.get("name", "—"), "Task", card.get("task_type", "—")],
        ["Test score", str(card.get("test_score", "—")), "Tuned CV", str(card.get("tuned_cv_score", "—"))],
        ["Train size", str(card.get("train_size", "—")), "Test size", str(card.get("test_size", "—"))],
    ]
    rows = []
    for a, b, c, d in mc_rows:
        rows.append([
            Paragraph(f'<font color="#64748b">{a}</font>', st["cell"]),
            Paragraph(f'<b>{_esc(b)}</b>', st["cell"]),
            Paragraph(f'<font color="#64748b">{c}</font>', st["cell"]),
            Paragraph(f'<b>{_esc(d)}</b>', st["cell"]),
        ])
    tbl = Table(rows, colWidths=[30 * mm, 60 * mm, 30 * mm, 60 * mm])
    tbl.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f5f3ff")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    flow.append(tbl)

    # Test metrics
    if card.get("test_metrics"):
        flow.append(Paragraph("Test metrics: " + _esc(
            " · ".join(f'{k}={v}' for k, v in card["test_metrics"].items())), st["item"]))
    # Best params
    if card.get("best_params"):
        flow.append(Paragraph("Best hyperparameters: " + _esc(
            ", ".join(f'{k}={v}' for k, v in card["best_params"].items())), st["item"]))

    # Feature importances
    if card.get("feature_importances"):
        flow.append(Paragraph("Feature Importances", st["h3"]))
        rows = [[Paragraph("<b>Feature</b>", st["cellh"]),
                 Paragraph("<b>Importance</b>", st["cellh"]),
                 Paragraph("<b>Share</b>", st["cellh"])]]
        for f in card["feature_importances"]:
            rows.append([
                Paragraph(_esc(f["feature"]), st["cell"]),
                Paragraph(str(f["importance"]), st["cell"]),
                Paragraph(f'{f["pct"]}%', st["cell"]),
            ])
        tbl = Table(rows, colWidths=[100 * mm, 40 * mm, 40 * mm], repeatRows=1)
        tbl.setStyle(_grid(ACCENT))
        flow.append(tbl)

    flow.append(Spacer(1, 10))
    flow.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))
    flow.append(Paragraph(
        "Generated by the Autonomous Data Science Pipeline. All metrics are computed on a held-out "
        "test split with scikit-learn.", st["meta"]))

    doc.build(flow)
    return buf.getvalue()


def _grid(header_bg, alt: str = "#f5f3ff") -> TableStyle:
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
    return (str(s if s is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
