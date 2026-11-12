"""Launch safety: production refuses unsafe settings; API responses carry security headers."""
from app.core.config import Settings


def test_dev_defaults_are_rejected_for_production():
    s = Settings(app_env="production", _env_file=None)
    problems = " ".join(s.production_problems())
    for word in ("JWT_SECRET", "PostgreSQL", "STORAGE_BACKEND", "https://"):
        assert word in problems


def test_safe_production_settings_pass():
    s = Settings(app_env="production", _env_file=None, jwt_secret="x" * 48,
                 database_url="postgresql+psycopg://u:p@db:5432/fitscan", storage_backend="s3",
                 s3_access_key="fitscan-app", s3_secret_key="a-long-random-secret", frontend_origin="https://fitscan.example.org")
    assert s.production_problems() == []


def test_security_headers(client):
    r = client.get("/api/v1/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Cache-Control"] == "no-store"
