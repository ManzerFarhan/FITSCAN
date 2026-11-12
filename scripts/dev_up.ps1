# Start FITSCAN locally on Windows (backend :8000, frontend :3000).
# First run: creates the venv, installs dependencies, migrates the DB, builds the KB index.
$root = Split-Path -Parent $PSScriptRoot
Set-Location "$root\backend"
if (-not (Test-Path .venv)) {
  python -m venv .venv
  .venv\Scripts\python.exe -m pip install -r requirements.txt
}
if (-not (Test-Path .env)) { Copy-Item ..\.env.example .env }
.venv\Scripts\alembic.exe upgrade head
.venv\Scripts\python.exe scripts\build_kb.py --tfidf
Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "-m uvicorn app.main:app --reload --port 8000"

Set-Location "$root\frontend"
if (-not (Test-Path node_modules)) { npm install }
if (-not (Test-Path .env.local)) { "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1" | Set-Content .env.local -Encoding utf8 }
npm run dev
