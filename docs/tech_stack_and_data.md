# FITSCAN - Technology, AI/ML and Data Storage Overview

FITSCAN is a web application that reads a printed lab report (PDF or photo), lets the user check every
value it extracted, and then explains the verified results in plain language with cited sources. It also
compares reports over time, shows dashboard charts, finds diagnostic centres nearby, and offers a site-wide
assistant chatbot. It gives general information only: it does not diagnose or prescribe.

---

## 1. Where the data is stored

All data stays on the machine running the backend. Nothing is sent to an outside service except the
specific calls listed in section 5.

| Data | Where it is stored (local development) | Production option |
|---|---|---|
| Structured data: users, documents, extracted values, analyses, comparisons, searches, audit log | SQLite database file `backend/fitscan.db` | PostgreSQL (`DATABASE_URL=postgresql+psycopg://...`) |
| Uploaded files (PDF / JPG / PNG) | Folder `backend/storage/documents/`, each file renamed to a random UUID (e.g. `7c804357-....pdf`) | S3-compatible object storage (AWS S3, MinIO, Cloudflare R2) with short-lived signed URLs (300 s) |
| Medical knowledge library (RAG source texts) | `backend/data/kb/kb_seed.yaml` + `kb_blood_tests.yaml` (81 articles: 69 MedlinePlus, 7 NIH ODS, 1 NHS, 4 FITSCAN glossary) | Same |
| Search index over the knowledge library | `backend/data/faiss_index/` (vectors + metadata) | Same |
| Lab-test dictionary (canonical names, synonyms, units, plausible limits) | `backend/data/dictionaries/*.json` | Same |
| Rules: safety filter, urgent-value rules, centre ranking, assistant answers | `backend/config/*.yaml` | Same |
| Login session | Browser cookie: `fitscan_auth` (JWT, account users) or `fitscan_guest` (guest session id) | Same |
| Assistant chat history | Browser `sessionStorage` only (cleared when the tab closes); not saved on the server | Same |

**Database tables (14):** `users`, `guest_sessions`, `documents`, `extraction_runs`, `parameters`,
`parameter_dictionary`, `analyses`, `chat_messages`,
`comparisons`, `centre_searches`, `kb_chunks`, `audit_log`. The schema is versioned with Alembic migrations.

**Retention and ownership**
- Every record belongs to either a registered user or a guest session. Users can only ever read their own
  data (enforced on every API request).
- Guest uploads are deleted automatically after 24 hours (`scripts/cleanup_guests.py`). When a guest
  registers, their uploads move into the new account.
- Users can delete any report, or their whole account, from the app.
- Passwords are stored only as bcrypt hashes. Login tokens are signed JWTs, valid for 24 hours.

---

## 2. Technology stack

### Frontend (what the user sees)
| Technology | Purpose |
|---|---|
| Next.js 15 (App Router) + React 19 | Web application framework, page routing |
| TypeScript 5 (strict mode) | Type-safe code |
| Tailwind CSS 3 + shadcn/ui-style components (class-variance-authority, tailwind-merge) | Styling and reusable UI parts |
| Recharts 3 | Dashboard charts and trend lines |
| Leaflet + React-Leaflet (OpenStreetMap tiles) | Map of nearby diagnostic centres |
| lucide-react | Icons |
| Playwright | End-to-end browser tests |

### Backend (server)
| Technology | Purpose |
|---|---|
| Python 3.11 | Language |
| FastAPI + Uvicorn | REST API (`/api/v1/...`) |
| Pydantic v2 + pydantic-settings | Request/response validation, configuration from `.env` |
| SQLAlchemy 2 + Alembic | Database access and schema migrations |
| SQLite (dev) / PostgreSQL (prod) | Database |
| boto3 | S3-compatible file storage (optional) |
| python-jose + bcrypt | JWT login tokens and password hashing |
| httpx | Calls to map and AI services |
| PyMuPDF | Reading PDFs: text layer and page images |
| OpenCV + Pillow + NumPy | Image clean-up before OCR (deskew, denoise, contrast) |
| RapidFuzz | Fuzzy matching of test names and medicine names |
| ReportLab | PDF summary download |
| PyYAML | Rule and knowledge files |
| pytest, pytest-cov, ruff, black | Testing, coverage, linting, formatting |

