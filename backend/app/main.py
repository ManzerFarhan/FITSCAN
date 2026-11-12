"""FITSCAN API entry point."""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import setup_logging

settings = get_settings()


async def _retention_loop() -> None:
    """BR-15: hourly guest/retention cleanup (cron via scripts/cleanup_guests.py also works)."""
    from app.db.session import SessionLocal
    from app.services.retention_service import cleanup

    def run_once():
        with SessionLocal() as db:
            cleanup(db)

    while True:
        try:
            await asyncio.to_thread(run_once)
        except Exception:  # keep the loop alive, but never fail silently - retention is a privacy promise (BR-15)
            logging.getLogger("fitscan.retention").exception("Retention cleanup failed")
        await asyncio.sleep(3600)


def _warm_ocr() -> None:
    try:
        import numpy as np

        from app.pipelines.ocr.printed_ocr import get_printed_ocr

        ocr = get_printed_ocr()
        if ocr.available:
            # Page-shaped: RapidOCR upscales the short side to 736 px, so a thin strip (e.g. 64x256 -> 736x2944)
            # would cost more memory than a real page (~560 MB vs ~320 MB) and crash 512 MB hosts at startup.
            ocr.run(np.full((736, 520, 3), 255, dtype=np.uint8), 1)
    except Exception:
        logging.getLogger("fitscan.ocr").exception("OCR warm-up failed")


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    if settings.is_production and (problems := settings.production_problems()):
        raise RuntimeError("Refusing to start in production:\n- " + "\n- ".join(problems))
    if settings.database_url.startswith("sqlite") and not settings.is_production:
        # zero-setup local dev; Alembic remains the source of truth for Postgres
        from app.db import models  # noqa: F401
        from app.db.base import Base
        from app.db.session import engine

        Base.metadata.create_all(engine)
    task = None if settings.process_inline else asyncio.create_task(_retention_loop())
    if not settings.process_inline:  # load the OCR models now so the first scanned upload doesn't wait for them
        asyncio.get_running_loop().run_in_executor(None, _warm_ocr)
    yield
    if task:
        task.cancel()


app = FastAPI(title="FITSCAN API", version="0.2.0", lifespan=lifespan,
              docs_url=None if settings.is_production else "/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.frontend_origin.split(",")],  # NFR-03: locked to the frontend
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Guest-Token"],
    expose_headers=["X-Guest-Token", "Content-Disposition"],
)
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    h = response.headers
    h.setdefault("X-Content-Type-Options", "nosniff")
    h.setdefault("X-Frame-Options", "DENY")
    h.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    h.setdefault("Cross-Origin-Resource-Policy", "same-site")
    if request.url.path.startswith("/api/"):
        h.setdefault("Cache-Control", "no-store")  # health data must not sit in shared/browser caches
    if settings.is_production:
        h.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


register_error_handlers(app)
app.include_router(api_router, prefix="/api/v1")
