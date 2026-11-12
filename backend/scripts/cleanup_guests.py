"""Run the retention job once (cron: `0 * * * *  python scripts/cleanup_guests.py`). BR-15."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.services.retention_service import cleanup  # noqa: E402

if __name__ == "__main__":
    with SessionLocal() as db:
        print(cleanup(db))
