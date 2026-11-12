"""Write the synthetic sample documents (+ expected JSON) to evaluation/datasets/synthetic/.
Used for demos, E2E tests and evaluation. NO real patient data."""
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.fixtures.synthetic_reports import (  # noqa: E402
    LAYOUTS,
    render_pdf,
    render_png,
)

OUT = ROOT.parent / "evaluation" / "datasets" / "synthetic"

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for lo in LAYOUTS:
        (OUT / f"{lo.key}.pdf").write_bytes(render_pdf(lo))
        (OUT / f"{lo.key}_scan.png").write_bytes(render_png(lo))
        (OUT / f"{lo.key}.expected.json").write_text(json.dumps(
            {"meta": lo.meta, "parameters": [asdict(e) for e in lo.expected],
             "lines": [" ".join(r) for r in lo.rows + lo.second_page_rows]}, indent=2), encoding="utf-8")
    print(f"Wrote samples to {OUT}")
