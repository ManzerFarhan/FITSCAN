"""PDF summary (FR-AI-8, API-09, BR-10, BR-13) with ReportLab. Extracted facts and AI-generated
text are in clearly labelled, visually distinct sections; the disclaimer is on every page."""
from __future__ import annotations

import io
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.constants import DISCLAIMER_TEXT
from app.db.models import Analysis, Document

BRAND = colors.HexColor("#0f766e")
AI_BG = colors.HexColor("#eef2ff")
EX_BG = colors.HexColor("#f0fdfa")
STATUS_COLORS = {"ABOVE": colors.HexColor("#b45309"), "BELOW": colors.HexColor("#1d4ed8"),
                 "WITHIN": colors.HexColor("#15803d"), "UNKNOWN": colors.grey}


def _styles():
    ss = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1", parent=ss["Heading1"], textColor=BRAND, fontSize=18, spaceAfter=4),
        "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12.5, spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle("body", parent=ss["BodyText"], fontSize=9.5, leading=13, alignment=TA_LEFT),
        "small": ParagraphStyle("small", parent=ss["BodyText"], fontSize=8, leading=10, textColor=colors.HexColor("#475569")),
        "tag": ParagraphStyle("tag", parent=ss["BodyText"], fontSize=8, textColor=colors.white),
        "cell": ParagraphStyle("cell", parent=ss["BodyText"], fontSize=8.5, leading=11),
    }


