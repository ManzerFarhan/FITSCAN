"""Admin panel API: only ADMIN_EMAILS accounts; client list, search, details, reports. Synthetic data only."""
import uuid

import pytest
from fastapi.testclient import TestClient

from tests.fixtures.synthetic_reports import LAYOUTS, render_pdf
from tests.integration.test_documents_api import upload

API = "/api/v1"


@pytest.fixture()
def admin_email(monkeypatch):
    from app.core.config import get_settings

    email = f"admin-{uuid.uuid4().hex[:8]}@example.com"
    monkeypatch.setattr(get_settings(), "admin_emails", f"someone@example.com, {email.upper()}")
    return email


def _register(c, email, **extra):
    r = c.post(f"{API}/auth/register", json={"email": email, "password": "s3cret-pass", **extra})
    assert r.status_code == 201, r.text
    return r.json()["user"]


def test_admin_access_is_limited(app, admin_email):
    with TestClient(app) as guest, TestClient(app) as member, TestClient(app) as admin:
        assert guest.get(f"{API}/admin/overview").status_code == 401
        assert _register(member, f"m-{uuid.uuid4().hex[:8]}@example.com")["is_admin"] is False
        assert member.get(f"{API}/admin/users").status_code == 403
        assert _register(admin, admin_email)["is_admin"] is True
        assert admin.get(f"{API}/auth/me").json()["user"]["is_admin"] is True
        assert admin.get(f"{API}/admin/overview").status_code == 200


def test_admin_sees_clients_and_their_reports(app, admin_email):
    tag = uuid.uuid4().hex[:8]
    with TestClient(app) as client, TestClient(app) as admin:
        user = _register(client, f"client-{tag}@example.com", full_name=f"Test Client {tag}")
        assert upload(client, render_pdf(LAYOUTS[0])).status_code == 202
        _register(admin, admin_email)

        ov = admin.get(f"{API}/admin/overview").json()
        assert ov["users"] >= 2 and ov["documents"] >= 1 and "by_status" in ov

        found = admin.get(f"{API}/admin/users", params={"q": tag}).json()
        assert found["total"] == 1
        row = found["items"][0]
        assert row["email"] == f"client-{tag}@example.com" and row["documents"] == 1 and "password_hash" not in row

        detail = admin.get(f"{API}/admin/users/{user['id']}").json()
        doc = detail["documents"][0]
        assert doc["status"] in ("EXTRACTED", "NEEDS_VERIFICATION") and doc["parameters"] == 6
        assert any(a["action"] == "UPLOAD" or a["action"] == "REGISTER" for a in detail["activity"])

        docs = admin.get(f"{API}/admin/documents").json()
        assert any(d["owner"] == f"client-{tag}@example.com" for d in docs)
        assert admin.get(f"{API}/admin/users/{uuid.uuid4()}").status_code == 404
