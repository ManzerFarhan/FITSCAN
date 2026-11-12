"""Auth, guest migration, per-user isolation, privacy & retention (FR-PROF-4..6, NFR-04, BR-14, BR-15)."""
import io
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from tests.fixtures.synthetic_reports import LAYOUTS, render_pdf

API = "/api/v1"


def upload(client, layout=0, url="/documents", **form):
    return client.post(f"{API}{url}", files={"file": ("r.pdf", io.BytesIO(render_pdf(LAYOUTS[layout])), "application/pdf")},
                       data={"doc_type": "LAB_REPORT", **form})


def test_dashboard_health_score_and_optional_bmi(client):
    doc_id = upload(client).json()["document_id"]
    d = client.get(f"{API}/dashboard").json()
    assert d["health_score"] is None and d["bmi"] is None  # guests: log in to unlock
    client.post(f"{API}/auth/register", json={"email": "bmi@example.com", "password": "s3cret-pass"})
    assert client.get(f"{API}/dashboard").json()["health_score"]["available"] is False  # nothing confirmed yet
    client.patch(f"{API}/documents/{doc_id}/extraction", json={"confirm": True})
    hs = client.get(f"{API}/dashboard").json()["health_score"]
    assert hs["available"] and 0 <= hs["score"] <= 10 and hs["out_of"] == 10 and hs["document_id"] == doc_id

    assert client.patch(f"{API}/profile", json={"height_cm": 20, "weight_kg": 70}).status_code == 422
    me = client.patch(f"{API}/profile", json={"height_cm": 170, "weight_kg": 65}).json()
    assert me["height_cm"] == 170 and me["weight_kg"] == 65
    assert client.get(f"{API}/dashboard").json()["bmi"] == {"value": 22.5, "category": "NORMAL", "height_cm": 170, "weight_kg": 65}
    client.patch(f"{API}/profile", json={"height_cm": None, "weight_kg": None})  # optional: can be removed
    assert client.get(f"{API}/dashboard").json()["bmi"] is None


def test_register_migrates_guest_documents(client):
    doc_id = upload(client).json()["document_id"]
    r = client.post(f"{API}/auth/register", json={"email": "Alice@Example.com", "password": "s3cret-pass", "full_name": "Alice"})
    assert r.status_code == 201, r.text
    assert r.json()["migrated_documents"] == 1
    me = client.get(f"{API}/auth/me").json()
    assert me["authenticated"] and me["user"]["email"] == "alice@example.com"
    assert client.get(f"{API}/documents/{doc_id}").status_code == 200
    assert client.get(f"{API}/dashboard").json()["user"]["full_name"] == "Alice"
    assert client.post(f"{API}/auth/register", json={"email": "alice@example.com", "password": "another-pass"}).status_code == 409


def test_login_logout_and_user_isolation(app):  # NFR-04
    with TestClient(app) as a, TestClient(app) as b:
        a.post(f"{API}/auth/register", json={"email": "u1@example.com", "password": "password-1"})
        b.post(f"{API}/auth/register", json={"email": "u2@example.com", "password": "password-2"})
        doc = upload(a).json()["document_id"]
        assert b.get(f"{API}/documents/{doc}").status_code == 404
        assert b.get(f"{API}/documents/{doc}/extraction").status_code == 404
        assert b.patch(f"{API}/documents/{doc}/extraction", json={"confirm": True}).status_code == 404
        assert b.post(f"{API}/documents/{doc}/analysis").status_code == 404
        assert b.post(f"{API}/comparisons", json={"document_ids": [doc, doc]}).status_code in (404, 422)
        assert b.get(f"{API}/documents").json()["total"] == 0
        a.post(f"{API}/auth/logout")
        assert a.get(f"{API}/auth/me").json()["authenticated"] is False
        assert a.get(f"{API}/documents/{doc}").status_code == 404  # now a fresh guest
        assert a.post(f"{API}/auth/login", json={"email": "u1@example.com", "password": "wrong"}).status_code == 401
        assert a.post(f"{API}/auth/login", json={"email": "u1@example.com", "password": "password-1"}).status_code == 200
        assert a.get(f"{API}/documents/{doc}").status_code == 200


