"""Auto-check & confirm: plausible flagged values are accepted, doubtful ones are left out of the analysis (BR-02)."""
import io
import uuid

from app.db.models import Parameter
from app.db.session import SessionLocal
from tests.fixtures.synthetic_reports import LAYOUTS, render_pdf

API = "/api/v1"


def _flag(param_id: str, **fields):
    """Simulate what a blurry scan produces: an unverified, low-confidence (or otherwise flagged) reading."""
    with SessionLocal() as db:
        p = db.get(Parameter, uuid.UUID(param_id))
        for k, v in {"verified": False, **fields}.items():
            setattr(p, k, v)
        db.commit()


def test_auto_check_accepts_plausible_and_excludes_doubtful(client):
    doc_id = client.post(f"{API}/documents", files={"file": ("r.pdf", io.BytesIO(render_pdf(LAYOUTS[0])), "application/pdf")},
                         data={"doc_type": "LAB_REPORT"}).json()["document_id"]
    ex = client.get(f"{API}/documents/{doc_id}/extraction").json()
    by = {p["parameter_id"]: p for p in ex["parameters"]}
    _flag(by["mcv"]["id"], confidence=0.7)                                       # fine, just read with low confidence
    _flag(by["esr"]["id"], confidence=0.7, issues=["IMPLAUSIBLE_VALUE"])        # must not be trusted automatically

    # Normal confirm still refuses while values are flagged...
    r = client.patch(f"{API}/documents/{doc_id}/extraction", json={"confirm": True})
    assert r.status_code == 409 and r.json()["error"]["code"] == "PENDING_VERIFICATION"

    # ...auto-check confirms, accepting the plausible value and leaving the doubtful one out.
    r = client.patch(f"{API}/documents/{doc_id}/extraction", json={"confirm": True, "auto_check": True})
    assert r.status_code == 200, r.text
    out = {p["parameter_id"]: p for p in r.json()["parameters"]}
    assert r.json()["document"]["status"] == "VERIFIED"
    assert out["mcv"]["verified"] is True
    assert out["esr"]["verified"] is False and out["esr"]["needs_verification"]

    a = client.post(f"{API}/documents/{doc_id}/analysis").json()
    assert "ESR" in [e["name"] for e in a["summary"]["excluded"]]                # listed, never analysed
    assert all(row["parameter_id"] != "esr" for row in a["summary"]["parameters"])


def test_auto_check_matches_clear_names(client):
    doc_id = client.post(f"{API}/documents", files={"file": ("r.pdf", io.BytesIO(render_pdf(LAYOUTS[0])), "application/pdf")},
                         data={"doc_type": "LAB_REPORT"}).json()["document_id"]
    ex = client.get(f"{API}/documents/{doc_id}/extraction").json()
    hb = next(p for p in ex["parameters"] if p["parameter_id"] == "hemoglobin")
    # Abbreviated label the dictionary only knows in full form ("Abs ... Cnt") - one clear match.
    _flag(hb["id"], parameter_id=None, name_raw="Abs Neutrophil Cnt", issues=["UNRECOGNIZED_PARAMETER"], confidence=0.5)
    r = client.patch(f"{API}/documents/{doc_id}/extraction", json={"confirm": True, "auto_check": True})
    p = next(x for x in r.json()["parameters"] if x["id"] == hb["id"])
    assert p["parameter_id"] == "neutrophils_abs"
    assert p["verified"] is False  # matched, but read confidence was too low to trust the value automatically


def test_unclear_names_are_never_auto_renamed(client):
    doc_id = client.post(f"{API}/documents", files={"file": ("r.pdf", io.BytesIO(render_pdf(LAYOUTS[0])), "application/pdf")},
                         data={"doc_type": "LAB_REPORT"}).json()["document_id"]
    ex = client.get(f"{API}/documents/{doc_id}/extraction").json()
    hb = next(p for p in ex["parameters"] if p["parameter_id"] == "hemoglobin")
    _flag(hb["id"], parameter_id=None, name_raw="Haemoglobln Level", issues=["UNRECOGNIZED_PARAMETER"], confidence=0.9)
    r = client.patch(f"{API}/documents/{doc_id}/extraction", json={"confirm": True, "auto_check": True})
    p = next(x for x in r.json()["parameters"] if x["id"] == hb["id"])
    assert p["parameter_id"] is None and p["verified"] is False  # below the 95 % bar -> left for the user
