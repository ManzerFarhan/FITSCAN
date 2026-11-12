# FITSCAN — Repository & File Structure

Monorepo. Frontend (Next.js) + Backend (FastAPI). Each file listed has one clear responsibility.
`[P1]`–`[P4]` = the phase in which the file is first created (see `03_PHASE_PLAN.md`).

```
fitscan/
├── README.md                          [P1] Setup, run, env, architecture summary
├── CLAUDE.md                          [P1] Instructions for Claude Code (rules, conventions, commands) — see bottom
├── docs/
│   ├── 01_BRD_FITSCAN.md              [P1]
│   ├── 02_FILE_STRUCTURE.md           [P1]
│   ├── 03_PHASE_PLAN.md               [P1]
│   ├── 04_TASK_SHEET.md               [P1]
│   ├── api.md                         [P2] Generated/maintained API notes
│   ├── evaluation_report.md           [P4]
│   └── architecture.md                [P3] Diagrams of pipelines
├── docker-compose.yml                 [P1] postgres, minio (S3), backend, (frontend optional)
├── .env.example                       [P1]
├── .gitignore                         [P1]
├── .github/workflows/ci.yml           [P4] lint + tests
│
├── frontend/                          # Next.js (App Router) + TS + Tailwind + shadcn/ui
│   ├── package.json                   [P1]
│   ├── next.config.js                 [P1]
│   ├── tailwind.config.ts             [P1]
│   ├── tsconfig.json                  [P1]
│   ├── public/
│   │   └── logo.svg                   [P1]
│   └── src/
│       ├── app/
│       │   ├── layout.tsx             [P1] Shell: navbar + disclaimer footer
│       │   ├── page.tsx               [P1] Redirect → /dashboard
│       │   ├── dashboard/page.tsx     [P1] Page 1
│       │   ├── analysis/page.tsx      [P1] Page 2
│       │   ├── tests/page.tsx         [P1] Page 3
│       │   ├── history/page.tsx       [P1] Page 4
│       │   ├── profile/page.tsx       [P1] Page 5
│       │   └── (auth)/
│       │       ├── login/page.tsx     [P4]
│       │       ├── register/page.tsx  [P4]
│       │       └── reset-password/page.tsx [P4]
│       ├── components/
│       │   ├── ui/                    [P1] shadcn primitives (button, card, dialog, table, tabs…)
│       │   ├── layout/
│       │   │   ├── Navbar.tsx         [P1]
│       │   │   ├── NotificationBell.tsx [P1]
│       │   │   └── DisclaimerBanner.tsx [P1]
│       │   ├── dashboard/
│       │   │   ├── SummaryCards.tsx   [P1]
│       │   │   ├── LatestReportCard.tsx [P1]
│       │   │   ├── ImportantFindings.tsx [P1]
│       │   │   ├── DoctorRecommendations.tsx [P1]
│       │   │   ├── RecentActivity.tsx [P1]
│       │   │   └── QuickActions.tsx   [P1]
│       │   ├── analysis/
│       │   │   ├── DocTypeSelector.tsx [P1]
│       │   │   ├── UploadDropzone.tsx [P1]
│       │   │   ├── DocumentPreview.tsx [P1]
│       │   │   ├── ProcessingStatus.tsx [P1]
│       │   │   ├── VerificationTable.tsx [P2] Lab params editor
│       │   │   ├── PrescriptionVerifier.tsx [P2] Image + bbox highlights + editable text
│       │   │   ├── AnalysisPanel.tsx  [P3] Summary + param-wise
│       │   │   ├── ParameterRow.tsx   [P3]
│       │   │   ├── ChatAssistant.tsx  [P3]
│       │   │   └── DownloadSummaryButton.tsx [P3]
│       │   ├── tests/
│       │   │   ├── RecommendedTestsList.tsx [P1]
│       │   │   ├── LocationPicker.tsx [P3]
│       │   │   ├── CentreSearchForm.tsx [P3]
│       │   │   ├── CentreCard.tsx     [P3]
│       │   │   ├── CentreCompare.tsx  [P3]
│       │   │   └── CentreMap.tsx      [P3]
│       │   ├── history/
│       │   │   ├── DocumentList.tsx   [P1]
│       │   │   ├── DocumentFilters.tsx [P1]
│       │   │   ├── ComparisonSelector.tsx [P3]
│       │   │   ├── TrendChart.tsx     [P3] Recharts
│       │   │   ├── PrevCurrentCards.tsx [P3]
│       │   │   └── ComparisonSummary.tsx [P3]
│       │   └── profile/
│       │       ├── ProfileForm.tsx    [P1]
│       │       ├── HistoricalUpload.tsx [P1→P4]
│       │       ├── SettingsTabs.tsx   [P1]
│       │       └── PrivacyControls.tsx [P4]
│       ├── lib/
│       │   ├── api.ts                 [P1] fetch wrapper (base URL, error handling)
│       │   ├── types.ts               [P1] TS types mirroring backend schemas
│       │   ├── constants.ts           [P1] enums, DISCLAIMER_TEXT
│       │   └── utils.ts               [P1]
│       ├── hooks/
│       │   ├── useDocument.ts         [P2] polling status
│       │   └── useAuth.ts             [P4]
│       ├── mocks/                     [P1] sample data for Phase 1
│       │   ├── dashboard.json
│       │   ├── reports.json
│       │   ├── prescriptions.json
│       │   └── centres.json
│       └── styles/globals.css         [P1]
│
├── backend/
│   ├── pyproject.toml / requirements.txt [P1]
│   ├── alembic.ini                    [P1]
│   ├── alembic/versions/              [P1+] migrations
│   ├── app/
│   │   ├── main.py                    [P1] FastAPI app, CORS, routers
│   │   ├── core/
│   │   │   ├── config.py              [P1] Pydantic Settings (env)
│   │   │   ├── security.py            [P4] hashing, JWT
│   │   │   ├── logging.py             [P1] PHI-safe logger
│   │   │   └── constants.py           [P1] enums & statuses
│   │   ├── db/
│   │   │   ├── session.py             [P1]
│   │   │   ├── base.py                [P1]
│   │   │   └── models/                [P1→P4] SQLAlchemy models (user, document, parameter, …)
│   │   ├── schemas/                   [P1→] Pydantic request/response models
│   │   ├── api/
│   │   │   ├── deps.py                [P1] db session, current user/guest
│   │   │   └── v1/
│   │   │       ├── router.py          [P1]
│   │   │       ├── documents.py       [P2]
│   │   │       ├── analysis.py        [P3]
│   │   │       ├── recommendations.py [P3]
│   │   │       ├── centres.py         [P3]
│   │   │       ├── comparisons.py     [P3]
│   │   │       ├── dashboard.py       [P1 mock → P3 real]
│   │   │       ├── auth.py            [P4]
│   │   │       ├── profile.py         [P4]
│   │   │       └── health.py          [P1]
│   │   ├── services/
│   │   │   ├── storage.py             [P1] S3/MinIO client, signed URLs
│   │   │   ├── document_service.py    [P2] orchestrates pipelines
│   │   │   ├── analysis_service.py    [P3]
│   │   │   ├── recommendation_service.py [P3]
│   │   │   ├── centre_service.py      [P3]
│   │   │   ├── comparison_service.py  [P3]
│   │   │   ├── pdf_report_service.py  [P3] ReportLab
│   │   │   └── retention_service.py   [P4] guest cleanup job
│   │   ├── pipelines/
│   │   │   ├── base.py                [P2] Stage interface
│   │   │   ├── preprocessing/
│   │   │   │   ├── pdf_loader.py      [P2] PyMuPDF
│   │   │   │   └── image_enhance.py   [P2] OpenCV
│   │   │   ├── ocr/
│   │   │   │   ├── printed_ocr.py     [P2] PaddleOCR (+ Tesseract fallback)
│   │   │   │   └── handwriting_ocr.py [P2] TrOCR
│   │   │   ├── lab_report/
│   │   │   │   ├── metadata_extractor.py [P2]
│   │   │   │   ├── table_parser.py    [P2]
│   │   │   │   ├── range_parser.py    [P2] "12-16", "<200", ">40"
│   │   │   │   ├── normalizer.py      [P2] synonyms→parameter_id, units
│   │   │   │   ├── status_calculator.py [P2]
│   │   │   │   ├── confidence.py      [P2]
│   │   │   │   └── pipeline.py        [P2]
│   │   │   └── prescription/
│   │   │       ├── region_segmenter.py [P2]
│   │   │       ├── entity_extractor.py [P2]
│   │   │       ├── vocab_matcher.py   [P2] rapidfuzz top-k
│   │   │       ├── abbreviation.py    [P2]
│   │   │       └── pipeline.py        [P2]
│   │   ├── rag/
│   │   │   ├── ingest.py              [P3] fetch/chunk KB docs
│   │   │   ├── embeddings.py          [P3] sentence-transformers
│   │   │   ├── vector_store.py        [P3] FAISS
│   │   │   ├── retriever.py           [P3]
│   │   │   ├── prompts.py             [P3] system + task prompts (versioned)
│   │   │   ├── llm_client.py          [P3] LLM interface
│   │   │   └── safety_validator.py    [P3] output guardrails
│   │   ├── integrations/
│   │   │   ├── centre_provider.py     [P3] abstract CentreProvider
│   │   │   └── google_places.py       [P3]
│   │   └── utils/
│   │       ├── units.py               [P2] conversions
│   │       └── dates.py               [P2]
│   ├── data/
│   │   ├── dictionaries/
│   │   │   ├── parameters.json        [P2] canonical params + synonyms + plausible ranges
│   │   │   ├── abbreviations.json     [P2]
│   │   │   ├── tests.json             [P2] diagnostic test names
│   │   │   ├── medicines.json         [P2]
│   │   │   └── unit_conversions.json  [P2]
│   │   ├── kb/                        [P3] raw knowledge-base source docs
│   │   └── faiss_index/               [P3] built index (gitignored)
│   ├── config/
│   │   ├── safety_rules.yaml          [P3] forbidden phrases
│   │   ├── escalation_rules.yaml      [P3] urgent thresholds
│   │   └── ranking_weights.yaml       [P3]
│   ├── scripts/
│   │   ├── build_kb.py                [P3]
│   │   ├── seed_dictionaries.py       [P2]
│   │   └── cleanup_guests.py          [P4]
│   └── tests/
│       ├── unit/ (range_parser, normalizer, status, units, comparison, ranking)
│       ├── integration/ (api flows, pipelines)
│       └── fixtures/ (sample reports, prescriptions, expected JSON)
│
├── evaluation/
│   ├── datasets/                      [P2→P4] annotated samples (no real PHI)
│   ├── notebooks/                     [P4] OCR / NER / RAG evaluation
│   └── scripts/ (cer_wer.py, ner_eval.py, rag_eval.py, faithfulness_eval.py)
│
└── scripts/ (dev_up.sh, lint.sh)
```

