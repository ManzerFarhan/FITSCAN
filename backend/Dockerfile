FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# Build the knowledge-library index at image build time (deterministic, no network needed).
RUN python scripts/build_kb.py --tfidf

# Never run as root (uid 1000 is what Hugging Face Spaces expects).
RUN useradd --create-home --uid 1000 fitscan && chown -R fitscan /app
USER fitscan

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -fsS http://localhost:${PORT:-8000}/api/v1/health || exit 1
# Migrations first; trust X-Forwarded-* from the reverse proxy so HTTPS/cookies behave correctly.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --proxy-headers --forwarded-allow-ips='*'"]
