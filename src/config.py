"""Shared paths, drug-class display order, and the results file every notebook writes to."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "docs" / "results.json"
for p in (RAW, PROCESSED):
    p.mkdir(parents=True, exist_ok=True)

# Drug-class display order: oldest standard of care first, newest last.
CLASS_ORDER = [
    "Biguanide (metformin)", "Sulfonylurea", "Thiazolidinedione", "Meglitinide", "Alpha-glucosidase inhibitor",
    "Insulin", "DPP-4 inhibitor", "SGLT2 inhibitor", "GLP-1 / GIP-GLP-1 agonist", "Amylin analog",
]


def update_results(section: str, payload):
    """Merge one notebook's headline numbers into docs/results.json (read by the presentation notebook)."""
    data = json.loads(RESULTS.read_text()) if RESULTS.exists() else {}
    data[section] = payload
    RESULTS.write_text(json.dumps(data, indent=2, default=str))
