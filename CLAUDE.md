# FITSCAN – Rules for Claude
- Read docs/01_BRD_FITSCAN.md before implementing any feature; cite requirement IDs in commit messages (e.g., "FR-LAB-10: range parser").
- Work phase by phase using docs/04_TASK_SHEET.md; update task Status column when done.
- Never violate Global Business Rules BR-01..BR-15.
- Never use real patient data in tests; use synthetic fixtures.
- Backend: Python 3.11, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, pytest. Format: ruff + black.
- Frontend: Next.js App Router, TypeScript strict, Tailwind, shadcn/ui-style primitives, Recharts.
- Every AI/LLM output must pass safety_validator and be labelled AI_GENERATED.
- All enums live once in backend/app/core/constants.py and are mirrored in frontend/src/lib/constants.ts.
- Module dependency rule: api/ -> services/ -> pipelines/ | rag/ | integrations/ | db/. Pipelines are pure (no DB access).

## Commands
- `docker compose up -d` (optional: Postgres + MinIO; local dev defaults to SQLite + local file storage)
- `cd backend && .venv\Scripts\activate && alembic upgrade head && uvicorn app.main:app --reload`
- `cd frontend && npm run dev`
- `cd backend && pytest`
