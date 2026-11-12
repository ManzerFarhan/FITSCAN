#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
(cd "$ROOT/backend" && .venv/bin/ruff check app scripts --select E,F,W --ignore E501)
(cd "$ROOT/frontend" && npm run typecheck)
