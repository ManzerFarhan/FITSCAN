# FITSCAN — Low-Level Business Requirements Document (BRD)

> Purpose: single source of truth for building FITSCAN. Written so an AI coding assistant (Claude Code) or a developer can implement without guessing.
> Companion files: `02_FILE_STRUCTURE.md`, `03_PHASE_PLAN.md`, `04_TASK_SHEET.md`.

---

> **Scope change (2026-11-11):** FITSCAN now reads **printed lab reports only**. The doctor's-prescription feature
> (FR-RX-*, test recommendations, API-12, DB-07/DB-08) was removed at the product owner's request, because handwriting could not
> be read reliably. Requirements below that mention prescriptions are kept for history but are out of scope. BR-07 now means:
> centre search uses only test names the user picks.

## 0. How to Read This Document

- Every requirement has an ID: `FR-<module>-<n>` (functional), `BR-<n>` (business rule), `NFR-<n>` (non-functional), `API-<n>` (endpoint), `DB-<n>` (table).
- **MUST** = required for the prototype. **SHOULD** = desirable. **MAY** = optional.
- Status vocabulary (used everywhere in code and UI) is defined in Section 6.

## 1. Product Summary

FITSCAN is a full-stack web app that lets users upload **lab reports** and **doctor's prescriptions** (PDF/JPG/JPEG/PNG), extracts structured data via OCR/handwriting recognition/NLP, explains lab results in plain language using RAG + LLM, extracts doctor-recommended tests, finds diagnostic centres, stores history, and compares reports over time.

**It is informational only.** It never diagnoses, prescribes, changes doses, or recommends additional tests.

## 2. Actors

| Actor | Description | Access |
|---|---|---|
| Guest | No account; temporary session data | Dashboard, upload, analysis, centre finder (session-only storage) |
| Registered Patient | Authenticated user | All pages, persistent history, profile |
| System (Pipelines) | Background workers | OCR, NLP, RAG, comparison |

## 3. Global Business Rules (apply to ALL modules)

| ID | Rule |
|---|---|
| BR-01 | The lab's own reference range is always preserved and used. Never apply a universal range in place of it. |
| BR-02 | Unverified/low-confidence numeric values MUST NOT be used in AI analysis or comparisons. |
| BR-03 | Never silently guess medicine names, dosages, or test names. Uncertain → flag `NEEDS_VERIFICATION`. |
| BR-04 | AI output must never state a disease diagnosis from a lab value. |
| BR-05 | "Out of range" ≠ "urgent". Three separate classes: `OUT_OF_RANGE`, `UNCERTAIN`, `URGENT`. `URGENT` only via validated escalation rules (config file), never by LLM opinion. |
| BR-06 | The lab's address is NEVER treated as the patient's address. |
| BR-07 | Centre search runs only on user-**confirmed** test names. |
| BR-08 | Viewing a centre does NOT mark a test as completed. Only the user can mark complete. |
| BR-09 | Historical comparison only on reliably matched parameters with compatible units. No "improved/worsened" judgement language. |
| BR-10 | Every AI-generated statement must be visually distinguishable from extracted facts (label "Extracted" vs "AI-generated"). |
| BR-11 | Explanations must cite retrieved sources when available; if no source retrieved, say so instead of inventing. |
| BR-12 | Centre info shown as "confirmed" only when adequately sourced; otherwise "unverified". |
| BR-13 | Every page/summary/PDF carries the medical disclaimer. |
| BR-14 | Store both `report_date` (actual) and `uploaded_at` (system). Never conflate. |
| BR-15 | Guest data is temporary (default retention 24h, configurable). |

Disclaimer text (constant `DISCLAIMER_TEXT`): *"FITSCAN provides general information to help you understand your documents. It does not diagnose conditions, prescribe medication, or replace advice from a qualified doctor. Always consult your doctor."*

## 4. Functional Requirements by Module

### 4.1 Module DASH — Dashboard (Page 1, route `/dashboard`)

