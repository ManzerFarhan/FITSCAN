"""A synthetic report laid out like real Indian lab PDFs (NO real patient data).

Real reports differ from the tidy fixtures in synthetic_reports.py: a patient block repeated on every page,
department / panel headings, a small "Method:" line under tests, flags printed next to the value, indented
sub-tests, multi-line reference ranges (Desirable / Borderline / High), unicode units, interpretation
paragraphs full of numbers, and "Page x of y" footers.
"""
from __future__ import annotations

import io

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# (name, value, flag, unit, range lines, method, indent) -> expected (parameter_id, value, low, high)
PAGE1 = [
    ("DEPARTMENT OF HAEMATOLOGY", None),
    ("COMPLETE BLOOD COUNT (CBC)", None),
    (("Haemoglobin (Hb)", "13.2", "", "g/dL", ["13.0 - 17.0"], "Photometric", 0), ("hemoglobin", 13.2, 13.0, 17.0)),
    (("Total RBC Count", "4.52", "", "mill/cumm", ["4.5 - 5.5"], "Electrical Impedance", 0), ("rbc_count", 4.52, 4.5, 5.5)),
    (("Total WBC Count", "11800", "H", "cells/cumm", ["4000 - 11000"], "Electrical Impedance", 0), ("wbc_count", 11800, 4000, 11000)),
    (("DIFFERENTIAL LEUCOCYTE COUNT", None)),
    (("Neutrophils", "72", "", "%", ["40 - 80"], None, 12), ("neutrophils_pct", 72, 40, 80)),
    (("Lymphocytes", "18", "L", "%", ["20 - 40"], None, 12), ("lymphocytes_pct", 18, 20, 40)),
    (("Platelet Count", "150", "", "10^3/µL", ["150 - 410"], "Electrical Impedance", 0), ("platelet_count", 150, 150, 410)),
    (("ESR (Westergren)", "22", "H", "mm/hr", ["0 - 15"], None, 0), ("esr", 22, 0, 15)),
]
PAGE2 = [
    ("DEPARTMENT OF BIOCHEMISTRY", None),
    ("LIPID PROFILE", None),
    (("Total Cholesterol", "212", "H", "mg/dL", ["Desirable : < 200", "Borderline : 200 - 239", "High : >= 240"], "CHOD-PAP", 0),
     ("cholesterol_total", 212, None, 200)),
    (("Triglycerides", "180", "H", "mg/dL", ["< 150"], "GPO-PAP", 0), ("triglycerides", 180, None, 150)),
    (("HDL Cholesterol", "38", "L", "mg/dL", ["> 40"], "Direct", 0), ("hdl", 38, 40, None)),
    (("LDL Cholesterol (Calculated)", "138", "H", "mg/dL", ["< 100"], "Calculated", 0), ("ldl", 138, None, 100)),
    ("DIABETES", None),
    (("Glucose Fasting (FBS)", "108", "H", "mg/dL", ["70 - 100"], "Hexokinase", 0), ("glucose_fasting", 108, 70, 100)),
    (("HbA1c (Glycosylated Haemoglobin)", "6.1", "H", "%", ["Non-diabetic : < 5.7", "Pre-diabetic : 5.7 - 6.4", "Diabetic : >= 6.5"], "HPLC", 0),
     ("hba1c", 6.1, None, 5.7)),
    ("Interpretation : As per ADA guidelines an HbA1c of 5.7 - 6.4 % indicates increased risk; values of 6.5 % or", None),
    ("more on two occasions are used for diagnosis. Fasting glucose 100 - 125 mg/dL is impaired fasting glucose.", None),
    ("THYROID & VITAMINS", None),
    (("TSH (Ultrasensitive)", "3.2", "", "µIU/mL", ["0.27 - 4.2"], "CLIA", 0), ("tsh", 3.2, 0.27, 4.2)),
    (("Vitamin D (25-OH)", "18.4", "L", "ng/mL", ["30 - 100"], "CLIA", 0), ("vitamin_d", 18.4, 30, 100)),
    (("Vitamin B12", "245", "", "pg/mL", ["197 - 771"], "CLIA", 0), ("vitamin_b12", 245, 197, 771)),
    (("Serum Creatinine", "1.1", "", "mg/dL", ["0.7 - 1.3"], "Jaffe", 0), ("creatinine", 1.1, 0.7, 1.3)),
]
EXPECTED = [row[1] for row in PAGE1 + PAGE2 if isinstance(row, tuple) and isinstance(row[0], tuple)]

COLS = {"name": 40, "value": 270, "flag": 305, "unit": 330, "range": 420}


def _patient_block(c: canvas.Canvas, top: float) -> float:
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, top, "LIFECARE DIAGNOSTICS & PATHOLOGY")
    c.setFont("Helvetica", 8)
    c.drawString(40, top - 12, "NABL Accredited | ISO 9001:2015 | 2nd Floor, 77 Park Street, Kolkata 700016 | Ph: 033-40012345")
    c.line(40, top - 18, 555, top - 18)
    c.setFont("Helvetica", 9)
    left = ["Patient Name : Mr. Synthetic Person", "Age / Gender : 45 Years / Male", "Referred By : Dr. Self"]
    right = ["Sample ID : 24051234", "Collected : 12/05/2024 08:30 AM", "Reported : 12/05/2024 04:10 PM"]
    for i, (a, b) in enumerate(zip(left, right)):
        c.drawString(40, top - 32 - i * 12, a)
        c.drawString(330, top - 32 - i * 12, b)
    c.line(40, top - 72, 555, top - 72)
    c.setFont("Helvetica-Bold", 9)
    for title, key in (("Test Name", "name"), ("Result", "value"), ("Unit", "unit"), ("Biological Ref. Interval", "range")):
        c.drawString(COLS[key], top - 86, title)
    c.line(40, top - 90, 555, top - 90)
    return top - 106


