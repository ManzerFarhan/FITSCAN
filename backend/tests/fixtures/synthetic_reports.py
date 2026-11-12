"""Synthetic lab reports in several layouts + expected extraction (P2-28). NO real patient data.

Each layout is a different "lab" with different column order, header wording, range styles,
flags and units, to exercise the layout-agnostic parser.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


@dataclass
class Expected:
    parameter_id: str
    value: float
    ref_low: float | None
    ref_high: float | None
    status: str
    unit: str | None = None
    flag: str | None = None


@dataclass
class Layout:
    key: str
    header_lines: list[str]
    columns: list[tuple[str, float]]  # (title, x)
    rows: list[list[str]]
    expected: list[Expected]
    meta: dict = field(default_factory=dict)
    second_page_rows: list[list[str]] = field(default_factory=list)
    show_header: bool = True


LAYOUTS: list[Layout] = [
    Layout(
        key="apex_cbc",
        header_lines=["APEX DIAGNOSTICS LABORATORY", "12 MG Road, Sector 5, Pune 411001",
                      "Patient Name : Test Patient One        Age/Sex : 34 Y / F",
                      "Report No : APX-2024-0001    Collected On : 03/02/2024    Reported On : 04/02/2024"],
        columns=[("Test Name", 50), ("Result", 260), ("Unit", 340), ("Biological Reference Interval", 420)],
        rows=[
            ["Haemoglobin", "11.2", "g/dL", "12.0 - 15.0"],
            ["Total Leucocyte Count", "7800", "cells/cumm", "4000 - 11000"],
            ["Platelet Count", "2.1", "lakhs/cumm", "1.5 - 4.5"],
            ["Packed Cell Volume (PCV)", "36.5", "%", "36 - 46"],
            ["MCV", "79.0", "fL", "83 - 101"],
            ["ESR", "28", "mm/1st hr", "0 - 20"],
        ],
        expected=[
            Expected("hemoglobin", 11.2, 12.0, 15.0, "BELOW", "g/dL"),
            Expected("wbc_count", 7800, 4000, 11000, "WITHIN", "/µL"),
            Expected("platelet_count", 2.1, 1.5, 4.5, "WITHIN", "lakh/µL"),
            Expected("hematocrit", 36.5, 36, 46, "WITHIN", "%"),
            Expected("mcv", 79.0, 83, 101, "BELOW", "fL"),
            Expected("esr", 28, 0, 20, "ABOVE", "mm/hr"),
        ],
        meta={"lab_name": "APEX DIAGNOSTICS LABORATORY", "report_date": "2024-02-04", "collected_date": "2024-02-03",
              "patient_name": "Test Patient One", "report_number": "APX-2024-0001", "report_category": "CBC"},
    ),
    Layout(
        key="sunrise_lft",
        header_lines=["Sunrise Pathology Lab", "Plot 44, Lake View Road, Bengaluru 560001",
                      "Name: Sample Person Two      Gender: Male", "Sample Collected: 15-Mar-2024   Report Date: 16-Mar-2024"],
        columns=[("Investigation", 50), ("Observed Value", 250), ("Flag", 335), ("Reference Range", 380), ("Units", 500)],
        rows=[
            ["Bilirubin - Total", "1.6", "H", "0.3 - 1.2", "mg/dL"],
            ["Bilirubin Direct", "0.3", "", "0.0 - 0.3", "mg/dL"],
            ["SGOT (AST)", "45", "H", "< 40", "U/L"],
            ["SGPT (ALT)", "38", "", "up to 41", "U/L"],
            ["Alkaline Phosphatase", "98", "", "40 - 129", "U/L"],
            ["Serum Albumin", "4.4", "", "3.5 - 5.2", "g/dL"],
        ],
        expected=[
            Expected("bilirubin_total", 1.6, 0.3, 1.2, "ABOVE", "mg/dL", "H"),
            Expected("bilirubin_direct", 0.3, 0.0, 0.3, "WITHIN", "mg/dL"),
            Expected("ast_sgot", 45, None, 40, "ABOVE", "U/L", "H"),
            Expected("alt_sgpt", 38, None, 41, "WITHIN", "U/L"),
            Expected("alp", 98, 40, 129, "WITHIN", "U/L"),
            Expected("albumin", 4.4, 3.5, 5.2, "WITHIN", "g/dL"),
        ],
        meta={"lab_name": "Sunrise Pathology Lab", "report_date": "2024-03-16", "collected_date": "2024-03-15", "report_category": "LFT"},
    ),
    Layout(
        key="citycare_lipid_noheader",
        header_lines=["CityCare Diagnostics", "2nd Floor, Station Road, Nashik 422001",
                      "Patient Name: Demo User Three", "Date: 10/01/2024"],
        columns=[("", 50), ("", 250), ("", 320), ("", 400)],
        show_header=False,
        rows=[
            ["Total Cholesterol", "212", "mg/dL", "Desirable: <200 Borderline: 200-239"],
            ["Triglycerides", "140", "mg/dL", "< 150"],
            ["HDL Cholesterol", "38", "mg/dL", "> 40"],
            ["LDL Cholesterol", "146", "mg/dL", "< 100"],
            ["VLDL Cholesterol", "28", "mg/dL", "5 - 40"],
        ],
        expected=[
            Expected("cholesterol_total", 212, None, 200, "ABOVE", "mg/dL"),
            Expected("triglycerides", 140, None, 150, "WITHIN", "mg/dL"),
            Expected("hdl", 38, 40, None, "BELOW", "mg/dL"),
            Expected("ldl", 146, None, 100, "ABOVE", "mg/dL"),
            Expected("vldl", 28, 5, 40, "WITHIN", "mg/dL"),
        ],
        meta={"lab_name": "CityCare Diagnostics", "report_date": "2024-01-10", "report_category": "LIPID"},
    ),
    Layout(
        key="medline_thyroid_sugar_inlineflag",
        header_lines=["Medline Labs & Imaging", "Opp. City Mall, Nagpur 440001",
                      "Pt. Name : Example Person Four", "Reg. No : ML/77/2024   Reported : 22 Apr 2024"],
        columns=[("Parameter", 50), ("Result", 260), ("Reference Interval", 360)],
        rows=[
            ["TSH - Ultrasensitive", "6.8 H", "0.4 - 4.0 µIU/mL"],
            ["Free T4", "1.1", "0.9 - 1.7 ng/dL"],
            ["Fasting Blood Sugar", "112 H", "70 - 100 mg/dL"],
            ["Glycosylated Haemoglobin (HbA1c)", "6.1", "4.0 - 5.6 %"],
        ],
        expected=[
            Expected("tsh", 6.8, 0.4, 4.0, "ABOVE", "µIU/mL", "H"),
            Expected("ft4", 1.1, 0.9, 1.7, "WITHIN", "ng/dL"),
            Expected("glucose_fasting", 112, 70, 100, "ABOVE", "mg/dL", "H"),
            Expected("hba1c", 6.1, 4.0, 5.6, "ABOVE", "%"),
        ],
        meta={"lab_name": "Medline Labs & Imaging", "report_date": "2024-04-22", "report_number": "ML/77/2024"},
    ),
    Layout(
        key="lifeline_kft_sexranges",
        header_lines=["LIFELINE HOSPITAL LABORATORY", "Ward 3, Civil Lines, Jaipur 302006",
                      "Patient Name : Sample Male Five     Age/Sex : 45 Y / M",
                      "Lab No : LL-5512    Reporting Date : 05.05.2024"],
        columns=[("Test", 50), ("Value", 230), ("Units", 300), ("Normal Range", 380)],
        rows=[
            ["Blood Urea", "32", "mg/dL", "15 - 40"],
            ["Serum Creatinine", "1.4", "mg/dL", "M: 0.7-1.3 F: 0.6-1.1"],
            ["Uric Acid", "6.2", "mg/dL", "M: 3.4-7.0 F: 2.4-5.7"],
            ["Sodium (Na+)", "139", "mmol/L", "135 - 145"],
            ["Potassium (K+)", "4.6", "mEq/L", "3.5 - 5.1"],
        ],
        expected=[
            Expected("urea", 32, 15, 40, "WITHIN", "mg/dL"),
            Expected("creatinine", 1.4, 0.7, 1.3, "ABOVE", "mg/dL"),
            Expected("uric_acid", 6.2, 3.4, 7.0, "WITHIN", "mg/dL"),
            Expected("sodium", 139, 135, 145, "WITHIN", "mmol/L"),
            Expected("potassium", 4.6, 3.5, 5.1, "WITHIN", "mEq/L"),
        ],
        meta={"lab_name": "LIFELINE HOSPITAL LABORATORY", "report_date": "2024-05-05", "report_number": "LL-5512", "report_category": "KFT"},
    ),
    Layout(
        key="greenleaf_twopage_vitamins",
        header_lines=["GreenLeaf Diagnostic Centre", "Shop 9, Park Street, Kolkata 700016",
                      "Patient Name : Synthetic Six", "Report Date : 2024-06-18"],
        columns=[("Test Description", 50), ("Result", 270), ("Unit", 340), ("Ref. Range", 420)],
        rows=[
            ["Vitamin B12", "180", "pg/mL", "211 - 911"],
            ["25-OH Vitamin D", "14.2", "ng/mL", "30 - 100"],
        ],
        second_page_rows=[
            ["Calcium", "9.4", "mg/dL", "8.6 - 10.2"],
            ["Serum Ferritin", "45", "ng/mL", "22 - 322"],
        ],
        expected=[
            Expected("vitamin_b12", 180, 211, 911, "BELOW", "pg/mL"),
            Expected("vitamin_d", 14.2, 30, 100, "BELOW", "ng/mL"),
            Expected("calcium", 9.4, 8.6, 10.2, "WITHIN", "mg/dL"),
            Expected("ferritin", 45, 22, 322, "WITHIN", "ng/mL"),
        ],
        meta={"lab_name": "GreenLeaf Diagnostic Centre", "report_date": "2024-06-18"},
    ),
]


def _draw_table(c: canvas.Canvas, layout: Layout, rows: list[list[str]], y: float) -> float:
    if layout.show_header:
        c.setFont("Helvetica-Bold", 10)
        for title, x in layout.columns:
            c.drawString(x, y, title)
        y -= 22
    c.setFont("Helvetica", 10)
    for row in rows:
        for (_, x), val in zip(layout.columns, row):
            if val:
                c.drawString(x, y, val)
        y -= 20
    return y


def render_pdf(layout: Layout) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    _, height = A4
    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, layout.header_lines[0])
    y -= 18
    c.setFont("Helvetica", 9)
    for line in layout.header_lines[1:]:
        c.drawString(50, y, line)
        y -= 15
    y -= 20
    _draw_table(c, layout, layout.rows, y)
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, 40, "*** End of page - synthetic document for testing ***")
    if layout.second_page_rows:
        c.showPage()
        _draw_table(c, layout, layout.second_page_rows, height - 80)
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(50, 40, "*** End of report - synthetic document for testing ***")
    c.save()
    return buf.getvalue()


def render_png(layout: Layout, dpi: int = 200) -> bytes:
    """Rasterized version (simulates a scanned/photographed report) for the OCR path."""
    import pymupdf as fitz

    with fitz.open(stream=render_pdf(layout), filetype="pdf") as doc:
        return doc.load_page(0).get_pixmap(dpi=dpi).tobytes("png")
