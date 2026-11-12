"""How real PDFs store their text (synthetic reports only - no patient data).

A "normal" lab PDF may be: real text (clean, or with columns on slightly different baselines), a scanner's page
images with an invisible - often poor or header-only - OCR layer, a text header over a results table pasted in
as a picture, or pages stored sideways and rotated for display. Every kind must give the same 17 results.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.pipelines.lab_report.pipeline import LabReportPipeline
from tests.fixtures import realistic_report as rr

KINDS = {
    "digital": lambda: rr.render_realistic_pdf(),
    "misaligned_columns": lambda: rr.render_realistic_pdf(baseline_jitter=4.0),
    "rotated_pages": rr.rotated_pdf,
    "scanner_garbled_text_layer": lambda: rr.scanner_pdf("garbled"),
    "scanner_header_only_text_layer": lambda: rr.scanner_pdf("header"),
    "table_pasted_as_picture": rr.hybrid_pdf,
}


@pytest.mark.parametrize("kind", KINDS)
def test_every_pdf_kind_reads_all_results(kind):
    from app.pipelines.ocr.printed_ocr import get_printed_ocr

    if kind.startswith(("scanner", "table")) and not get_printed_ocr().available:
        pytest.skip("no OCR engine installed")
    res = LabReportPipeline().run(KINDS[kind](), "application/pdf")
    got = {}
    for p in res.parameters:
        got.setdefault(p.parameter_id, p)
    wrong = [pid for pid, v, lo, hi in rr.EXPECTED
             if not ((p := got.get(pid)) and p.value_num == v and p.ref_low == lo and p.ref_high == hi)]
    assert wrong == [], f"{kind}: wrong or missing {wrong}"
    assert len(res.parameters) == len(rr.EXPECTED)  # no header/footer/interpretation text read as tests
    if res.engine == "native-text":
        assert res.metadata["patient_name"].value == "Mr. Synthetic Person"


def test_reads_cut_off_by_a_restart_are_failed_not_left_spinning(app):
    from app.core.constants import DocumentStatus
    from app.db.models import Document
    from app.db.session import SessionLocal
    from app.services.document_service import fail_interrupted

    with SessionLocal() as db:
        old = Document(doc_type="LAB_REPORT", original_filename="a.pdf", storage_key="k1", mime="application/pdf",
                       status=DocumentStatus.OCR_RUNNING, uploaded_at=datetime.now(timezone.utc) - timedelta(hours=1))
        fresh = Document(doc_type="LAB_REPORT", original_filename="b.pdf", storage_key="k2", mime="application/pdf",
                         status=DocumentStatus.OCR_RUNNING)
        db.add_all([old, fresh])
        db.commit()
        assert fail_interrupted(db) >= 1
        db.refresh(old)
        db.refresh(fresh)
        assert old.status == DocumentStatus.FAILED and "upload the report again" in old.status_message
        assert fresh.status == DocumentStatus.OCR_RUNNING  # may still be running in another worker
        db.delete(old)
        db.delete(fresh)
        db.commit()
