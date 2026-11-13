from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    app_env: str = "development"
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'fitscan.db').as_posix()}"
    frontend_origin: str = "http://localhost:3000"

    storage_backend: str = "local"  # local | s3 | db (files in the database; for free hosting)
    local_storage_dir: str = str(BACKEND_DIR / "storage")
    s3_endpoint_url: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_bucket: str = "fitscan-documents"
    signed_url_ttl_seconds: int = 300

    max_upload_mb: int = 15
    max_pdf_pages: int = 30
    confidence_threshold: float = 0.85

    # Admin panel (/admin): comma-separated emails of registered accounts that may open it. Empty = nobody.
    admin_emails: str = ""
    # Weekly summary email to the owners (Resend HTTP API - https://resend.com). Empty key = not sent.
    resend_api_key: str | None = None
    email_from: str = "FITSCAN <onboarding@resend.dev>"  # Resend's test sender: delivers only to your Resend account email
    weekly_summary_weekday: int = 0  # 0 = Monday (09:00 IST)

    jwt_secret: str = "dev-only-change-me"
    jwt_expire_minutes: int = 60 * 24
    guest_retention_hours: int = 24

    llm_provider: str = "anthropic"
    llm_api_key: str | None = None
    llm_model: str = "claude-opus-5-5"
    llm_effort: str = "medium"  # low | medium | high (Opus 5.5 default is medium)

    # Chatbot (site assistant + "what is this term?"): Google Gemini when a key is set, else the LLM above.
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash"
    gemini_fallback_model: str = "gemini-3.5-flash-lite"  # used when the main model is busy (503/429/timeout)

    centre_provider: str = "google"
    google_places_api_key: str | None = None

    process_inline: bool = False  # tests: run pipelines synchronously

    @field_validator("database_url")
    @classmethod
    def _psycopg_driver(cls, v: str) -> str:
        # Hosted Postgres (Neon, Supabase, Render...) hands out postgres:// URLs; SQLAlchemy needs the driver name.
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+psycopg://" + v[len(prefix):]
        return v

    @property
    def data_dir(self) -> Path:
        return BACKEND_DIR / "data"

    @property
    def config_dir(self) -> Path:
        return BACKEND_DIR / "config"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    def role_for(self, email: str | None, stored_role: str | None) -> str:
        """Effective admin-panel role: OWNER (ADMIN_EMAILS) > ADMIN (granted in the panel) > USER."""
        if self.is_admin_email(email):
            return "OWNER"
        return "ADMIN" if stored_role in ("ADMIN", "OWNER") else "USER"

    def is_admin_email(self, email: str | None) -> bool:
        admins = {e.strip().lower() for e in self.admin_emails.split(",") if e.strip()}
        return bool(email) and email.strip().lower() in admins

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def production_problems(self) -> list[str]:
        """Settings that are fine for local development but unsafe for a public launch."""
        problems = []
        if self.jwt_secret in ("dev-only-change-me", "change-me", "") or len(self.jwt_secret) < 32:
            problems.append("JWT_SECRET must be a random value of at least 32 characters")
        if self.database_url.startswith("sqlite"):
            problems.append("DATABASE_URL must point to PostgreSQL (SQLite is for local development)")
        if self.storage_backend not in ("s3", "db"):
            problems.append("STORAGE_BACKEND must be 's3' or 'db' (local files are lost when a container is replaced)")
        elif self.storage_backend == "s3" and (
                not (self.s3_access_key and self.s3_secret_key) or self.s3_secret_key in ("minioadmin", "change-me")):
            problems.append("S3_ACCESS_KEY / S3_SECRET_KEY must be set to non-default values")
        origins = [o.strip() for o in self.frontend_origin.split(",") if o.strip()]
        if not origins or any(not o.startswith("https://") for o in origins):
            problems.append("FRONTEND_ORIGIN must list only https:// origins")
        return problems


@lru_cache
def get_settings() -> Settings:
    return Settings()
