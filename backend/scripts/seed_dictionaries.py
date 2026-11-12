"""Load data/dictionaries/parameters.json into the parameter_dictionary table (DB-06, P2)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.models import ParameterDictionary  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.utils import dictionaries  # noqa: E402

if __name__ == "__main__":
    with SessionLocal() as db:
        for pid, p in dictionaries.parameters().items():
            db.merge(ParameterDictionary(parameter_id=pid, canonical_name=p["canonical_name"], category=p["category"],
                                         synonyms=p["synonyms"], default_unit=p.get("default_unit"),
                                         plausible_min=p.get("plausible_min"), plausible_max=p.get("plausible_max")))
        db.commit()
    print(f"Seeded {len(dictionaries.parameters())} parameters")
