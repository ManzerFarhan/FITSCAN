# FITSCAN — Phase-Wise Steps Distribution

Total: 10 weeks, 4 phases. Each phase lists **goal → steps (ordered) → exit criteria → hand-off artifacts**.
Task IDs (e.g., `P2-07`) refer to `04_TASK_SHEET.md`.

```
Wk:  1  2 | 3  4  5 | 6  7  8 | 9  10
     P1   |   P2     |   P3     |  P4
```

---

## PHASE 1 — Foundation & UI (Weeks 1–2)

**Goal:** Navigable 5-page frontend on mock data + running backend skeleton + DB/storage.

### Week 1
1. Init monorepo, git, `.gitignore`, `.env.example`, `CLAUDE.md`, docs folder. (P1-01…P1-03)
2. `docker-compose` with Postgres + MinIO. (P1-04)
3. Frontend scaffold: Next.js + TS + Tailwind + shadcn; global layout, navbar, disclaimer. (P1-05…P1-07)
4. Define shared enums/types/mocks. (P1-08, P1-09)
5. Build **Dashboard** page with mock data. (P1-10…P1-15)

### Week 2
6. Build **Upload & Analysis** page UI (selector, dropzone, preview, status; verification/analysis as static placeholders). (P1-16…P1-19)
7. Build **Tests** page UI (list + search form + map placeholder). (P1-20)
8. Build **History** page UI (list, filters, comparison placeholder). (P1-21)
9. Build **Profile** page UI (forms, settings tabs, historical upload). (P1-22)
10. Backend skeleton: FastAPI app, config, health, DB models + first Alembic migration, storage service, mock `/dashboard`. (P1-23…P1-28)
11. Wire upload to backend `POST /documents` (store file, return id; no processing). (P1-29)

**Exit criteria:** all 5 routes render; mobile-responsive; file validation works; `/health` OK; migrations run; a file uploaded lands in MinIO and a `documents` row exists.
**Hand-off:** running app, mock JSON contracts that Phase 2 must replace.

---

## PHASE 2 — Document Intelligence (Weeks 3–5)

**Goal:** Real extraction for lab reports and prescriptions with confidence + verification UI.

### Week 3 — Printed / lab reports core
1. Dictionaries: parameters, abbreviations, units. (P2-01…P2-03)
2. PDF loader + native-text detection + image enhancement. (P2-04, P2-05)
3. PaddleOCR wrapper + Tesseract fallback. (P2-06)
4. Range parser + unit utils + status calculator (**unit tests first**). (P2-07…P2-09)

### Week 4 — Lab pipeline completion
5. Table parser (layout-agnostic: row clustering by y-coordinate, column inference). (P2-10)
6. Metadata extractor (lab name, dates, patient, report no.). (P2-11)
7. Normalizer (synonyms → canonical IDs; fuzzy fallback). (P2-12)
8. Confidence scoring + sanity checks + `NEEDS_VERIFICATION` logic. (P2-13)
9. Pipeline orchestrator + async job + status polling API. (P2-14, P2-15)
10. Verification UI + corrections API. (P2-16, P2-17)

### Week 5 — Prescriptions
11. Region segmentation + printed/handwritten classification. (P2-18)
12. TrOCR integration; benchmark alternatives on sample set; record CER/WER. (P2-19, P2-20)
13. Entity extractor + vocab matcher (top-k) + abbreviation expansion. (P2-21…P2-23)
14. Prescription verifier UI with bbox highlights. (P2-24, P2-25)
15. Confirm tests → `test_recommendations`. (P2-26)
16. Collect/annotate evaluation sets; first OCR metrics. (P2-27)

**Exit criteria:** ≥ 5 different lab layouts parsed with correct params/units/ranges on fixtures; low-confidence fields flagged; user corrections persist; prescription tests extracted with candidates; nothing auto-guessed.
**Hand-off:** `verified` parameters & confirmed tests in DB.

---

