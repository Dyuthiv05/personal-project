"""Build docs/story.html (the presentation page) from docs/results.json.

Run after the notebooks:  python site/build_story.py
Every number on the page comes from results.json, which the notebooks write.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
results = json.loads((ROOT / "docs" / "results.json").read_text())

# Keep only what the page draws, so the page stays small.
m, t, pr, mo = results["market"], results["targeting"], results["profile"], results["models"]
data = {
    "cleaning": results["cleaning"],
    "sources": results["sources"],
    "profile": {k: pr[k] for k in ["overall_readmit", "a1c_tested_pct", "high_a1c_changed_pct", "heart_dx_pct",
                                   "heart_dx_readmit", "kidney_dx_pct", "journey", "profile"]}
               | {"prior": pr["by"]["Prior hospital stays (past year)"], "discharge": pr["by"]["Discharged to"],
                  "diagnosis": pr["by"]["Primary diagnosis"]},
    "models": mo,
    "market": {k: m[k] for k in ["by_year", "spend_by_class", "mix", "specialties", "national_advanced_pct",
                                 "states", "state_medians", "total_prescribers", "total_claims"]},
    "targeting": t,
    "kaggle_sample": results["kaggle_sample"],
    "api_samples": results["api_samples"],
    "privacy_api": results["privacy_api"],
}
html = (Path(__file__).parent / "story_template.html").read_text()
out = ROOT / "docs" / "story.html"
out.write_text(html.replace("/*__DATA__*/{}", json.dumps(data, separators=(",", ":"), default=str)))
print("wrote", out, f"{out.stat().st_size / 1024:.0f} KB")
