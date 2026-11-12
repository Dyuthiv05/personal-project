"""One drug-class mapping shared by every notebook (hospital data and CMS data use the same rules).

Classes come from the NLM RxClass API (ATC system). A few ingredients in the ATC
catch-all class A10BX are placed by mechanism. Combination products count toward
every class they contain, the same rule for the Kaggle drug columns and the CMS
generic names.
"""
from functools import lru_cache

from . import apis

ATC = ["A10A", "A10BA", "A10BB", "A10BF", "A10BG", "A10BH", "A10BJ", "A10BK", "A10BX"]
ATC_TO_CLASS = {"A10A": "Insulin", "A10BA": "Biguanide (metformin)", "A10BB": "Sulfonylurea",
                "A10BF": "Alpha-glucosidase inhibitor", "A10BG": "Thiazolidinedione", "A10BH": "DPP-4 inhibitor",
                "A10BJ": "GLP-1 / GIP-GLP-1 agonist", "A10BK": "SGLT2 inhibitor"}
OVERRIDE = {"tirzepatide": "GLP-1 / GIP-GLP-1 agonist", "pramlintide": "Amylin analog",
            "repaglinide": "Meglitinide", "nateglinide": "Meglitinide"}
NOT_A_DRUG = ("pump", "device", "supplies", "pen,reusable", "pmp", "syr", "needle")
NEWER = ("GLP-1 / GIP-GLP-1 agonist", "SGLT2 inhibitor")
WEIGHT_LOSS_BRANDS = {"Wegovy", "Zepbound", "Saxenda"}


@lru_cache(maxsize=1)
def ingredient_table():
    """ingredient key -> class, from RxClass (cached on disk by src.apis)."""
    rx = apis.rxclass_members(ATC)
    rx["drug_class"] = rx.ingredient.map(OVERRIDE).fillna(rx.atc_id.map(ATC_TO_CLASS))
    rx = rx.dropna(subset=["drug_class"])
    out = {}
    for ing, cls in zip(rx.ingredient, rx.drug_class):
        key = " ".join(ing.replace(",", "").split()[:2]) if ing.startswith("insulin") else ing.split()[0]
        out[key] = cls
    return out


def classes_of(name: str) -> list[str]:
    """Every class in a drug name. Works for CMS generic names ('Empagliflozin/Metformin HCl')
    and Kaggle drug columns ('glyburide-metformin'). Returns [] for supplies and non-diabetes drugs."""
    n = name.lower()
    if any(w in n for w in NOT_A_DRUG):
        return []
    table = ingredient_table()
    found = []
    for part in n.replace("-", "/").split("/"):
        part = part.strip().replace(",", " ")
        if not part:
            continue
        if part.startswith("insulin"):
            found.append("Insulin")
            continue
        cls = table.get(part.split()[0])
        if cls:
            found.append(cls)
    if "lixisenatide" in n or "liraglutide" in n:
        found.append("GLP-1 / GIP-GLP-1 agonist")
    return list(dict.fromkeys(found))


def is_newer(name: str) -> bool:
    """True if the product contains a GLP-1 or SGLT2 component."""
    return any(c in NEWER for c in classes_of(name))

PRIORITY = ["GLP-1 / GIP-GLP-1 agonist", "SGLT2 inhibitor", "DPP-4 inhibitor", "Insulin", "Amylin analog",
            "Thiazolidinedione", "Sulfonylurea", "Meglitinide", "Alpha-glucosidase inhibitor", "Biguanide (metformin)"]


def primary_class(name: str):
    """One class per product for market-share charts: the newest class it contains."""
    found = classes_of(name)
    return next((c for c in PRIORITY if c in found), None)
