"""Analysis, chat, PDF, comparisons and centres through the API (BR-02, 07, 08, 10, 11, 13, 14)."""
import io

import pymupdf
import pytest

from app.core.constants import DISCLAIMER_TEXT
from app.integrations.centre_provider import Centre, GeoPoint
from app.services import centre_service
from tests.fixtures.synthetic_reports import LAYOUTS, render_pdf

API = "/api/v1"


def upload(client, data, doc_type="LAB_REPORT", name="r.pdf"):
    r = client.post(f"{API}/documents", files={"file": (name, io.BytesIO(data), "application/pdf")}, data={"doc_type": doc_type})
    assert r.status_code == 202, r.text
    return r.json()["document_id"]


def verified_doc(client, layout):
    doc_id = upload(client, render_pdf(layout))
    r = client.patch(f"{API}/documents/{doc_id}/extraction", json={"confirm": True})
    assert r.status_code == 200, r.text
    return doc_id


def test_analysis_requires_verification(client):  # BR-02
    doc_id = upload(client, render_pdf(LAYOUTS[0]))
    r = client.post(f"{API}/documents/{doc_id}/analysis")
    assert r.status_code == 409 and r.json()["error"]["code"] == "NOT_VERIFIED"


def test_analysis_verified_only_and_labelled(client):
    doc_id = upload(client, render_pdf(LAYOUTS[0]))
    ex = client.get(f"{API}/documents/{doc_id}/extraction").json()
    hb = next(p for p in ex["parameters"] if p["parameter_id"] == "hemoglobin")
    esr = next(p for p in ex["parameters"] if p["parameter_id"] == "esr")
    # verify only hemoglobin; ESR stays unverified
    client.patch(f"{API}/documents/{doc_id}/extraction", json={"parameters": [{"id": hb["id"], "verified": True}]})
    a = client.post(f"{API}/documents/{doc_id}/analysis").json()
    s = a["summary"]
    assert a["source_tag"] == "AI_GENERATED" and a["disclaimer"] == DISCLAIMER_TEXT  # BR-10, BR-13
    assert [r["parameter_id"] for r in s["parameters"]] == ["hemoglobin"]
    assert esr["id"] in [e["row_id"] for e in s["excluded"]]
    row = s["parameters"][0]
    assert row["status"] == "BELOW" and "below the lab's reference range (12.0 - 15.0)" in row["explanation"]
    assert row["explanation_source"] == "AI_GENERATED" and row["value_source"] == "EXTRACTED"
    assert a["sources"] and "[S" in row["context"]  # BR-11 citation
    assert client.get(f"{API}/documents/{doc_id}").json()["status"] == "ANALYZED"


def test_chat_citations_and_guardrails(client):
    doc_id = verified_doc(client, LAYOUTS[0])
    m = client.post(f"{API}/documents/{doc_id}/chat", json={"question": "What does hemoglobin measure?"}).json()
    assert m["role"] == "assistant" and "[S1]" in m["content"] and m["sources"]          # BR-11
    assert "11.2" in m["content"]
    bait = client.post(f"{API}/documents/{doc_id}/chat", json={"question": "Should I take iron tablets? What dose?"}).json()
    assert "can't give advice" in bait["content"] and not bait["sources"]
    dx = client.post(f"{API}/documents/{doc_id}/chat", json={"question": "Do I have anemia?"}).json()
    assert "only a doctor can make a diagnosis" in dx["content"]
    nosrc = client.post(f"{API}/documents/{doc_id}/chat", json={"question": "zxqv wplk?"}).json()
    assert "couldn't find a source" in nosrc["content"]                                   # BR-11 fallback
    assert len(client.get(f"{API}/documents/{doc_id}/chat").json()) == 8


def test_pdf_summary_has_disclaimer_and_labels(client):  # FR-AI-8, BR-13, BR-10
    doc_id = verified_doc(client, LAYOUTS[1])
    assert client.get(f"{API}/documents/{doc_id}/summary.pdf").status_code == 404
    client.post(f"{API}/documents/{doc_id}/analysis")
    r = client.get(f"{API}/documents/{doc_id}/summary.pdf")
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    with pymupdf.open(stream=r.content, filetype="pdf") as pdf:
        pages = [p.get_text() for p in pdf]
    text = " ".join(" ".join(pages).split())
    assert "does not diagnose conditions" in text
    assert all("Always consult your doctor" in " ".join(p.split()) for p in pages)  # on every page
    assert "AI-GENERATED" in text and "EXTRACTED" in text and "Sources" in text


