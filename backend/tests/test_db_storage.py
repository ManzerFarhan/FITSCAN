"""STORAGE_BACKEND=db keeps uploaded files in the database (free hosting without object storage)."""
import pytest


def test_database_storage_round_trip(app):
    from app.services.storage import DatabaseStorage

    store = DatabaseStorage()
    store.put("guest/abc/report.pdf", b"%PDF-1.4 synthetic", "application/pdf")
    assert store.get("guest/abc/report.pdf") == b"%PDF-1.4 synthetic"
    store.put("guest/abc/report.pdf", b"replaced", "application/pdf")  # same key overwrites
    assert store.get("guest/abc/report.pdf") == b"replaced"
    assert store.signed_url("guest/abc/report.pdf") is None  # API streams the bytes itself
    store.delete("guest/abc/report.pdf")
    with pytest.raises(FileNotFoundError):
        store.get("guest/abc/report.pdf")
    store.delete("guest/abc/report.pdf")  # deleting twice is fine


def test_db_storage_is_allowed_in_production():
    from app.core.config import Settings

    s = Settings(app_env="production", jwt_secret="x" * 40, database_url="postgresql+psycopg://u:p@h/d",
                 storage_backend="db", frontend_origin="https://fitscan.vercel.app")
    assert s.production_problems() == []


def test_hosted_postgres_url_gets_psycopg_driver():
    from app.core.config import Settings

    for url in ("postgres://u:p@ep-x.neon.tech/db?sslmode=require", "postgresql://u:p@ep-x.neon.tech/db?sslmode=require"):
        assert Settings(database_url=url).database_url == "postgresql+psycopg://u:p@ep-x.neon.tech/db?sslmode=require"
