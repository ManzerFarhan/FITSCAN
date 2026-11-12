# FITSCAN API (v1)

Base URL `/api/v1`. Interactive docs: `http://localhost:8000/docs` (disabled in production).

**Auth model.** Every request belongs to an *owner*: a logged-in user (JWT in the httpOnly cookie `fitscan_auth`, or a
`Bearer` header) or a guest (signed token in the httpOnly cookie `fitscan_guest`, created automatically, expires after
`GUEST_RETENTION_HOURS`). Every query is scoped to the owner. Another owner's resources return **404**, not 403.

**Errors.** `{"error": {"code": "STRING", "message": "human text", "details": {}}}`.
Common codes: `VALIDATION_ERROR` (422), `NOT_FOUND` (404), `UNSUPPORTED_FORMAT` (415), `FILE_TOO_LARGE` (413),
`TOO_MANY_PAGES` (413), `PENDING_VERIFICATION` (409), `REPORT_DATE_REQUIRED` (409), `NOT_VERIFIED` (409),
`TEST_NOT_CONFIRMED` (409), `INVALID_TRANSITION` (409), `RATE_LIMITED` (429), `PROVIDER_UNAVAILABLE` (503).

| ID | Endpoint | Notes |
|---|---|---|
| API-01 | `POST /documents` multipart `file`, `doc_type`, opt. `report_date`, `category`, `description` | 202 `{document_id, status}`; processing is async. Magic-byte check, 15 MB, 30 pages. Rate limit 30/min |
| API-02 | `GET /documents/{id}` | Poll until `status` is in `EXTRACTED, NEEDS_VERIFICATION, VERIFIED, ANALYZED, FAILED` |
| API-03 | `GET /documents/{id}/file[?download=true]` | Streams the file (local) or 307 to a signed, expiring S3 URL |
| - | `GET /documents/{id}/pages/{n}.png` | Rendered page image for preview and verification crops |
| API-04 | `GET /documents/{id}/extraction` | Metadata with confidence, parameters (status, finding_class, confidence, issues, bbox, `needs_verification`) |
| API-05 | `PATCH /documents/{id}/extraction` | `{metadata?, parameters[{id, name_raw?, value_raw?, unit?, ref_raw?, parameter_id?, verified?, delete?}], new_parameters[], confirm, auto_check?}`. `confirm` requires a report date and every flagged value checked, unless `auto_check` is set (then doubtful values stay unverified and are left out of the analysis) |
| - | `POST /documents/{id}/reprocess` | Retry after a failure |
| API-06 | `POST /documents/{id}/analysis` | Verified values only. Returns summary, parameter rows (explanation, context, `explanation_source: AI_GENERATED`), observations, doctor questions, sources, model, prompt_version |
| API-07 | `GET /documents/{id}/analysis` | Latest analysis |
| API-08 | `POST /documents/{id}/chat` `{question}` / `GET /documents/{id}/chat` | Cited answers. Medicine/dose questions get a fixed refusal. Rate limit 20/min |
| API-09 | `GET /documents/{id}/summary.pdf` | ReportLab PDF; disclaimer on every page |
| API-10 | `DELETE /documents/{id}` | Cascades to derived data and the stored file |
| API-11 | `GET /documents?category=&lab=&from=&to=&q=&limit=&offset=` | `{items, total}`; dates filter on `report_date` (falls back to upload date) |
| API-12 | _(removed with the doctor's-prescription feature)_ | |
| API-13 | `POST /centres/search` `{test_names?, city?, locality?, postal_code?, radius_km?, lat?, lng?}`; `GET /centres/location` | **Log in to unlock** (guests get 401 `LOGIN_TO_UNLOCK`). Tests the user picked (or any centre). Returns origin, ranked results with `score_breakdown`, `verified`, `test_availability`, and a disclaimer |
| API-14 | `POST /comparisons` `{document_ids[2..10]}`; `GET /comparisons` | compared (points, deltas, % change, transitions, range changes), unmatched, non_comparable, summary |
| API-15 | `GET /dashboard` | cards, latest_report, important_findings (with change vs previous), charts, health_score (out of 10; `null` for guests - log in to unlock), bmi (optional, from the profile), notifications |
| API-16 | `POST /auth/register`, `/auth/login`, `/auth/logout`, `/auth/reset-password`, `/auth/reset-password/confirm`; `GET /auth/me` | Guest data migrates on login/register. Changing the password invalidates all tokens. Outside production, the reset token is returned as `dev_reset_token` (there is no email service) |
| - | `POST /assistant/chat` `{question, page?, document_id?, history[]}`; `POST /assistant/explain-term` | Site chatbot (Google Gemini when `GEMINI_API_KEY` is set). Chat is **log in to unlock** (401 `LOGIN_TO_UNLOCK` for guests); explain-term stays open for the review screen |
| API-17 | `GET/PATCH /profile`, `POST /profile/password`, `DELETE /profile` `{password}`, `DELETE /profile/documents`, `GET /profile/records` | Email change needs `current_password` |
| API-18 | `POST /profile/historical-documents` | Login required; `report_date` can't be in the future |
| API-19 | `GET /health` | `{status, database}` |
