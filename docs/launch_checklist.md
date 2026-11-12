# FITSCAN - Launch checklist

Status as of 2026-11-11. ✅ = done and verified in this repo, ⬜ = needs an action from the project owner
(accounts, money, legal or clinical sign-off), ⚠️ = done but could not be verified on the development machine.

## 1. Product scope

| | Item |
|---|---|
| ✅ | 10 priority blood-test panels covered (CBC, lipid, diabetes, KFT, LFT, thyroid, vitamins, iron, electrolytes, inflammation) - 142 tests, 694 name variants in the dictionary |
| ✅ | Printed lab reports only - the doctor's-prescription feature (handwriting reading, test recommendations) was removed |
| ✅ | Reads test rows only - notes, interpretation paragraphs, method lines and page/booking footers are ignored |
| ✅ | "Auto-check & confirm": plausible values accepted automatically; doubtful values excluded from the AI analysis and listed |
| ✅ | Knowledge library: 81 articles (69 MedlinePlus, 7 NIH ODS, 1 NHS, 4 FITSCAN glossary); every MedlinePlus link checked |
| ⬜ | **Clinical review** of the 81 knowledge articles, the assistant's answers (`backend/config/assistant_faq.yaml`) and the urgent-value rules (`backend/config/escalation_rules.yaml`) by a qualified clinician |

## 2. Quality evidence (see `docs/evaluation_report.md`)

| | Item |
|---|---|
| ✅ | Backend: 276 automated tests pass (unit + API + panel benchmark) |
| ✅ | Frontend: production build passes (14 pages), TypeScript strict, 7 Playwright browser tests pass |
| ✅ | Panel benchmark (30 synthetic reports, 147 rows, real-world value distributions): digital 100 % exact, 0 extra rows; scanned 100 % recall, 97.3 % exact, 0 extra rows |
| ✅ | Safety guardrails: 18/18 unsafe AI outputs blocked |
| ⬜ | **Real-world pilot**: 30+ consented, de-identified real reports from several Indian labs, annotated and scored (BRD §10). Synthetic results are not evidence of real-world accuracy |

## 3. Security & privacy

| | Item |
|---|---|
| ✅ | Backend refuses to start in production with default secrets, SQLite, local file storage, default storage keys or non-HTTPS origins |
| ✅ | HTTPS via Caddy (automatic certificates), HSTS, nosniff, frame-deny, referrer policy; API responses `Cache-Control: no-store` |
| ✅ | httpOnly + Secure + SameSite cookies; bcrypt passwords; per-user/guest data isolation (tested); rate limits on upload, AI and assistant |
| ✅ | Containers run as non-root; API docs hidden in production; guest data auto-deleted after 24 h (failures are logged) |
| ✅ | Privacy and Terms pages, linked in the footer of every page |
| ✅ | Full Privacy Policy (14 sections: DPDP Act 2023 rights, SPDI Rules 2011, Grievance Officer) and Terms & Conditions (19 sections), linked in the footer of every page and accepted at sign-up |
| ⬜ | Fill every `[placeholder]` in `frontend/src/lib/site.ts` (company name, address, emails, Grievance Officer, jurisdiction city) and the few inline ones (data region, retention days, liability cap). Placeholders show highlighted in yellow on the pages until replaced |
| ⬜ | **Legal review** of `/privacy` and `/terms` by a lawyer familiar with the DPDP Act 2023 and IT Act 2000 |
| ⬜ | Dependency vulnerability scan in CI (`pip-audit`, `npm audit`) and a basic penetration test |

## 4. Deployment

| | Item |
|---|---|
| ✅ | `docker-compose.prod.yml`: Caddy -> Next.js (standalone) + FastAPI, PostgreSQL 16, MinIO (S3) |
| ✅ | `deploy/.env.production.example`, `deploy/Caddyfile`, health checks, Alembic migrations on start |
| ⚠️ | Docker is not installed on the development machine, so the images and compose stack have **not been built here**. First run them on the server (or install Docker Desktop) and fix anything that comes up |
| ⬜ | Server or cloud account (e.g. a 2 vCPU / 4 GB VM), a domain name and its DNS A record |
| ⬜ | Fill `deploy/.env.production` with real secrets, then `docker compose -f docker-compose.prod.yml --env-file deploy/.env.production up -d --build` |
| ⬜ | Daily PostgreSQL + MinIO backups, with one test restore before launch |
| ⬜ | Uptime monitoring on `https://<domain>/api/v1/health` and error alerting (e.g. Sentry) |

## 5. Optional upgrades (keys / spend)

| | Item |
|---|---|
| ⬜ | `LLM_API_KEY` (Anthropic) for fluent AI explanations - otherwise offline template explanations are used |
| ⬜ | `GOOGLE_PLACES_API_KEY` for richer centre search - otherwise OpenStreetMap |

## 6. Go / no-go

Launch publicly only when every ⬜ in sections 1-4 is done. Until then FITSCAN is suitable for a closed beta with
informed testers.