def test_comparison_api(client):
    a = verified_doc(client, LAYOUTS[2])
    # second lipid report later with changed values (built by editing a copy)
    b = upload(client, render_pdf(LAYOUTS[2]))
    ex = client.get(f"{API}/documents/{b}/extraction").json()
    ldl = next(p for p in ex["parameters"] if p["parameter_id"] == "ldl")
    client.patch(f"{API}/documents/{b}/extraction", json={"parameters": [{"id": ldl["id"], "value_raw": "98"}],
                                                          "metadata": {"report_date": "2024-07-10"}, "confirm": True})
    r = client.post(f"{API}/comparisons", json={"document_ids": [b, a]})
    assert r.status_code == 201, r.text
    res = r.json()["result"]
    c = next(x for x in res["compared"] if x["parameter_id"] == "ldl")
    assert c["previous"]["value"] == 146 and c["current"]["value"] == 98 and c["absolute_change"] == -48
    assert c["transition"] == "NEWLY_INSIDE_RANGE"
    assert res["summary"]["source_tag"] == "AI_GENERATED"
    assert client.post(f"{API}/comparisons", json={"document_ids": [a]}).status_code == 422


class FakeProvider:
    name = "fake"

    def geocode(self, q):
        return GeoPoint(lat=18.52, lng=73.85, label=q)

    def search(self, tests, origin, radius, label):
        return [Centre(provider_id="1", name="Alpha Diagnostics Lab", lat=18.521, lng=73.851, phone="020", address="Pune"),
                Centre(provider_id="2", name="Beta Hospital", lat=18.53, lng=73.86)]

    def search_doctors(self, doctor, origin, radius, label):
        return [Centre(provider_id="d1", name="Gamma Heart Clinic", lat=18.522, lng=73.852, kind="doctor")]


@pytest.fixture()
def fake_provider():
    centre_service.set_provider(FakeProvider())
    yield
    centre_service.set_provider(None)


def test_centre_search_flow(client, fake_provider):  # BR-06, BR-07, BR-12; log in to unlock
    """Users search for tests they pick themselves, or for any diagnostic centre."""
    r = client.post(f"{API}/centres/search", json={"city": "Pune"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "LOGIN_TO_UNLOCK"   # guests: log in to unlock
    assert client.get(f"{API}/centres/location").status_code == 401
    client.post(f"{API}/auth/register", json={"email": "centres@example.com", "password": "s3cret-pass"})
    assert client.post(f"{API}/centres/search", json={"test_names": ["CBC"]}).status_code == 422  # location required
    r = client.post(f"{API}/centres/search", json={"test_names": ["Complete Blood Count"], "city": "Pune", "radius_km": 5})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["tests"] == ["Complete Blood Count"]
    assert body["results"][0]["centre"]["name"] == "Alpha Diagnostics Lab"
    assert all(x["verified"] is False for x in body["results"])                       # BR-12 (not adequately sourced)
    assert "do not guarantee" in body["disclaimer"]
    r = client.post(f"{API}/centres/search", json={"city": "Pune"})
    assert r.status_code == 200 and r.json()["tests"] == [] and r.json()["doctor_type"] is None

    # Optional type of doctor: alone -> only doctors; with tests -> doctors and labs.
    r = client.post(f"{API}/centres/search", json={"city": "Pune", "doctor_type": "CARDIOLOGIST"})
    body = r.json()
    assert r.status_code == 200 and body["doctor_type"] == "CARDIOLOGIST"
    assert [x["centre"]["kind"] for x in body["results"]] == ["doctor"]
    assert body["results"][0]["test_availability"].startswith("Cardiologist")
    r = client.post(f"{API}/centres/search", json={"city": "Pune", "doctor_type": "CARDIOLOGIST", "test_names": ["Lipid Profile"]})
    assert {x["centre"]["kind"] for x in r.json()["results"]} == {"doctor", "lab"}
    assert client.post(f"{API}/centres/search", json={"city": "Pune", "doctor_type": "WIZARD"}).status_code == 422

    upload(client, render_pdf(LAYOUTS[0]))  # the report prints the LAB's address - never used as the user's (BR-06)
    loc = client.get(f"{API}/centres/location").json()
    assert loc["source"] is None and loc["locality"] is None
