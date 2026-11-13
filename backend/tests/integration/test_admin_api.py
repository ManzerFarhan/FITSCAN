"""Admin panel API (FR-ADM): roles, clients, admin team, suspension, reports, audit. Synthetic data only."""
import uuid

import pytest
from fastapi.testclient import TestClient

from tests.fixtures.synthetic_reports import LAYOUTS, render_pdf
from tests.integration.test_documents_api import upload

API = "/api/v1"
PW = "s3cret-pass"


@pytest.fixture()
def owner_email(monkeypatch):
    from app.core.config import get_settings

    email = f"owner-{uuid.uuid4().hex[:8]}@example.com"
    monkeypatch.setattr(get_settings(), "admin_emails", f"someone@example.com, {email.upper()}")
    return email


def _register(c, email, **extra):
    r = c.post(f"{API}/auth/register", json={"email": email, "password": PW, **extra})
    assert r.status_code == 201, r.text
    return r.json()["user"]


def _email(tag="c"):
    return f"{tag}-{uuid.uuid4().hex[:8]}@example.com"


def test_admin_access_is_limited(app, owner_email):
    with TestClient(app) as guest, TestClient(app) as member, TestClient(app) as owner:
        assert guest.get(f"{API}/admin/overview").status_code == 401
        assert _register(member, _email("m"))["is_admin"] is False
        assert member.get(f"{API}/admin/users").status_code == 403
        me = _register(owner, owner_email)
        assert me["is_admin"] is True and me["admin_role"] == "OWNER"
        ov = owner.get(f"{API}/admin/overview").json()
        assert len(ov["signups_daily"]) == 30 and "read_success_rate" in ov
        assert owner.get(f"{API}/admin/system").json()["tests_in_dictionary"] >= 450


def test_clients_reports_and_audit(app, owner_email):
    tag = uuid.uuid4().hex[:8]
    with TestClient(app) as client, TestClient(app) as owner:
        user = _register(client, f"client-{tag}@example.com", full_name=f"Test Client {tag}")
        doc_id = upload(client, render_pdf(LAYOUTS[0])).json()["document_id"]
        _register(owner, owner_email)

        found = owner.get(f"{API}/admin/users", params={"q": tag}).json()
        assert found["total"] == 1 and found["items"][0]["documents"] == 1 and "password_hash" not in found["items"][0]
        assert owner.get(f"{API}/admin/users", params={"status": "suspended", "q": tag}).json()["total"] == 0

        detail = owner.get(f"{API}/admin/users/{user['id']}").json()
        assert detail["documents"][0]["parameters"] == 6 and detail["user"]["last_login_at"]

        doc = owner.get(f"{API}/admin/documents/{doc_id}").json()
        assert doc["owner"] == f"client-{tag}@example.com" and doc["parameters"] == 6 and len(doc["results"]) == 6
        assert owner.get(f"{API}/admin/documents/{doc_id}/file").content[:4] == b"%PDF"
        assert owner.post(f"{API}/admin/documents/{doc_id}/reprocess").status_code == 202
        assert owner.get(f"{API}/admin/documents", params={"q": tag}).json()["total"] == 1

        csv = owner.get(f"{API}/admin/users.csv", params={"q": tag})
        assert csv.headers["content-type"].startswith("text/csv") and f"client-{tag}@example.com" in csv.text

        log = owner.get(f"{API}/admin/audit", params={"action": "ADMIN_VIEW"}).json()
        assert log["total"] >= 2 and "ADMIN_EXPORT" in log["actions"]

        assert owner.delete(f"{API}/admin/documents/{doc_id}").status_code == 204
        assert owner.get(f"{API}/admin/documents/{doc_id}").status_code == 404
        assert owner.get(f"{API}/admin/users/{uuid.uuid4()}").status_code == 404


def test_suspend_reset_and_delete_client(app, owner_email):
    email = _email()
    with TestClient(app) as client, TestClient(app) as owner:
        user = _register(client, email)
        _register(owner, owner_email)
        assert owner.post(f"{API}/admin/users/{user['id']}/suspend").status_code == 200
        assert client.get(f"{API}/auth/me").json()["authenticated"] is False  # signed out at once
        r = client.post(f"{API}/auth/login", json={"email": email, "password": PW})
        assert r.status_code == 403 and r.json()["error"]["code"] == "ACCOUNT_DISABLED"
        owner.post(f"{API}/admin/users/{user['id']}/reactivate")
        temp = owner.post(f"{API}/admin/users/{user['id']}/reset-password").json()["temporary_password"]
        assert client.post(f"{API}/auth/login", json={"email": email, "password": temp}).status_code == 200
        assert owner.delete(f"{API}/admin/users/{user['id']}").status_code == 204
        assert owner.get(f"{API}/admin/users/{user['id']}").status_code == 404


def test_owner_manages_admin_team(app, owner_email):
    new_admin = _email("adm")
    with TestClient(app) as owner, TestClient(app) as adm:
        me = _register(owner, owner_email)
        assert owner.post(f"{API}/admin/admins", json={"email": new_admin}).status_code == 404  # needs a password
        r = owner.post(f"{API}/admin/admins", json={"email": new_admin, "password": "admin-pass-1", "full_name": "New Admin"})
        assert r.status_code == 201 and r.json()["created"] is True
        assert any(a["email"] == new_admin for a in owner.get(f"{API}/admin/admins").json())

        s = adm.post(f"{API}/auth/login", json={"email": new_admin, "password": "admin-pass-1"}).json()
        assert s["user"]["admin_role"] == "ADMIN"
        assert adm.get(f"{API}/admin/users").status_code == 200          # admins can view
        assert adm.post(f"{API}/admin/admins", json={"email": _email()}).status_code == 403  # only the owner manages admins
        assert adm.delete(f"{API}/admin/users/{me['id']}").status_code == 403
        assert adm.post(f"{API}/admin/users/{me['id']}/suspend").status_code == 403    # owner can't be suspended

        assert owner.delete(f"{API}/admin/admins/{me['id']}").status_code == 403       # owner can't be removed
        assert owner.delete(f"{API}/admin/admins/{s['user']['id']}").status_code == 204
        assert adm.get(f"{API}/admin/users").status_code == 403
