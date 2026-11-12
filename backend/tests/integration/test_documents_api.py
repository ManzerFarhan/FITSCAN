"""Upload -> extract -> verify flow, isolation, validation (API-01..05, 10, 11, 12; NFR-04; BR-02/03/08/14)."""
import io

from fastapi.testclient import TestClient

from tests.fixtures.synthetic_reports import LAYOUTS, render_pdf

API = "/api/v1"


def upload(client, data: bytes, name="report.pdf", doc_type="LAB_REPORT", **form):
    return client.post(f"{API}/documents", files={"file": (name, io.BytesIO(data), "application/pdf")},
                       data={"doc_type": doc_type, **form})


def test_health(client):
    r = client.get(f"{API}/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_upload_and_extract_lab_report(client):
    r = upload(client, render_pdf(LAYOUTS[0]))
    assert r.status_code == 202, r.text
    doc_id = r.json()["document_id"]

    doc = client.get(f"{API}/documents/{doc_id}").json()
    assert doc["status"] in ("EXTRACTED", "NEEDS_VERIFICATION")
    assert doc["lab_name"] == "APEX DIAGNOSTICS LABORATORY"
    assert doc["report_date"] == "2024-02-04"       # BR-14: actual report date
    assert doc["uploaded_at"].startswith("20")      # ...kept separate from upload time
    assert doc["parameter_count"] == 6

    ex = client.get(f"{API}/documents/{doc_id}/extraction").json()
    hb = next(p for p in ex["parameters"] if p["parameter_id"] == "hemoglobin")
    assert hb["status"] == "BELOW" and hb["finding_class"] == "OUT_OF_RANGE" and hb["source_tag"] == "EXTRACTED"

    # page preview renders
    assert client.get(f"{API}/documents/{doc_id}/pages/1.png").headers["content-type"] == "image/png"


def test_correction_and_confirm(client):
    doc_id = upload(client, render_pdf(LAYOUTS[1])).json()["document_id"]
    ex = client.get(f"{API}/documents/{doc_id}/extraction").json()
    alb = next(p for p in ex["parameters"] if p["parameter_id"] == "albumin")
    r = client.patch(f"{API}/documents/{doc_id}/extraction", json={
        "parameters": [{"id": alb["id"], "value_raw": "3.1"}],
        "new_parameters": [{"name_raw": "Total Protein", "value_raw": "6.8", "unit": "g/dL", "ref_raw": "6.4 - 8.3"}],
        "metadata": {"report_date": "2024-03-17"},
    })
    assert r.status_code == 200, r.text
    ex = r.json()
    alb = next(p for p in ex["parameters"] if p["id"] == alb["id"])
    assert alb["value_num"] == 3.1 and alb["status"] == "BELOW"
    assert alb["source_tag"] == "USER_CORRECTED" and alb["verified"]
    assert any(p["parameter_id"] == "total_protein" for p in ex["parameters"])
    assert ex["document"]["report_date"] == "2024-03-17"

    r = client.patch(f"{API}/documents/{doc_id}/extraction", json={"confirm": True})
    assert r.status_code == 200, r.text
    assert r.json()["document"]["status"] == "VERIFIED"
    assert all(p["verified"] for p in r.json()["parameters"])


def test_confirm_blocked_until_flagged_values_checked(client):  # BR-02
    doc_id = upload(client, render_pdf(LAYOUTS[0])).json()["document_id"]
    ex = client.get(f"{API}/documents/{doc_id}/extraction").json()
    hb = next(p for p in ex["parameters"] if p["parameter_id"] == "hemoglobin")
    # Simulate an OCR slip: 112 instead of 11.2 -> implausible -> must be checked
    client.patch(f"{API}/documents/{doc_id}/extraction", json={"parameters": [{"id": hb["id"], "value_raw": "112", "verified": False}]})
    r = client.patch(f"{API}/documents/{doc_id}/extraction", json={"confirm": True})
    assert r.status_code == 409 and r.json()["error"]["code"] == "PENDING_VERIFICATION"
    assert hb["id"] in r.json()["error"]["details"]["parameter_ids"]
    r = client.patch(f"{API}/documents/{doc_id}/extraction", json={"parameters": [{"id": hb["id"], "value_raw": "11.2"}], "confirm": True})
    assert r.status_code == 200


def test_validation_errors(client):
    r = client.post(f"{API}/documents", files={"file": ("x.txt", io.BytesIO(b"hello"), "text/plain")}, data={"doc_type": "LAB_REPORT"})
    assert r.status_code == 415 and r.json()["error"]["code"] == "UNSUPPORTED_FORMAT"
    # disguised file: .pdf extension, non-PDF bytes
    r = client.post(f"{API}/documents", files={"file": ("x.pdf", io.BytesIO(b"\x89PNG\r\n\x1a\nxxxx"), "application/pdf")}, data={"doc_type": "LAB_REPORT"})
    assert r.status_code == 415
    r = client.post(f"{API}/documents", files={"file": ("x.pdf", io.BytesIO(render_pdf(LAYOUTS[0])), "application/pdf")}, data={"doc_type": "BOGUS"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_isolation_between_guests(app, client):  # NFR-04
    doc_id = upload(client, render_pdf(LAYOUTS[2])).json()["document_id"]
    with TestClient(app) as other:
        assert other.get(f"{API}/documents/{doc_id}").status_code == 404
        assert other.get(f"{API}/documents/{doc_id}/file").status_code == 404
        assert other.delete(f"{API}/documents/{doc_id}").status_code == 404
        assert other.get(f"{API}/documents").json()["total"] == 0
    assert client.get(f"{API}/documents/{doc_id}").status_code == 200


def test_history_filters_and_delete(client):
    a = upload(client, render_pdf(LAYOUTS[2])).json()["document_id"]
    upload(client, render_pdf(LAYOUTS[3]))
    lst = client.get(f"{API}/documents", params={"category": "LIPID"}).json()
    assert [d["id"] for d in lst["items"]] == [a]
    assert client.get(f"{API}/documents", params={"q": "CityCare"}).json()["total"] == 1
    assert client.get(f"{API}/documents", params={"from": "2024-04-01"}).json()["total"] == 1
    assert client.delete(f"{API}/documents/{a}").status_code == 204
    assert client.get(f"{API}/documents/{a}").status_code == 404


def test_dashboard(client):
    upload(client, render_pdf(LAYOUTS[0]))
    d = client.get(f"{API}/dashboard").json()
    assert d["user"]["is_guest"] is True
    assert d["cards"]["total_reports"] >= 1
    assert d["latest_report"]["lab_name"] == "APEX DIAGNOSTICS LABORATORY"
    classes = {f["finding_class"] for f in d["important_findings"]}
    assert "URGENT" not in classes  # nothing in this report crosses an escalation rule (BR-05)
    assert "health_score" in d and "charts" in d
