"""Site assistant (floating chatbot) + dashboard chart data. Synthetic fixtures only."""
import io

import pytest

from app.rag.safety_validator import validate
from tests.fixtures.synthetic_reports import LAYOUTS, render_pdf

API = "/api/v1"


def ask(client, q, **kw):
    r = client.post(f"{API}/assistant/chat", json={"question": q, **kw})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.parametrize("q,intent", [
    ("I have chest pain and can't breathe", "emergency"),
    ("How many tablets of metformin should I take?", "medicine_advice"),
    ("Do I have diabetes?", "diagnosis"),
    ("hi", "greeting"),
    ("How do I upload my report?", "upload"),
    ("Can I upload a handwritten prescription?", "prescription"),
    ("How can I download the pdf summary?", "download"),
    ("How do I compare my reports over time?", "compare"),
    ("Where is a lab near me?", "centres"),
    ("Who can see my data?", "privacy"),
    ("What does reference range mean?", "reference_range"),
])
def test_intents(member, q, intent):
    r = ask(member, q, page="/dashboard")
    assert r["intent"] == intent and r["source_tag"] == "AI_GENERATED"
    if intent != "emergency":  # fixed safety redirect, deliberately says "emergency"
        assert validate(r["answer"], "chat").ok
    assert r["suggestions"]


def test_safety_wins_over_test_names(member):
    assert ask(member, "Should I stop my thyroid tablets because my TSH is high?")["intent"] == "medicine_advice"


def test_test_question_uses_library_with_citation(member):
    r = ask(member, "What does HbA1c measure?")
    assert r["intent"] == "knowledge" and r["sources"] and "[S1]" in r["answer"]
    assert validate(r["answer"], "chat").ok


def test_off_topic_falls_back(member):
    r = ask(member, "Who won the cricket match yesterday?")
    assert r["intent"] == "fallback" and r["actions"]


def test_report_aware_and_isolated(app, member):
    from fastapi.testclient import TestClient

    client = member
    doc_id = client.post(f"{API}/documents", files={"file": ("r.pdf", io.BytesIO(render_pdf(LAYOUTS[0])), "application/pdf")},
                         data={"doc_type": "LAB_REPORT"}).json()["document_id"]
    ex = client.get(f"{API}/documents/{doc_id}/extraction").json()
    client.patch(f"{API}/documents/{doc_id}/extraction",
                 json={"parameters": [{"id": p["id"], "verified": True} for p in ex["parameters"]], "confirm": True})
    r = ask(client, "What does my hemoglobin mean?", document_id=doc_id, page="/analysis")
    assert "On your report, Hemoglobin" in r["answer"] and "below the lab's reference range" in r["answer"]
    with TestClient(app) as other:  # another account can't use my document as context
        other.post(f"{API}/auth/register", json={"email": "other-asst@example.com", "password": "s3cret-pass"})
        assert other.post(f"{API}/assistant/chat", json={"question": "hemoglobin", "document_id": doc_id}).status_code == 404

    d = client.get(f"{API}/dashboard").json()
    charts = d["charts"]
    assert charts["latest_status"]["below"] >= 1
    assert any(row["outside"] >= 1 for row in charts["by_system"])
    hb = next(t for t in charts["trends"] if t["parameter_id"] == "hemoglobin")
    assert hb["points"] and hb["ref_low"] is not None


def test_validation(member):
    assert member.post(f"{API}/assistant/chat", json={"question": ""}).status_code == 422


def test_guests_must_log_in_to_chat(client):  # log in to unlock
    r = client.post(f"{API}/assistant/chat", json={"question": "hi"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "LOGIN_TO_UNLOCK"
    assert client.post(f"{API}/assistant/explain-term", json={"term": "Hb"}).status_code == 200  # review helper stays open
