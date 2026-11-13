> **Scope change (2026-11-11):** the doctor's-prescription tasks (FR-RX-*, recommendations) were removed - printed lab reports only.

# FITSCAN — Task Sheet

Legend — **Pri:** M = MUST, S = SHOULD. **Status:** ☐ Todo · ◐ In progress · ☑ Done. **Est:** hours (rough).
**Refs** point to `01_BRD_FITSCAN.md`. Update the Status column as work completes.

#> **Scope change (2026-11-11):** the doctor's-prescription tasks (FR-RX-*, recommendations) were removed - printed lab reports only.

# PHASE 1 — Foundation & UI (Weeks 1–2)

| ID | Task | Files / Area | Refs | Pri | Est | Depends | Status |
|---|---|---|---|---|---|---|---|
| P1-01 | Create monorepo, git init, .gitignore | root | — | M | 1 | — | ◐ git not installed on dev machine - run `git init` |
| P1-02 | Add docs folder with 4 docs | docs/ | — | M | 0.5 | P1-01 | ☑ |
| P1-03 | Write README, CLAUDE.md, .env.example | root | NFR-05 | M | 1.5 | P1-01 | ☑ |
| P1-04 | docker-compose: Postgres + MinIO | docker-compose.yml | NFR-06 | M | 2 | P1-01 | ☑ |
| P1-05 | Scaffold Next.js + TS + Tailwind + shadcn | frontend/ | — | M | 2 | P1-01 | ☑ |
| P1-06 | Global layout, Navbar, nav to 5 routes | layout/Navbar.tsx | §4 | M | 3 | P1-05 | ☑ |
| P1-07 | DisclaimerBanner + constants | DisclaimerBanner, constants.ts | BR-13 | M | 1 | P1-05 | ☑ |
| P1-08 | TS types + enums mirroring BRD §6 | lib/types.ts | §6 | M | 2 | P1-05 | ☑ |
| P1-09 | Mock JSON data (dashboard, reports, rx, centres) | src/mocks/ | FR-DASH-10 | M | 2 | P1-08 | ☑ |
| P1-10 | SummaryCards (4 cards) | dashboard/SummaryCards | FR-DASH-3 | M | 2 | P1-09 | ☑ |
| P1-11 | LatestReportCard | dashboard/ | FR-DASH-4 | M | 2 | P1-09 | ☑ |
| P1-12 | ImportantFindings with 3 finding classes | dashboard/ | FR-DASH-5,9 | M | 3 | P1-09 | ☑ |
| P1-13 | DoctorRecommendations | dashboard/ | FR-DASH-6 | M | 2 | P1-09 | ☑ |
| P1-14 | RecentActivity + QuickActions | dashboard/ | FR-DASH-7,8 | M | 2 | P1-09 | ☑ |
| P1-15 | Assemble dashboard page + header (guest ok) | dashboard/page.tsx | FR-DASH-1,2 | M | 2 | P1-10..14 | ☑ |
| P1-16 | DocTypeSelector | analysis/ | FR-UPL-1 | M | 1.5 | P1-05 | ☑ |
| P1-17 | UploadDropzone: drag/drop, validation, progress | analysis/ | FR-UPL-2,3 | M | 4 | P1-16 | ☑ |
| P1-18 | DocumentPreview (PDF pages + images) | analysis/ | FR-UPL-2 | M | 4 | P1-17 | ☑ |
| P1-19 | ProcessingStatus + page layout w/ placeholders | analysis/page.tsx | FR-UPL-5 | M | 3 | P1-17 | ☑ |
| P1-20 | Tests page UI: list, form, map placeholder | tests/ | FR-TEST-1,4 | M | 5 | P1-09 | ☑ |
| P1-21 | History page UI: list, filters, compare placeholder | history/ | FR-HIST-1 | M | 5 | P1-09 | ☑ |
| P1-22 | Profile page UI: form, tabs, historical upload | profile/ | FR-PROF-1,2,4 | M | 5 | P1-05 | ☑ |
| P1-23 | FastAPI skeleton, config, CORS, logging | backend/app/main.py, core/ | NFR-03,08 | M | 3 | P1-01 | ☑ |
| P1-24 | /health + router structure | api/v1/health.py | API-19 | M | 1 | P1-23 | ☑ |
| P1-25 | SQLAlchemy models DB-01..DB-14 (core ones first) | db/models/ | §7 | M | 5 | P1-23 | ☑ |
| P1-26 | Alembic + initial migration | alembic/ | §7 | M | 2 | P1-25 | ☑ |
| P1-27 | Storage service (MinIO/S3, signed URL) | services/storage.py | NFR-06 | M | 3 | P1-04 | ☑ |
| P1-28 | Mock /dashboard endpoint | api/v1/dashboard.py | API-15 | S | 1 | P1-24 | ☑ |
| P1-29 | POST /documents: validate, store, DB row | api/v1/documents.py | API-01,FR-UPL-3,4 | M | 4 | P1-26,27 | ☑ |