def test_profile_and_historical_upload(client):
    assert client.get(f"{API}/profile").status_code == 401
    assert upload(client, url="/profile/historical-documents").status_code == 401
    client.post(f"{API}/auth/register", json={"email": "p@example.com", "password": "password-p"})
    p = client.patch(f"{API}/profile", json={"preferred_city": "Pune", "gender": "Female", "dob": "1990-05-01"}).json()
    assert p["preferred_city"] == "Pune"
    assert client.patch(f"{API}/profile", json={"email": "new@example.com"}).status_code == 401
    r = upload(client, 5, "/profile/historical-documents", report_date="2023-01-15", description="old report")
    assert r.status_code == 202
    d = client.get(f"{API}/documents/{r.json()['document_id']}").json()
    assert d["report_date"] == "2023-01-15"            # BR-14: user-supplied actual date kept
    assert d["uploaded_at"][:4] >= "2026" or d["uploaded_at"][:4] >= "2025"
    assert upload(client, 0, "/profile/historical-documents", report_date="2999-01-01").status_code == 422
    assert client.get(f"{API}/profile/records").json()["lab_reports"] == 1


def test_report_date_required_to_confirm(client):  # BR-14
    doc = upload(client, 0).json()["document_id"]
    client.patch(f"{API}/documents/{doc}/extraction", json={"metadata": {"report_date": None}})
    r = client.patch(f"{API}/documents/{doc}/extraction", json={"confirm": True})
    assert r.status_code == 409 and r.json()["error"]["code"] == "REPORT_DATE_REQUIRED"


def test_password_reset_and_change_invalidate_sessions(app):
    with TestClient(app) as c:
        c.post(f"{API}/auth/register", json={"email": "r@example.com", "password": "old-password"})
        token = c.post(f"{API}/auth/reset-password", json={"email": "r@example.com"}).json()["dev_reset_token"]
        unknown = c.post(f"{API}/auth/reset-password", json={"email": "nobody@example.com"}).json()
        assert "dev_reset_token" not in unknown  # no account enumeration signal in the message
        assert c.post(f"{API}/auth/reset-password/confirm", json={"token": token, "new_password": "new-password"}).status_code == 200
        assert c.post(f"{API}/auth/reset-password/confirm", json={"token": token, "new_password": "again-pass"}).status_code == 400
        assert c.get(f"{API}/auth/me").json()["authenticated"] is False  # old session token invalid
        assert c.post(f"{API}/auth/login", json={"email": "r@example.com", "password": "new-password"}).status_code == 200


def test_delete_account_removes_data(app):
    with TestClient(app) as c:
        c.post(f"{API}/auth/register", json={"email": "d@example.com", "password": "delete-me-1"})
        doc = upload(c).json()["document_id"]
        assert c.request("DELETE", f"{API}/profile", json={"password": "nope"}).status_code == 401
        assert c.request("DELETE", f"{API}/profile", json={"password": "delete-me-1"}).status_code == 204
        assert c.post(f"{API}/auth/login", json={"email": "d@example.com", "password": "delete-me-1"}).status_code == 401
    from app.db.models import Document
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        assert db.get(Document, __import__("uuid").UUID(doc)) is None


def test_guest_retention_cleanup(app):  # BR-15
    from app.db.models import Document, GuestSession
    from app.db.session import SessionLocal
    from app.services.retention_service import cleanup

    with TestClient(app) as g:
        doc = upload(g).json()["document_id"]
    with SessionLocal() as db:
        cleanup(db, now=datetime.now(timezone.utc) + timedelta(hours=1))
        assert db.get(Document, __import__("uuid").UUID(doc)) is not None  # not expired yet
        cleanup(db, now=datetime.now(timezone.utc) + timedelta(hours=25))
        assert db.get(Document, __import__("uuid").UUID(doc)) is None
        assert db.query(GuestSession).count() == 0


def test_rate_limit_on_login(client):
    codes = [client.post(f"{API}/auth/login", json={"email": "x@example.com", "password": "x"}).status_code for _ in range(12)]
    assert codes[-1] == 429 and codes[0] == 401