| ID | Requirement | Priority |
|---|---|---|
| FR-DASH-1 | Header: logo, welcome message (name if logged in), notification bell, profile menu, quick-upload button. | MUST |
| FR-DASH-2 | Guests can open the dashboard without login. | MUST |
| FR-DASH-3 | 4 summary cards: Total Reports, Tests Analyzed, Out-of-Range Parameters, Pending Test Recommendations. | MUST |
| FR-DASH-4 | "Latest Report" panel: name, lab, category, report date, upload date, status, parameter count, short summary, "View full analysis" link. | MUST |
| FR-DASH-5 | "Important Findings" list: below-range, above-range, lab flags, needs-verification, change-vs-previous. Click → `/analysis?doc=<id>&param=<id>`. | MUST |
| FR-DASH-6 | "Doctor's Recommendations" list: test, prescription date, verification status, discovery status, link to `/tests`. | MUST |
| FR-DASH-7 | "Recent Activity" feed (uploads, analyses, summaries, comparisons, confirmations). | SHOULD |
| FR-DASH-8 | Quick actions: Upload Report, Upload Prescription, View AI Analysis, Find Centres, Compare Reports, View History. | MUST |
| FR-DASH-9 | Findings UI must visually separate `OUT_OF_RANGE` / `UNCERTAIN` / `URGENT`. | MUST |
| FR-DASH-10 | Phase 1 uses mock data from `frontend/src/mocks/`; later replaced by API. | MUST |

**Acceptance:** dashboard renders all sections with mock data; cards count matches mock dataset; no abnormal result is styled as emergency unless flagged `URGENT`.

### 4.2 Module UPL — Upload & AI Analysis (Page 2, route `/analysis`)

| ID | Requirement | Priority |
|---|---|---|
| FR-UPL-1 | Document type selector: `LAB_REPORT` or `PRESCRIPTION`; selection decides the pipeline. | MUST |
| FR-UPL-2 | Upload: drag-drop, browse, PDF/JPG/JPEG/PNG, multipage PDF, preview, size + format validation, progress bar, processing status. | MUST |
| FR-UPL-3 | Max file size 15 MB (config `MAX_UPLOAD_MB`); max 30 pages per PDF (config). | MUST |
| FR-UPL-4 | Original document retained per retention policy. | MUST |
| FR-UPL-5 | Layout order: selector → upload → preview → status → extraction/verification → AI button → detail analysis → assistant → download. | MUST |

#### 4.2.1 Lab Report Pipeline