#> **Scope change (2026-11-11):** the doctor's-prescription tasks (FR-RX-*, recommendations) were removed - printed lab reports only.

# PHASE 2 — Document Intelligence (Weeks 3–5)

| ID | Task | Files / Area | Refs | Pri | Est | Depends | Status |
|---|---|---|---|---|---|---|---|
| P2-01 | parameters.json (CBC, LFT, KFT, lipid, thyroid, sugar, B12, D) w/ synonyms + plausible ranges | data/dictionaries | FR-LAB-5,6 | M | 6 | — | ☑ |
| P2-02 | abbreviations.json + tests.json | data/dictionaries | FR-RX-5 | M | 3 | — | ☑ |
| P2-03 | unit_conversions.json + utils/units.py | utils/units.py | FR-HIST-3 | M | 3 | — | ☑ |
| P2-04 | pdf_loader: native text vs scanned detection, PDF→images | preprocessing/pdf_loader.py | FR-LAB-1 | M | 4 | P1-29 | ☑ |
| P2-05 | image_enhance: denoise, contrast, deskew | preprocessing/image_enhance.py | FR-LAB-1 | M | 4 | P2-04 | ☑ |
| P2-06 | PaddleOCR wrapper (+Tesseract fallback) w/ per-word confidence + bbox | ocr/printed_ocr.py | FR-LAB-3 | M | 5 | P2-05 | ☑ |
| P2-07 | range_parser + unit tests (12-16, <200, >40, up to, M/F ranges) | lab_report/range_parser.py | FR-LAB-10 | M | 4 | — | ☑ |
| P2-08 | status_calculator + tests (BR-01) | lab_report/status_calculator.py | FR-LAB-10 | M | 2 | P2-07 | ☑ |
| P2-09 | Lab flag preservation (H/L/*) | lab_report/ | FR-LAB-11 | M | 1 | P2-06 | ☑ |
| P2-10 | table_parser: row clustering, column inference, multi-page | lab_report/table_parser.py | FR-LAB-4 | M | 10 | P2-06 | ☑ |
| P2-11 | metadata_extractor | lab_report/metadata_extractor.py | FR-LAB-2 | M | 5 | P2-06 | ☑ |
| P2-12 | normalizer: synonym→parameter_id, fuzzy fallback | lab_report/normalizer.py | FR-LAB-5 | M | 5 | P2-01 | ☑ |
| P2-13 | confidence + sanity checks + NEEDS_VERIFICATION | lab_report/confidence.py | FR-LAB-7,8, BR-02 | M | 4 | P2-10,12 | ☑ |
| P2-14 | Lab pipeline orchestrator (Pydantic I/O) | lab_report/pipeline.py | NFR-09 | M | 4 | P2-10..13 | ☑ |
| P2-15 | Async job + GET /documents/{id}, GET extraction | services/document_service.py, api | API-02,04, NFR-02 | M | 5 | P2-14 | ☑ |
| P2-16 | PATCH extraction (corrections, verify) | api/v1/documents.py | API-05, FR-LAB-9 | M | 3 | P2-15 | ☑ |
| P2-17 | VerificationTable UI + useDocument polling | analysis/VerificationTable, hooks | FR-LAB-9 | M | 6 | P2-16 | ☑ |
| P2-18 | region_segmenter + printed/handwritten classifier | prescription/region_segmenter.py | FR-RX-1 | M | 6 | P2-05 | ☑ |
| P2-19 | TrOCR handwriting wrapper w/ confidence | ocr/handwriting_ocr.py | FR-RX-2 | M | 6 | P2-18 | ◐ wrapper done; TrOCR not installed/tested (requirements-ml.txt) |
| P2-20 | Benchmark TrOCR vs alternatives on rx samples; log CER/WER | evaluation/ | §10 | M | 6 | P2-19 | ☐ needs consented handwritten prescription set |
| P2-21 | entity_extractor (doctor, date, meds, dosage, tests) | prescription/entity_extractor.py | FR-RX-3 | M | 6 | P2-19 | ☑ |
| P2-22 | vocab_matcher (rapidfuzz top-k, no auto-substitute) | prescription/vocab_matcher.py | FR-RX-4, BR-03 | M | 4 | P2-02 | ☑ |
| P2-23 | abbreviation expansion | prescription/abbreviation.py | FR-RX-5 | M | 2 | P2-02 | ☑ |
| P2-24 | Prescription pipeline orchestrator | prescription/pipeline.py | NFR-09 | M | 3 | P2-21..23 | ☑ |
| P2-25 | PrescriptionVerifier UI (bbox highlights, candidates dropdown) | analysis/PrescriptionVerifier | FR-RX-6 | M | 7 | P2-24 | ☑ |
| P2-26 | Confirm tests → test_recommendations (+ API) | api/v1/recommendations.py | FR-RX-7,8 | M | 3 | P2-25 | ☑ |
| P2-27 | Build annotated eval datasets (synthetic + public) | evaluation/datasets | §10 | M | 8 | — | ◐ synthetic set done; real/public annotated set pending |
| P2-28 | Fixtures from ≥5 lab layouts + expected JSON; pipeline tests | tests/fixtures | NFR-10 | M | 6 | P2-14 | ☑ |

#> **Scope change (2026-11-11):** the doctor's-prescription tasks (FR-RX-*, recommendations) were removed - printed lab reports only.

# PHASE 3 — AI Analysis & Recommendations (Weeks 6–8)

| ID | Task | Files / Area | Refs | Pri | Est | Depends | Status |
|---|---|---|---|---|---|---|---|
| P3-01 | Collect KB sources (MedlinePlus/NIH/WHO/NHS) respecting licences | data/kb | FR-AI-7 | M | 6 | — | ☑ |
| P3-02 | Chunking + metadata (source, URL, title) | rag/ingest.py | FR-AI-7 | M | 3 | P3-01 | ☑ |
| P3-03 | Embeddings (sentence-transformers) | rag/embeddings.py | FR-AI-7 | M | 2 | P3-02 | ☑ |
| P3-04 | FAISS index build/load + script | rag/vector_store.py, scripts/build_kb.py | FR-AI-7 | M | 3 | P3-03 | ☑ |
| P3-05 | Retriever (top-k, parameter-aware query) | rag/retriever.py | BR-11 | M | 3 | P3-04 | ☑ |
| P3-06 | LLMClient interface + provider impl | rag/llm_client.py | A1 | M | 3 | — | ☑ |
| P3-07 | Versioned prompts (system rules, summary, param explain, chat, compare) | rag/prompts.py | BR-04,10,11 | M | 5 | P3-06 | ☑ |
| P3-08 | safety_validator + safety_rules.yaml | rag/safety_validator.py | FR-AI-5, BR-04 | M | 5 | P3-07 | ☑ |
| P3-09 | escalation_rules.yaml + URGENT logic | config/, analysis_service | BR-05 | M | 3 | P3-08 | ☑ |
| P3-10 | analysis_service: verified-only summary & observations | services/analysis_service.py | FR-AI-2,4, BR-02 | M | 6 | P3-05,08 | ☑ |
| P3-11 | POST/GET /documents/{id}/analysis | api/v1/analysis.py | API-06,07 | M | 2 | P3-10 | ☑ |
| P3-12 | AnalysisPanel + AI button + ParameterRow | analysis/ | FR-AI-1,3 | M | 7 | P3-11 | ☑ |
| P3-13 | Chat endpoint with citations | api/v1/analysis.py | API-08, FR-AI-6 | M | 4 | P3-10 | ☑ |
| P3-14 | ChatAssistant UI | analysis/ChatAssistant | FR-AI-6 | M | 5 | P3-13 | ☑ |
| P3-15 | PDF summary (ReportLab) + download endpoint/button | pdf_report_service.py | FR-AI-8, API-09 | M | 7 | P3-10 | ☑ |
| P3-16 | CentreProvider interface | integrations/centre_provider.py | FR-TEST-5 | M | 1 | — | ☑ |
| P3-17 | GooglePlaces provider (search, details, caching) | integrations/google_places.py | FR-TEST-4,6 | M | 6 | P3-16 | ◐ implemented; not tested live (no API key) - OSM used |
| P3-18 | Ranking engine + ranking_weights.yaml + tests | centre_service.py | FR-TEST-8 | M | 4 | P3-17 | ☑ |
| P3-19 | Location resolution (profile → doc patient addr → manual) | centre_service, LocationPicker | FR-TEST-3, BR-06 | M | 3 | P3-17 | ☑ |
| P3-20 | POST /centres/search + CentreSearchForm + CentreCard | api, tests/ UI | API-13, FR-TEST-6,7 | M | 7 | P3-18,19 | ☑ |
| P3-21 | CentreMap + CentreCompare | tests/ | FR-TEST-9,10 | M | 6 | P3-20 | ☑ |
| P3-22 | Recommendation status flow + mark complete | recommendations API/UI | FR-TEST-2,11, BR-08 | M | 4 | P2-26 | ☑ |
| P3-23 | comparison_service: match, unit-normalize, Δ, %Δ, range-change, unmatched | services/comparison_service.py | FR-HIST-3, BR-09 | M | 8 | P2-03,12 | ☑ |
| P3-24 | POST /comparisons + unit tests | api/v1/comparisons.py | API-14 | M | 3 | P3-23 | ☑ |
| P3-25 | ComparisonSelector + PrevCurrentCards | history/ | FR-HIST-3,4 | M | 4 | P3-24 | ☑ |
| P3-26 | TrendChart (Recharts with ref-range band) + timeline | history/TrendChart | FR-HIST-4 | M | 5 | P3-24 | ☑ |
| P3-27 | AI comparison summary + ComparisonSummary | analysis_service, history/ | FR-HIST-5 | M | 4 | P3-24,08 | ☑ |
| P3-28 | Real /dashboard aggregation; remove mocks | api/v1/dashboard.py | API-15 | M | 4 | P3-11,22 | ☑ |
| P3-29 | Real history list/filter endpoint wired to UI | api/v1/documents.py | API-11, FR-HIST-1,2 | M | 4 | P2-15 | ☑ |
| P3-30 | Adversarial safety tests (diagnosis bait, dose bait) | tests/ | BR-04 | M | 3 | P3-08 | ☑ |

#> **Scope change (2026-11-11):** the doctor's-prescription tasks (FR-RX-*, recommendations) were removed - printed lab reports only.

# PHASE 4 — Patient Management, Testing, Deployment (Weeks 9–10)

| ID | Task | Files / Area | Refs | Pri | Est | Depends | Status |
|---|---|---|---|---|---|---|---|
| P4-01 | core/security.py: argon2/bcrypt hashing, JWT/session | core/security.py | NFR-03 | M | 3 | — | ☑ |
| P4-02 | Auth endpoints: register/login/logout/reset | api/v1/auth.py | API-16, FR-PROF-5 | M | 5 | P4-01 | ☑ |
| P4-03 | deps: get_current_user_or_guest; guest token | api/deps.py | FR-PROF-6, BR-15 | M | 3 | P4-02 | ☑ |
| P4-04 | Login/Register/Reset UI + route guards + useAuth | (auth)/, hooks | FR-PROF-5 | M | 5 | P4-02 | ☑ |
| P4-05 | Enforce per-user filtering across all queries + authz tests | api/, tests/ | NFR-04 | M | 4 | P4-03 | ☑ |
| P4-06 | Guest → account migration of session docs | services | FR-PROF-6 | S | 3 | P4-03 | ☑ |
| P4-07 | Profile GET/PATCH + UI binding | api/v1/profile.py | API-17, FR-PROF-1 | M | 4 | P4-02 | ☑ |
| P4-08 | Historical upload via profile (report_date handling, BR-14) | api, HistoricalUpload | API-18, FR-PROF-2 | M | 5 | P4-07 | ☑ |
| P4-09 | Delete document + cascade derived data + storage object | services | API-10, FR-HIST-2 | M | 3 | P4-05 | ☑ |
| P4-10 | Retention preferences + account deletion | PrivacyControls, api | FR-PROF-4 | M | 4 | P4-09 | ☑ |
| P4-11 | Guest cleanup job (cron/script) | retention_service, scripts | BR-15 | M | 2 | P4-03 | ☑ |
| P4-12 | Integration tests: upload→extract→verify→analyze | tests/integration | NFR-10 | M | 6 | — | ☑ |
| P4-13 | Playwright E2E for 5 key flows | frontend/e2e | — | M | 6 | P4-04 | ☑ |
| P4-14 | Run evaluations: CER/WER, NER F1, param exact-match, range acc., unit norm | evaluation/ | §10 | M | 8 | P2-27 | ◐ run on synthetic data (docs/evaluation_report.md) |
| P4-15 | Run RAG evaluations: P@K, R@K, faithfulness; write evaluation_report.md | evaluation/, docs/ | §10 | M | 6 | P3-05 | ◐ RAG metrics done; faithfulness rubric pending |
| P4-16 | Security pass: authz, upload validation, rate limiting, dep audit, secrets scan | repo-wide | NFR-03..06 | M | 5 | P4-05 | ◐ authz/upload/rate-limit done; dependency audit + secrets scan pending |
| P4-17 | Deploy backend (Render) + DB + S3-compatible storage | infra | A3 | M | 5 | P4-16 | ☐ needs Render/DB/S3 accounts |
| P4-18 | Deploy frontend (Vercel); env + CORS hardening | infra | A3 | M | 3 | P4-17 | ☐ needs Vercel account |
| P4-19 | Technical documentation + api.md + architecture.md | docs/ | — | M | 6 | — | ☑ |
| P4-20 | Final project report | docs/ | — | M | 8 | P4-15 | ☐ |
| P4-21 | Presentation + demo script (with synthetic data) | docs/ | — | M | 5 | P4-18 | ☐ |
| P4-22 | CI workflow (lint + tests) | .github/workflows/ci.yml | — | S | 2 | P4-12 | ◐ workflow written; runs once pushed to GitHub |

#> **Scope change (2026-11-11):** the doctor's-prescription tasks (FR-RX-*, recommendations) were removed - printed lab reports only.

# BR Coverage Checklist (all must have ≥1 automated test by end of Phase 4)

| BR | Test location | Done |
|---|---|---|
| BR-01 own ref range | unit/status_calculator | ☑ |
| BR-02 unverified excluded | integration/analysis | ☑ |
| BR-03 no silent guessing | unit/vocab_matcher | ☑ |
| BR-04 no diagnosis | unit/safety_validator + adversarial | ☑ |
| BR-05 three finding classes | unit/analysis | ☑ |
| BR-06 lab address ≠ patient address | unit/centre_service | ☑ |
| BR-07 search on confirmed only | integration/centres | ☑ |
| BR-08 view ≠ complete | integration/recommendations | ☑ |
| BR-09 comparison rules | unit/comparison_service | ☑ |
| BR-10 labelled sources | e2e UI | ☑ |
| BR-11 citations / no-source fallback | integration/chat | ☑ |
| BR-12 verified vs unverified centres | unit/centre_service | ☑ |
| BR-13 disclaimer present | e2e + pdf test | ☑ |
| BR-14 report_date vs uploaded_at | unit/models | ☑ |
| BR-15 guest retention | integration/cleanup | ☑ |

### Additions after Phase 4

| ID | Task | Req | Status |
|---|---|---|---|
| X-01 | Extended test dictionary: 310 more tests (urine, blood gas, tumour markers, serology, autoimmune, vitamins, hormones, coagulation, drug levels) | FR-LAB-5 | ☑ |
| X-02 | Admin panel `/admin` + `/api/v1/admin/*` (overview, clients, reports, unrecognised test names) | FR-ADM-1..6 | ☑ |

**Totals:** Phase 1: 29 tasks · Phase 2: 28 · Phase 3: 30 · Phase 4: 22 → **109 tasks**.
