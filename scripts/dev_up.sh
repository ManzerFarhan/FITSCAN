#!/usr/bin/env bash
# Start FITSCAN locally (backend :8000, frontend :3000).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
[ -d .venv ] || { python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt; }
[ -f .env ] || cp ../.env.example .env
.venv/bin/alembic upgrade head
.venv/bin/python scripts/build_kb.py --tfidf
.venv/bin/uvicorn app.main:app --reload --port 8000 &
cd "$ROOT/frontend"
[ -d node_modules ] || npm install
[ -f .env.local ] || echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1" > .env.local
npm run dev
