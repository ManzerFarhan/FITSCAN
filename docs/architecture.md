# FITSCAN - Architecture

## Components

```
Browser (Next.js 15 App Router)
  /dashboard  /analysis  /tests  /history  /profile  /(auth)/*
      |  fetch with credentials (httpOnly cookie: guest token or JWT)
      v
FastAPI  /api/v1
  api/          thin routers, request validation, rate limits, owner scoping
  services/     document_service, findings, analysis_service, comparison_service, centre_service, assistant_service,
                health_score, dashboard_service, pdf_report_service, user_service, retention_service, audit
  pipelines/    pure functions: bytes / Pydantic in -> Pydantic out (no DB)
  rag/          ingest -> embeddings -> vector_store -> retriever; prompts, llm_client, safety_validator
  integrations/ CentreProvider: GooglePlacesProvider | OSMProvider (Overpass -> Nominatim fallback)
  db/           SQLAlchemy 2 models (DB-01..14), Alembic migrations
Storage: local dir or S3-compatible (signed URLs)      DB: SQLite (dev) / Postgres
```

## Lab report pipeline (FR-LAB-*)

```
upload -> magic-byte + size + page checks -> storage -> BackgroundTask
  load_document   PyMuPDF: native words per page (digital) or 220-DPI raster (scanned)
  enhance         grayscale, resize, denoise, CLAHE, deskew            [scanned only]
  printed OCR     PaddleOCR > RapidOCR (PP-OCR/ONNX) > Tesseract        [scanned only]
  group_lines     cluster words by vertical overlap; split cells on wide gaps
  table_parser    per-line cell classification (value / range / unit / flag / name);
                  header row, if found, gives column hints; works per page; rejects non-result lines
  normalizer      synonyms -> parameter_id (exact, filtered, fuzzy >= 0.86; short keys exact only)
  range_parser    "12-16", "<200", "up to 5", ">40", sex-specific (uses sex from the doc/profile), tiered
  status          WITHIN / BELOW / ABOVE / UNKNOWN from the lab's own range (BR-01)
  confidence      OCR conf x name-match score; sanity checks (plausible range after unit conversion,
                  decimal slip, missing/ambiguous) -> needs_verification
  metadata        lab name/address, patient, sex, report no., report/collection dates, category vote
-> parameters stored with source_tag EXTRACTED, finding_class via findings.classify
```

Scope: printed lab reports only. The doctor's-prescription feature (FR-RX-*: handwriting reading, test
recommendations) was removed on 2026-11-11.

## Analysis & safety (FR-AI-*, BR-02/04/05/10/11)

```
verified parameters only -> per-parameter retrieval (parameter-aware query + boost, score threshold)
  -> LLM available?  Claude (claude-opus-5-5, JSON-schema output, server-side refusal fallback)
                     -> safety_validator -> regenerate once with feedback -> else template
     no LLM          deterministic templates: what the test measures + value vs lab range + cited KB title
  -> URGENT rows get the fixed escalation text (rules file, never the LLM)
  -> Analysis row (model, prompt_version, sources); document -> ANALYZED
Chat: advice/dose questions -> fixed refusal; diagnosis questions -> "only a doctor can diagnose" + general info;
      no retrieved source -> "no source found" instead of guessing.
Site chatbot: safety intents -> app how-to intents -> knowledge library + Google Gemini (gemini-3.5-flash, lite model
      when busy; GEMINI_API_KEY) -> safety_validator; offline template answers when no key is set.
```

## Comparison (FR-HIST-3..5, BR-09)

Verified values with a parameter_id, grouped across selected reports (sorted by report date). Values are converted
to the latest report's unit through `unit_conversions.json` (generic and analyte-specific factors), or reported as
non-comparable. Outputs per parameter: points, absolute change, % change (none if the baseline is 0), direction
(higher/lower/unchanged), range-change flag and transition (newly inside/outside, still outside). The summary uses
neutral wording, and the validator blocks improved/worsened.

## Centre discovery (FR-TEST-*)

Location priority: profile city -> explicitly labelled *patient* address on a report -> manual (the lab
address is never used, BR-06). Tests are the ones the user picks (BR-07). Geocode -> provider search -> rank =
0.40 availability + 0.25 proximity + 0.15 completeness + 0.10 ratings + 0.10 convenience
(`config/ranking_weights.yaml`). `verified` only for Google listings that are operational with phone and address
(BR-12). Results are cached for 6 h.

## Status vocabularies

Document: UPLOADED -> PREPROCESSING -> OCR_RUNNING -> EXTRACTING -> NEEDS_VERIFICATION | EXTRACTED -> VERIFIED -> ANALYZED; FAILED.
(`EXTRACTED` = all fields confident but not yet confirmed. It is listed in BRD §5 as a terminal polling state.)

## Security & privacy (NFR-03..08)

bcrypt passwords; HS256 JWT in an httpOnly SameSite=Lax cookie (Secure in production) with a password fingerprint
(a password change revokes all sessions); CORS locked to `FRONTEND_ORIGIN`; per-IP rate limits on auth, upload,
analysis and chat; magic-byte upload validation; PHI-scrubbing log filter; signed S3 URLs; hourly retention job
(guests 24 h, per-user `retention_days`); account deletion cascades and removes stored files.
