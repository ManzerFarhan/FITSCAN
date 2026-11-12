"""Test setup: isolated SQLite DB + temp storage, synchronous processing. Synthetic data only."""
import os
import sys
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="fitscan-test-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ["LOCAL_STORAGE_DIR"] = str(_TMP / "storage")
os.environ["STORAGE_BACKEND"] = "local"
os.environ["PROCESS_INLINE"] = "true"
os.environ["LLM_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["GOOGLE_PLACES_API_KEY"] = ""
os.environ["JWT_SECRET"] = "test-secret"
os.environ["LLM_PROVIDER"] = "none"  # never call a real LLM from tests
os.environ.pop("ANTHROPIC_API_KEY", None)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def app():
    from app.db.base import Base
    from app.db.session import engine
    from app.main import app as fastapi_app

    Base.metadata.create_all(engine)
    return fastapi_app


@pytest.fixture(autouse=True)
def _reset_limits():
    from app.core.security import reset_rate_limits

    reset_rate_limits()
    yield


@pytest.fixture()
def client(app):
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def member(client):
    """A logged-in client - for 'log in to unlock' features (assistant, Tests & Centres, health score)."""
    import uuid

    r = client.post("/api/v1/auth/register", json={"email": f"m-{uuid.uuid4().hex[:10]}@example.com",
                                                   "password": "s3cret-pass"})
    assert r.status_code == 201, r.text
    return client
