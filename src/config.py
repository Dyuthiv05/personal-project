"""Shared paths, chart style and drug-class definitions used by every notebook."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "docs" / "figures"
RESULTS = ROOT / "docs" / "results.json"
for p in (RAW, PROCESSED, FIGURES):
    p.mkdir(parents=True, exist_ok=True)

# Chart palette (validated categorical order, light mode) and ink colors.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
SURFACE = "#fcfcfb"

# Drug-class display order: oldest standard of care first, newest last.
CLASS_ORDER = [
    "Biguanide (metformin)",
    "Sulfonylurea",
    "Thiazolidinedione",
    "Meglitinide",
    "Alpha-glucosidase inhibitor",
    "Insulin",
    "DPP-4 inhibitor",
    "SGLT2 inhibitor",
    "GLP-1 / GIP-GLP-1 agonist",
    "Amylin analog",
]
# Classes current ADA guidance prefers for patients with heart or kidney disease.
ADVANCED = {"SGLT2 inhibitor", "GLP-1 / GIP-GLP-1 agonist"}

# Brands of diabetes ingredients that are approved for weight loss, not diabetes.
WEIGHT_LOSS_BRANDS = {"Wegovy", "Zepbound", "Saxenda"}


def style():
    """Apply one consistent matplotlib look to every notebook chart."""
    import matplotlib as mpl

    mpl.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK2, "axes.titlecolor": INK,
        "axes.titleweight": "bold", "axes.titlesize": 12, "axes.titlelocation": "left",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
        "xtick.color": MUTED, "ytick.color": MUTED, "font.size": 10,
        "axes.prop_cycle": mpl.cycler(color=SERIES), "figure.dpi": 110,
        "legend.frameon": False,
    })


def update_results(section: str, payload):
    """Merge one notebook's headline numbers into docs/results.json (read by the story page)."""
    import json

    data = json.loads(RESULTS.read_text()) if RESULTS.exists() else {}
    data[section] = payload
    RESULTS.write_text(json.dumps(data, indent=2, default=str))