def _label(text: str, bg) -> Table:
    t = Table([[Paragraph(f"<b>{text}</b>", _styles()["tag"])]], hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LEFTPADDING", (0, 0), (-1, -1), 6),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 2),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    return t


def _box(flowables, bg) -> Table:
    t = Table([[flowables]], colWidths=[180 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return t


def _on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#475569"))
    text = canvas.beginText(15 * mm, 12 * mm)
    words, line = DISCLAIMER_TEXT.split(), ""
    for w in words:
        if canvas.stringWidth(line + " " + w, "Helvetica", 7) > 165 * mm:
            text.textLine(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    text.textLine(line)
    canvas.drawText(text)
    canvas.drawRightString(195 * mm, 6 * mm, f"FITSCAN summary - page {doc.page}")
    canvas.restoreState()


def build_pdf(doc: Document, analysis: Analysis, comparison: dict | None = None) -> bytes:
    st = _styles()
    s = analysis.summary_json
    buf = io.BytesIO()
    pdf = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=15 * mm,
                            bottomMargin=24 * mm, title="FITSCAN report summary", author="FITSCAN")
    E = lambda x: escape(str(x)) if x is not None else "-"  # noqa: E731
    story = [
        Paragraph("FITSCAN - Lab Report Summary", st["h1"]),
        Paragraph(f"Generated {datetime.now().strftime('%d %b %Y, %H:%M')} &nbsp;|&nbsp; Prompt version {E(analysis.prompt_version)} "
                  f"&nbsp;|&nbsp; Text by {E(analysis.model)}", st["small"]),
        Spacer(1, 4),
        _box([Paragraph(f"<b>Important:</b> {E(DISCLAIMER_TEXT)}", st["body"])], colors.HexColor("#fff7ed")),
        Paragraph("Report details", st["h2"]), _label("EXTRACTED FROM YOUR DOCUMENT", BRAND), Spacer(1, 3),
    ]
    details = [["Patient", E(doc.patient_name)], ["Lab", E(doc.lab_name)], ["Lab address", E(doc.lab_address)],
               ["Report category", E(doc.report_category)], ["Report date", E(doc.report_date)],
               ["Sample collected", E(doc.collected_date)], ["Report number", E(doc.report_number)],
               ["Uploaded to FITSCAN", doc.uploaded_at.strftime("%d %b %Y")]]
    t = Table([[Paragraph(f"<b>{a}</b>", st["cell"]), Paragraph(b, st["cell"])] for a, b in details], colWidths=[45 * mm, 135 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), EX_BG), ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1"))]))
    story.append(t)

    c = s["counts"]
    story += [Paragraph("Results", st["h2"]), _label("EXTRACTED VALUES - CHECKED BY YOU", BRAND), Spacer(1, 3),
              Paragraph(f"{c['verified']} verified values: {c['within']} within, {c['below']} below and {c['above']} above "
                        f"the lab's own reference range; {c['unknown']} could not be compared. "
                        f"{c['needs_verification']} unverified value(s) were left out.", st["body"]), Spacer(1, 3)]
    rows = [[Paragraph(f"<b>{h}</b>", st["cell"]) for h in ("Parameter", "Value", "Lab reference range", "Status", "Source")]]
    for r in s["parameters"]:
        color = STATUS_COLORS.get(r["status"], colors.grey)
        rows.append([Paragraph(E(r["name"]), st["cell"]), Paragraph(f"{E(r['value'])} {E(r['unit'] or '')}", st["cell"]),
                     Paragraph(E(r["ref_raw"]), st["cell"]),
                     Paragraph(f"<font color='{color.hexval()}'><b>{E(r['status'])}</b></font>" + (f" (lab flag {E(r['lab_flag'])})" if r["lab_flag"] else ""), st["cell"]),
                     Paragraph("You corrected" if r["value_source"] == "USER_CORRECTED" else "Extracted", st["cell"])])
    t = Table(rows, colWidths=[50 * mm, 30 * mm, 45 * mm, 32 * mm, 23 * mm], repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                           ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(t)

    if s.get("urgent"):
        story += [Spacer(1, 6), _box([Paragraph(f"<b>{E(u['name'])}:</b> {E(u['urgent_message'])}", st["body"]) for u in s["urgent"]],
                                     colors.HexColor("#fee2e2"))]

    story += [Paragraph("Explanations", st["h2"]), _label("AI-GENERATED - GENERAL INFORMATION, NOT A DIAGNOSIS", colors.HexColor("#4338ca")), Spacer(1, 3)]
    expl = [Paragraph(f"<b>{E(r['name'])}</b> - {E(r['explanation'])} <i>{E(r['context'])}</i>", st["body"]) for r in s["parameters"]]
    story.append(_box(expl, AI_BG))
    if analysis.observations_json:
        story += [Paragraph("Observations", st["h2"]), _label("AI-GENERATED", colors.HexColor("#4338ca")), Spacer(1, 3),
                  _box([Paragraph(f"- {E(o)}", st["body"]) for o in analysis.observations_json], AI_BG)]
    if comparison and comparison.get("compared"):
        story += [Paragraph("Comparison with earlier reports", st["h2"]), _label("CALCULATED FROM VERIFIED VALUES", BRAND), Spacer(1, 3)]
        crow = [[Paragraph(f"<b>{h}</b>", st["cell"]) for h in ("Parameter", "Previous", "Current", "Change", "Range changed?")]]
        for cp in comparison["compared"]:
            pct = f" ({cp['percent_change']:+g}%)" if cp["percent_change"] is not None else ""
            crow.append([Paragraph(E(cp["name"]), st["cell"]),
                         Paragraph(f"{cp['previous']['value']:g} ({E(cp['previous']['date'])})", st["cell"]),
                         Paragraph(f"{cp['current']['value']:g} ({E(cp['current']['date'])})", st["cell"]),
                         Paragraph(f"{cp['absolute_change']:+g} {E(cp['unit'] or '')}{pct}", st["cell"]),
                         Paragraph("Yes" if cp["reference_range_changed"] else "No", st["cell"])])
        t = Table(crow, colWidths=[45 * mm, 37 * mm, 37 * mm, 38 * mm, 23 * mm])
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                               ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0"))]))
        story.append(t)
        if comparison.get("summary"):
            story += [Spacer(1, 4), _label("AI-GENERATED", colors.HexColor("#4338ca")), Spacer(1, 2),
                      _box([Paragraph(E(comparison["summary"]["text"]), st["body"])], AI_BG)]
    if s.get("doctor_questions"):
        story += [Paragraph("Questions you could ask your doctor", st["h2"]), _label("AI-GENERATED", colors.HexColor("#4338ca")), Spacer(1, 3),
                  _box([Paragraph(f"{i + 1}. {E(q)}", st["body"]) for i, q in enumerate(s["doctor_questions"])], AI_BG)]
    story.append(Paragraph("Sources", st["h2"]))
    if analysis.sources_json:
        for i, src in enumerate(analysis.sources_json):
            story.append(Paragraph(f"[S{i + 1}] {E(src['title'])} - {E(src['source'])}: {E(src['url'])}", st["small"]))
    else:
        story.append(Paragraph("No sources were retrieved for this summary.", st["small"]))
    story += [Spacer(1, 8), Paragraph(f"<b>Disclaimer:</b> {E(DISCLAIMER_TEXT)}", st["small"])]
    pdf.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()