def _page(c: canvas.Canvas, rows: list, page_no: int, pages: int) -> None:
    _, height = A4
    y = _patient_block(c, height - 40)
    for spec, _expected in rows:
        if isinstance(spec, str):  # heading or paragraph
            c.setFont("Helvetica-Bold" if spec.isupper() else "Helvetica-Oblique", 9 if spec.isupper() else 7.5)
            c.drawString(40, y, spec)
            y -= 14
            continue
        name, value, flag, unit, ranges, method, indent = spec
        c.setFont("Helvetica", 9)
        c.drawString(COLS["name"] + indent, y, name)
        c.setFont("Helvetica-Bold" if flag else "Helvetica", 9)
        c.drawRightString(COLS["value"] + 25, y + _JITTER, value)
        if flag:
            c.drawString(COLS["flag"], y, flag)
        c.setFont("Helvetica", 9)
        c.drawString(COLS["unit"], y - _JITTER, unit)
        for i, r in enumerate(ranges):
            c.drawString(COLS["range"], y - i * 11 + _JITTER, r)
        if method:
            c.setFont("Helvetica-Oblique", 7)
            c.drawString(COLS["name"] + indent, y - 10, f"Method : {method}")
        y -= max(len(ranges) * 11, 22 if method else 16) + 4
    c.setFont("Helvetica", 7)
    c.drawString(40, 40, "This is an electronically authenticated report. Results relate only to the sample tested.")
    c.drawRightString(555, 40, f"Page {page_no} of {pages}")
    if page_no == pages:
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(297, 70, "*** End of Report ***")
        c.drawString(420, 90, "Dr. A. Pathologist, MD (Path)")
    c.showPage()


def render_realistic_pdf(baseline_jitter: float = 0.0) -> bytes:
    """baseline_jitter: shift values/units/ranges vertically (points) - some PDF writers place each column as
    its own text box, so a row's cells don't share one baseline."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    global _JITTER
    _JITTER = baseline_jitter
    _page(c, PAGE1, 1, 2)
    _page(c, PAGE2, 2, 2)
    _JITTER = 0.0
    c.save()
    return buf.getvalue()


_JITTER = 0.0


# ---------------------------------------------------------------- how real PDFs store their text
def _rasterize(pdf: bytes, dpi: int = 200) -> list[bytes]:
    import pymupdf as fitz

    with fitz.open(stream=pdf, filetype="pdf") as doc:
        return [p.get_pixmap(dpi=dpi).tobytes("jpg", jpg_quality=85) for p in doc]  # scanners save JPEG


def scanner_pdf(text_layer: str = "garbled") -> bytes:
    """What scanner apps produce: each page is a picture, plus an invisible text layer from the scanner's own
    OCR - often poor ('garbled') or only covering the header ('header')."""
    import pymupdf as fitz

    out = fitz.open()
    for png in _rasterize(render_realistic_pdf()):
        page = out.new_page(width=595, height=842)
        page.insert_image(page.rect, stream=png)
        junk = ("Hacrnoql0bin (Hb) l3.2 g/dl l3.O - l7.O Tota1 RBC Coumt 4.S2 mi11/cumm 4.S - S.S " * 3
                if text_layer == "garbled" else "LIFECARE DIAGNOSTICS & PATHOLOGY Patient Name : Mr. Synthetic Person "
                "Age / Gender : 45 Years / Male Referred By : Dr. Self Sample ID : 24051234")
        page.insert_textbox(fitz.Rect(40, 40, 555, 200), junk, fontsize=8, render_mode=3)  # 3 = invisible
    return out.tobytes()


def hybrid_pdf() -> bytes:
    """Header/footer as real text, but the results table pasted in as a picture (some lab software does this)."""
    import pymupdf as fitz

    src = fitz.open(stream=render_realistic_pdf(), filetype="pdf")
    out = fitz.open()
    for sp in src:
        page = out.new_page(width=595, height=842)
        clip = fitz.Rect(0, 150, 595, 760)  # the table area
        page.insert_image(clip, stream=sp.get_pixmap(dpi=200, clip=clip).tobytes("jpg", jpg_quality=85))
        page.show_pdf_page(fitz.Rect(0, 0, 595, 150), src, sp.number, clip=fitz.Rect(0, 0, 595, 150))
        page.show_pdf_page(fitz.Rect(0, 760, 595, 842), src, sp.number, clip=fitz.Rect(0, 760, 595, 842))
    return out.tobytes()


def rotated_pdf() -> bytes:
    """Pages stored landscape and rotated for display - text comes out in unrotated coordinates."""
    import pymupdf as fitz

    doc = fitz.open(stream=render_realistic_pdf(), filetype="pdf")
    out = fitz.open()
    for sp in doc:
        page = out.new_page(width=842, height=595)  # stored sideways...
        page.show_pdf_page(page.rect, doc, sp.number, rotate=90)
        page.set_rotation(90)                        # ...and turned upright for viewing
    return out.tobytes()