## PHASE 3 — AI Analysis & Smart Recommendations (Weeks 6–8)

**Goal:** RAG explanations, safe summaries, PDF export, centre finder, comparison.

### Week 6 — RAG
1. Collect KB sources (MedlinePlus, NIH, WHO, NHS); chunk; embed; FAISS index. (P3-01…P3-04)
2. Retriever + LLM client + versioned prompts. (P3-05…P3-07)
3. Safety validator + escalation rules + tests with adversarial prompts. (P3-08, P3-09)

### Week 7 — Analysis UX
4. Analysis service: summary + parameter-wise + observations (verified-only). (P3-10, P3-11)
5. Analysis panel UI + "Check AI Medical Report Analysis" button. (P3-12)
6. Chat assistant API + UI with citations. (P3-13, P3-14)
7. PDF summary generator (ReportLab) + download. (P3-15)

### Week 8 — Centres & Comparison
8. CentreProvider interface + Google Places implementation; ranking engine. (P3-16…P3-18)
9. Tests page: location resolution, search, cards, compare, map. (P3-19…P3-21)
10. Recommendation status flow endpoints/UI. (P3-22)
11. Comparison service (match, unit normalize, deltas) + API. (P3-23, P3-24)
12. History UI: charts, prev/current cards, AI comparison summary. (P3-25…P3-27)
13. Replace dashboard mocks with real aggregated API. (P3-28)

**Exit criteria:** explanations cite sources; guardrail blocks diagnosis language in tests; PDF downloads; centre search returns ranked, labelled results; comparison correct on synthetic data.

---

## PHASE 4 — Patient Management, Testing, Deployment (Weeks 9–10)

**Goal:** Auth, persistence, privacy, evaluation, deploy, final docs.

### Week 9
1. Auth backend (register/login/logout/reset), hashing, sessions/JWT, protected routes. (P4-01…P4-03)
2. Auth UI + route guards. (P4-04)
3. Per-user data isolation on all queries; guest→user migration. (P4-05, P4-06)
4. Profile API + UI binding; historical upload via profile; report-date handling. (P4-07, P4-08)
5. Privacy: delete document, retention preferences, account deletion, guest cleanup job. (P4-09…P4-11)

### Week 10
6. End-to-end tests (Playwright) + integration tests. (P4-12, P4-13)
7. Evaluation runs and report (OCR, NER, RAG, faithfulness). (P4-14, P4-15)
8. Security checks (authz tests, file validation, rate limit, dependency audit). (P4-16)
9. Deploy (frontend + backend + DB + storage); env hardening. (P4-17, P4-18)
10. Final docs, demo script, presentation. (P4-19…P4-21)

**Exit criteria:** authenticated multi-user isolation verified; deployed URL works end-to-end; evaluation report complete; all BR-01…BR-15 covered by at least one test.

---

## Cross-Phase Dependencies

| Needs | From |
|---|---|
| Verification UI (P2) | Document & parameter schemas (P1) |
| AI analysis (P3) | Verified parameters (P2) |
| Centre finder (P3) | Confirmed tests (P2) |
| Comparison (P3) | Canonical IDs + normalized units (P2) |
| Auth (P4) | `user_id`/`guest_session_id` columns (P1 migrations) |

## Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Handwriting accuracy low | High | Confidence flags, top-k candidates, mandatory user confirmation, honest reporting |
| Diverse lab layouts | High | Layout-agnostic parser, fixtures from ≥ 5 labs, manual correction UI |
| LLM hallucination | High | Verified-only input, RAG citations, safety validator, no-source fallback |
| Maps/API cost & data quality | Med | Provider interface, caching, "unverified" labelling |
| CPU-heavy OCR latency | Med | Async jobs, page limits, progress UI |
| Privacy/PHI leakage | High | PHI-free logs, signed URLs, retention, deletion |
| Time (10 weeks) | Med | MUST/SHOULD priorities in BRD; cut SHOULD items first |