### Infrastructure / tooling
- Docker Compose file for optional PostgreSQL + MinIO (S3) services.
- GitHub Actions CI workflow (`.github/workflows/ci.yml`): lint, backend tests, frontend type-check.
- Start scripts: `scripts/dev_up.ps1` (Windows), `scripts/dev_up.sh` (Linux/macOS).

---

## 3. Architecture

```
Browser (Next.js)  --HTTPS/JSON-->  FastAPI  (api/)
                                       |
                                    services/        business rules, ownership, workflow
                                    /   |    \
                         pipelines/   rag/   integrations/        db/ (SQLAlchemy)
                         OCR, parsing  retrieval, LLM,  maps, AI API      |
                         (pure, no DB) safety filter                  SQLite / Postgres
                                                                   + file storage
```

Dependency rule: `api -> services -> pipelines | rag | integrations | db`. Pipelines are pure functions
(no database access), which makes them easy to test on synthetic documents.

**Lab report flow**
1. Upload: file type/size checked (PDF, JPG, PNG; up to 15 MB and 30 pages); content sniffed so a renamed
   file is rejected.
2. Read: digital PDFs use their text layer directly. Scans and photos are cleaned up with OpenCV, then OCR'd.
3. Parse: layout and table parsing finds rows of *test name - value - unit - reference range*. Lab
   name and report date are also read.
4. Normalise: test names are matched to a 142-test dictionary (694 synonyms, 14 categories) using exact and fuzzy matching. Units are normalised.
5. Compare: each value is compared with **the lab's own printed range**. The result is within, below or
   above, never a generic range.
6. Confidence: values with low OCR confidence, implausible numbers or unparsed ranges are flagged
   "needs your check".
7. User verification: the user corrects and confirms values. Only confirmed values go on to the analysis.
8. AI analysis: explanations, observations and doctor questions, each with cited sources, labelled AI-generated.
9. Extras: PDF summary, comparison across reports, dashboard charts, centre search.

---

## 4. AI and machine-learning components

The table shows exactly what runs in the current installation and what is optional.

| Component | Technique / model | Status |
|---|---|---|
| Printed-text OCR | **RapidOCR**: PaddleOCR's PP-OCR detection + recognition models run on **ONNX Runtime** (CPU) | **Active** |
| Alternative OCR engines | Full PaddleOCR, Tesseract | Optional (used automatically if installed) |
| Chatbot language model | **Google Gemini** (`gemini-3.5-flash`, falls back to `gemini-3.5-flash-lite` when busy) via the REST API | **Active** when `GEMINI_API_KEY` is set; replies pass the safety validator |
| Report explanations language model | **Anthropic Claude** (`claude-opus-5-5`) via the official SDK | Optional (`LLM_API_KEY`); offline template text otherwise |
| Image pre-processing | OpenCV: grayscale, denoising, adaptive thresholding, deskew | Active |
| Test-name normalisation | Dictionary of 142 blood tests with 694 synonyms + RapidFuzz fuzzy matching | Active |
| Range / status logic | Rule-based parser for ranges such as `12.0 - 15.0`, `< 40`, `Desirable: <200`; numeric comparison | Active (deterministic, no AI) |
| "Urgent" findings | Validated threshold rules in `config/escalation_rules.yaml`. The AI is never allowed to call a result urgent. | Active (rules, no AI) |
| Retrieval (RAG) | **TF-IDF** vectors (unigrams + bigrams), cosine similarity, parameter-aware boosting; index stored with NumPy/FAISS layout | **Active** |
| Better embeddings | `sentence-transformers` + `faiss-cpu` semantic search | Optional (auto-used if installed) |
| Large language model | **Anthropic Claude** (`claude-opus-5-5`) via the Anthropic Messages API, structured JSON output, versioned prompts | Optional: used when `LLM_API_KEY` is set. **Currently not set**, so FITSCAN uses its offline explanation templates. |
| Offline explanation engine | Deterministic templates built from the verified values, the lab ranges and the retrieved sources | Active (fallback / default) |
| Safety validator (guardrail) | Pattern rules in `config/safety_rules.yaml` block diagnosis, treatment/dose advice, test recommendations, urgency words and "improved/worsened" wording. Unsafe AI text is regenerated once, then replaced by the safe template. | Active on every AI output |
| Site assistant chatbot | Intent matching over a curated answer base (`config/assistant_faq.yaml`, 20 intents) + RAG over the knowledge library + LLM (if key set); safety intents (emergency, medicine advice, diagnosis) are answered first with fixed safe replies | Active |