## Module Dependency Rules

1. `api/` → `services/` → `pipelines/` | `rag/` | `integrations/` | `db/`. No reverse imports.
2. Pipelines are pure: input = file/path or Pydantic object; output = Pydantic object. No DB access inside pipeline stages.
3. Frontend never calls external providers directly (maps key proxied or domain-restricted).
4. All enums defined once in `backend/app/core/constants.py` and mirrored in `frontend/src/lib/constants.ts`.

## Suggested `CLAUDE.md` content (put at repo root)

```
# FITSCAN – Rules for Claude
- Read docs/01_BRD_FITSCAN.md before implementing any feature; cite requirement IDs in commit messages (e.g., "FR-LAB-10: range parser").
- Work phase by phase using docs/04_TASK_SHEET.md; update task Status column when done.
- Never violate Global Business Rules BR-01..BR-15.
- Never use real patient data in tests; use synthetic fixtures.
- Backend: Python 3.11, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, pytest. Format: ruff + black.
- Frontend: Next.js App Router, TypeScript strict, Tailwind, shadcn/ui, Recharts.
- Every AI/LLM output must pass safety_validator and be labelled AI_GENERATED.
- Commands: `docker compose up -d`, `cd backend && uvicorn app.main:app --reload`, `cd frontend && npm run dev`, `pytest`.
```