| ID | Requirement | Priority |
|---|---|---|
| FR-LAB-1 | Preprocess: PDF→images (PyMuPDF), denoise, contrast, deskew/orientation (OpenCV). Digital PDFs: try native text extraction first, OCR fallback. | MUST |
| FR-LAB-2 | Detect metadata: lab name, lab address, patient name, report ID, report date, collection date, category. | MUST |
| FR-LAB-3 | OCR (PaddleOCR; Tesseract fallback): test names, values, units, reference ranges, flags, table headings. | MUST |
| FR-LAB-4 | Layout-agnostic table parsing (no per-lab hard-coded templates). | MUST |
| FR-LAB-5 | NLP normalization: map test name synonyms → canonical `parameter_id` via dictionary (`data/dictionaries/parameters.json`). | MUST |
| FR-LAB-6 | Supported categories: CBC, LFT, KFT, Lipid, Thyroid, Sugar/HbA1c, B12, Vitamin D, other. | MUST |
| FR-LAB-7 | Confidence scoring per field; threshold config (default 0.85). Below → `NEEDS_VERIFICATION`. | MUST |
| FR-LAB-8 | Detect missing values, ambiguous parameter↔value association, implausible numbers (range sanity checks). | MUST |
| FR-LAB-9 | Verification UI: side-by-side original image crop + extracted editable value; user can correct, confirm. | MUST |
| FR-LAB-10 | Status computation per parameter: `WITHIN`, `BELOW`, `ABOVE`, `UNKNOWN` using the report's own range; parse ranges like `12-16`, `< 200`, `> 40`, `up to 5.0`. | MUST |
| FR-LAB-11 | Lab flags (H/L/HH/LL/*) preserved as `lab_flag`. | MUST |

#### 4.2.2 AI Analysis (button: "Check AI Medical Report Analysis")

| ID | Requirement | Priority |
|---|---|---|
| FR-AI-1 | Button appears after processing; opens expandable section/modal on same page. | MUST |
| FR-AI-2 | Overall summary: category, lab, date, counts (total / within / below / above / needs verification), key observations. | MUST |
| FR-AI-3 | Parameter table: name, value, unit, lab range, status, plain explanation, context. | MUST |
| FR-AI-4 | Observations: only from **verified** data; may mention related combined findings; must not diagnose (BR-04). | MUST |
| FR-AI-5 | Output validator: post-generation check rejects/regenerates text containing diagnosis phrases, treatment advice, dose advice (regex + LLM-judge list in `config/safety_rules.yaml`). | MUST |
| FR-AI-6 | Q&A assistant in-context; prompt includes verified report JSON + retrieved chunks; answers cite sources. | MUST |
| FR-AI-7 | Knowledge base: MedlinePlus, NIH, WHO, NHS, official lab docs → chunk → embed (Sentence Transformers) → FAISS. | MUST |
| FR-AI-8 | PDF summary download (ReportLab): patient/report details, lab info, parameters, ranges, observations, explanations, comparisons, doctor questions, disclaimer, sources. Extracted vs AI sections clearly labeled. | MUST |
| FR-AI-9 | "Questions to ask your doctor" generated list. | SHOULD |

#### 4.2.3 Prescription Pipeline

| ID | Requirement | Priority |
|---|---|---|
| FR-RX-1 | Preprocess image; segment text lines/regions; classify printed vs handwritten. | MUST |
| FR-RX-2 | Printed text → PaddleOCR; handwriting → TrOCR (or best evaluated alternative). | MUST |
| FR-RX-3 | Extract: doctor, clinic/hospital, patient, date, medicines, dosage/frequency, instructions, recommended tests. | MUST |
| FR-RX-4 | Medical vocabulary matching (fuzzy, rapidfuzz) against medicines + tests dictionaries, return top-k candidates with scores; never auto-substitute low-confidence. | MUST |
| FR-RX-5 | Abbreviation expansion (CBC→Complete Blood Count, LFT, KFT, TSH, HbA1c, etc.) from `abbreviations.json`. | MUST |
| FR-RX-6 | Verification UI: extracted text alongside original image, bounding-box highlight on uncertain words, editable fields. | MUST |
| FR-RX-7 | Confirmed tests sent to `test_recommendations` with status flow (Section 6). | MUST |
| FR-RX-8 | Button → `/tests` after confirmation. | MUST |

### 4.3 Module TEST — Test Recommendations & Centre Finder (Page 3, route `/tests`)

| ID | Requirement | Priority |
|---|---|---|
| FR-TEST-1 | List tests from verified prescriptions with source prescription link + status. User may edit/confirm test names. | MUST |
| FR-TEST-2 | Statuses: `IDENTIFIED`, `AWAITING_VERIFICATION`, `CONFIRMED`, `CENTRE_SEARCH_DONE`, `COMPLETED_BY_USER`. | MUST |
| FR-TEST-3 | Location priority: (1) profile preferred city, (2) clearly identified patient address from doc, (3) manual city/locality. User can always change (BR-06). | MUST |
| FR-TEST-4 | Search inputs: test, city, locality, postal code, distance. | MUST |
| FR-TEST-5 | Provider: Google Places API (primary) behind an interface `CentreProvider` so it can be swapped (e.g., OSM/Nominatim). | MUST |
| FR-TEST-6 | Result card: name, address, city/locality, phone, distance, rating/reviews, hours, website, booking link, test availability, price (only if reliable). | MUST |
| FR-TEST-7 | Mark info as `verified` / `unverified` (BR-12). Disclaimer: listing ≠ guaranteed availability. | MUST |
| FR-TEST-8 | Ranking score = weighted: availability (0.40), proximity (0.25), data completeness (0.15), ratings (0.10), price/convenience (0.10). Weights in config. | MUST |
| FR-TEST-9 | Compare view for 2–3 centres. | SHOULD |
| FR-TEST-10 | Interactive map (Leaflet/Google Maps) with markers, details popup, external-navigation link, change-location control. | MUST |
| FR-TEST-11 | User can mark test as completed manually (BR-08). | MUST |

### 4.4 Module HIST — Medical History & Comparison (Page 4, route `/history`)

| ID | Requirement | Priority |
|---|---|---|
| FR-HIST-1 | List all lab reports & prescriptions: name, lab, report date, upload date, category, status, AI-analysis availability. Search + filter by date/category/lab. | MUST |
| FR-HIST-2 | Per-document: view original, view extracted data, open prior analysis, view summary, download original, download PDF, delete. | MUST |
| FR-HIST-3 | Comparison: choose ≥2 reports → match by `parameter_id`, normalize compatible units (conversion table `unit_conversions.json`), absolute change, % change (only if baseline ≠ 0 and meaningful), flag changed reference intervals, list unmatched parameters. | MUST |
| FR-HIST-4 | Visuals (Recharts): line chart per parameter with ref-range band, timeline, previous-vs-current cards. | MUST |
| FR-HIST-5 | AI comparison summary: changed params, magnitude, still-out-of-range, newly in/out of range, non-comparable items, doctor questions. No "improved/worsened" (BR-09). | MUST |
| FR-HIST-6 | Prescription history: original, extracted text, verified tests, linked reports. | SHOULD |

### 4.5 Module PROF — Profile & Settings (Page 5, route `/profile`)

| ID | Requirement | Priority |
|---|---|---|
| FR-PROF-1 | Profile fields: full name, email, phone, DOB, gender (optional), preferred city, address (optional). | MUST |
| FR-PROF-2 | Upload historical documents: type, file, actual report date (required if not extracted), category, description. Runs same pipeline. | MUST |
| FR-PROF-3 | Consolidated records view (reports, prescriptions, summaries, comparisons, confirmed tests). | SHOULD |
| FR-PROF-4 | Settings: account (details, password, email/phone), location, notifications, privacy (view/delete docs, retention, account deletion, policy). | MUST |
| FR-PROF-5 | Auth: register, login, logout, password reset, sessions, protected routes, per-user data isolation. | MUST (Phase 4) |
| FR-PROF-6 | Guest mode: session-scoped data using a signed guest token; upgrade-to-account migrates session docs. | SHOULD |

## 5. API Specification (REST, FastAPI, prefix `/api/v1`)

| ID | Method & Path | Purpose |
|---|---|---|
| API-01 | `POST /documents` (multipart: file, doc_type) | Upload & queue processing → `{document_id, status}` |
| API-02 | `GET /documents/{id}` | Metadata + processing status |
| API-03 | `GET /documents/{id}/file` | Original file (auth-checked, signed URL) |
| API-04 | `GET /documents/{id}/extraction` | Extracted fields with confidence |
| API-05 | `PATCH /documents/{id}/extraction` | User corrections / verification |
| API-06 | `POST /documents/{id}/analysis` | Generate AI analysis (verified data only) |
| API-07 | `GET /documents/{id}/analysis` | Fetch analysis |
| API-08 | `POST /documents/{id}/chat` | Q&A about this document |
| API-09 | `GET /documents/{id}/summary.pdf` | Download PDF summary |
| API-10 | `DELETE /documents/{id}` | Delete document + derived data |
| API-11 | `GET /documents?type=&category=&lab=&from=&to=&q=` | History list |
| API-12 | `GET /recommendations` / `PATCH /recommendations/{id}` | List / confirm / edit / mark complete |
| API-13 | `POST /centres/search` | `{test_ids, city, locality, postal, radius}` → ranked centres |
| API-14 | `POST /comparisons` | `{document_ids[]}` → comparison result + summary |
| API-15 | `GET /dashboard` | Aggregated dashboard payload |
| API-16 | `POST /auth/register`, `/auth/login`, `/auth/logout`, `/auth/reset-password` | Auth |
| API-17 | `GET/PATCH /profile` | Profile |
| API-18 | `POST /profile/historical-documents` | Upload previous docs |
| API-19 | `GET /health` | Health check |

Processing is asynchronous: API-01 returns immediately; frontend polls API-02 (or SSE) until `status ∈ {EXTRACTED, NEEDS_VERIFICATION, FAILED}`.

Error format: `{ "error": { "code": "STRING", "message": "human text", "details": {} } }`.

## 6. Status Vocabularies (use exactly these enums)

- **Document status:** `UPLOADED → PREPROCESSING → OCR_RUNNING → EXTRACTING → NEEDS_VERIFICATION → VERIFIED → ANALYZED` ; terminal error: `FAILED`.
- **Parameter status:** `WITHIN`, `BELOW`, `ABOVE`, `UNKNOWN`.
- **Finding class:** `OUT_OF_RANGE`, `UNCERTAIN`, `URGENT`.
- **Recommendation status:** `IDENTIFIED`, `AWAITING_VERIFICATION`, `CONFIRMED`, `CENTRE_SEARCH_DONE`, `COMPLETED_BY_USER`.
- **Doc type:** `LAB_REPORT`, `PRESCRIPTION`.
- **Source tag on every field:** `EXTRACTED`, `USER_CORRECTED`, `AI_GENERATED`.

## 7. Data Model (PostgreSQL)

| ID | Table | Key columns |
|---|---|---|
| DB-01 | `users` | id (uuid), email (unique), password_hash, full_name, phone, dob, gender, preferred_city, address, created_at |
| DB-02 | `guest_sessions` | id, token_hash, created_at, expires_at |
| DB-03 | `documents` | id, user_id (nullable), guest_session_id (nullable), doc_type, original_filename, storage_key, mime, pages, status, lab_name, lab_address, report_category, report_date, collected_date, report_number, uploaded_at, description |
| DB-04 | `extraction_runs` | id, document_id, engine, version, started_at, finished_at, raw_json |
| DB-05 | `parameters` | id, document_id, parameter_id (canonical), name_raw, value_num, value_raw, unit, unit_normalized, ref_low, ref_high, ref_raw, lab_flag, status, finding_class, confidence, bbox_json, page_no, verified (bool), source_tag |
| DB-06 | `parameter_dictionary` | parameter_id, canonical_name, category, synonyms[], default_unit, plausible_min, plausible_max |
| DB-07 | `prescription_items` | id, document_id, item_type (MEDICINE/TEST/INSTRUCTION/META), text_raw, text_normalized, dosage, frequency, confidence, bbox_json, verified |
| DB-08 | `test_recommendations` | id, user_id/guest, prescription_id, test_name, canonical_test_id, status, created_at, completed_at |
| DB-09 | `analyses` | id, document_id, summary_json, observations_json, model, prompt_version, sources_json, created_at |
| DB-10 | `chat_messages` | id, document_id, role, content, sources_json, created_at |
| DB-11 | `comparisons` | id, user_id, document_ids[], result_json, summary_text, created_at |
| DB-12 | `centre_searches` | id, recommendation_id, city, locality, query_json, results_json, created_at |
| DB-13 | `kb_chunks` | id, source, url, title, text, embedding_ref |
| DB-14 | `audit_log` | id, user_id, action, entity, entity_id, at |

Indexes: `documents(user_id, report_date)`, `parameters(document_id)`, `parameters(parameter_id)`.

## 8. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | Single-page lab report (digital PDF) extraction ≤ 20 s; scanned ≤ 60 s on CPU target machine (indicative). |
| NFR-02 | Processing is async with visible progress; failures return friendly message + retry. |
| NFR-03 | HTTPS only; passwords hashed with argon2/bcrypt; JWT (httpOnly cookie) or secure sessions; CORS locked to frontend origin. |
| NFR-04 | Per-user document isolation enforced in every query. |
| NFR-05 | Secrets only in env vars; `.env.example` provided; never committed. |
| NFR-06 | Files in S3-compatible storage with signed, expiring URLs. |
| NFR-07 | Responsive UI (mobile ≥ 360px). Accessible (WCAG AA basics: contrast, labels, keyboard). |
| NFR-08 | Logging without PHI (no patient values in plain logs). |
| NFR-09 | Pipelines modular: each stage a separate class with defined input/output schema (Pydantic). |
| NFR-10 | Test coverage ≥ 70% on backend core logic (range parsing, normalization, comparison, ranking). |

## 9. Safety & Escalation

- `config/escalation_rules.yaml` lists parameter-specific critical thresholds (e.g., clinically-reviewed critical values). Only these can yield `URGENT`, and the UI text for URGENT is: *"This value is far outside the reference range. Please contact your doctor promptly."* — no diagnosis.
- LLM system prompt must include the prohibitions in BR-04, BR-11, and forbid medicine/dose advice.
- Prescription items never auto-corrected; show top-k candidates, user picks.

## 10. Evaluation Plan (maps to Section 14 of project spec)

| Component | Metric | Target (prototype) | Dataset |
|---|---|---|---|
| Printed OCR | CER/WER | CER < 3% on clean digital | 30+ reports |
| Handwriting | CER/WER | Report honestly; no target claim | 50+ prescriptions |
| NER | P/R/F1 | F1 ≥ 0.85 on lab params | annotated set |
| Parameter extraction | exact match | ≥ 90% | verified reports |
| Ref range extraction | accuracy | ≥ 90% | verified reports |
| Unit normalization | correct rate | ≥ 95% | unit test set |
| RAG | Precision@5 / Recall@5 | report | QA set (50 Qs) |
| Explanation | faithfulness/groundedness | manual rubric | 50 outputs |
| Comparison | numerical consistency | 100% on unit tests | synthetic |
| Centre discovery | relevance | manual rubric | 20 queries |

Clinical diagnostic accuracy is **not** claimed.

## 11. Out of Scope

HIS/EHR integration, booking/payments, real-time lab feeds, diagnosis, prescription generation, medicine purchase, teleconsultation, treatment recommendations, radiology/ECG, wearables, clinical decision support.

## 12. Assumptions & Open Decisions

| # | Item | Default if undecided |
|---|---|---|
| A1 | LLM provider | Anthropic/OpenAI-compatible API behind `LLMClient` interface |
| A2 | Maps provider | Google Places + Maps JS; fallback Leaflet + OSM |
| A3 | Hosting | Frontend Vercel, backend Render, Postgres managed, S3/R2 |
| A4 | Worker queue | FastAPI BackgroundTasks first; Celery/RQ+Redis if needed |
| A5 | Handwriting model | TrOCR-base-handwritten → evaluate fine-tuning / alternatives |
| A6 | Primary language | English reports/prescriptions (Indian labs focus) |
| A7 | Currency/locale | India (IST), metric units |