**Responsible-AI rules built into the code**
- AI only sees **verified** values and the lab's ranges, never the patient's name or address.
- Every AI statement is labelled **AI-generated** and cites its sources, or says that no source was found.
- No diagnosis, no medicine or dose advice, no test recommendations, no urgency claims.
- Every page shows the disclaimer: FITSCAN does not diagnose or replace a doctor.

---

## 5. External services and APIs

| Service | Used for | Key needed | Status |
|---|---|---|---|
| OpenStreetMap **Nominatim** | Turning an address / PIN code into map coordinates, and keyword search for centres | No | Active (default) |
| OpenStreetMap **Overpass API** | Finding clinics, hospitals and labs within a radius | No | Active (falls back to Nominatim if overloaded) |
| OpenStreetMap map tiles | Map background in the browser | No | Active |
| **Google Places API (New)** | Better centre results with ratings, hours, phone numbers | Yes (`GOOGLE_PLACES_API_KEY`) | Built in; activates when a key is added. Falls back to OpenStreetMap on any error. |
| Google Maps links | "Directions", "Open in Google Maps", "See more on Google Maps" | No | Active |
| **Anthropic API** (Claude) | AI explanations, comparisons, assistant answers | Yes (`LLM_API_KEY`) | Built in; activates when a key is added |

**MCP (Model Context Protocol):** the FITSCAN application does **not** use MCP. The AI model is called
directly through the Anthropic API from the backend. The project was developed with the help of an
AI coding assistant (Claude Code), but MCP is not part of the running application.

---

## 6. Testing and evaluation

- **Backend:** about 216 automated tests (pytest; ~84 % code coverage). They cover parsing, range logic,
  safety rules, API flows, user isolation, the assistant, dashboard charts and centre search.
- **Frontend:** 6 Playwright end-to-end browser tests: upload -> verify -> analysis, analysis -> centres,
  assistant, dashboard charts, registration, file validation.
- **Evaluation on synthetic reports** (`evaluation/`; no real patient data is used anywhere):

| Measure | Result |
|---|---|
| Digital PDF reports: values, ranges, units extracted correctly | 100 % |
| Scanned/photographed reports: value recall | 80 % |
| Scanned reports: character error rate (CER) | 5.1 % |
| Knowledge retrieval hit rate | 1.0 |
| Unsafe AI outputs blocked by the safety validator | 18 / 18 |

---

## 6b. Reference datasets

Public, de-identified datasets are used to set data-driven sanity limits and to generate realistic synthetic benchmark
reports. They are never used to diagnose or to replace the lab's printed range.
- NHANES 2017-2018, 2011-2012 (thyroid) and 2005-2006 (B12, folate), from the US CDC (public domain)
- UCI Chronic Kidney Disease (India), UCI ILPD Indian Liver Patient Dataset, and UCI HCV data (all CC BY 4.0)

In total: 68 tests and 410,202 values. Per-test counts and sources are in `docs/datasets.md`. The launch steps are in
`docs/launch_checklist.md`.

## 7. Current limitations

- Only printed lab reports are accepted; the doctor's-prescription feature was removed.
- Without an Anthropic API key, explanations come from offline templates. They are accurate but less fluent.
- Without a Google Places key, centre data comes from OpenStreetMap, which has fewer phone numbers, hours and ratings.
- Test availability and prices at centres are not confirmed. The app tells users to call the centre.
- SQLite and local storage are for development. A real deployment should use PostgreSQL and S3 storage with HTTPS.


