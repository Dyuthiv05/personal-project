"""Small, cached clients for the public APIs this project collects from.

Every function saves what it downloads to data/raw/ and reuses that file on later runs,
so the notebooks can be re-run offline and the APIs are only hit once.
"""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

from .config import RAW

SESSION = requests.Session()
SESSION.headers["User-Agent"] = "personal-project diabetes market analysis (python-requests)"

CMS = "https://data.cms.gov/data-api/v1/dataset/{id}/data"
CMS_SPENDING_2024 = "7e0b4365-fd63-4a29-8f5e-e0ac9f66a81b"      # Part D Spending by Drug, 2020-2024
CMS_GEO_DRUG_2024 = "c8ea3f8e-3a09-4fea-86f2-8902fb4b0920"      # Part D Prescribers by Geography and Drug, 2024
CMS_PROVIDER_DRUG_2024 = "9552739e-3d05-4c1b-8eff-ecabf391e2e5"  # Part D Prescribers by Provider and Drug, 2024
CDC_PLACES_COUNTY_2025 = "swc5-untb"                             # PLACES county data, 2025 release
RXCLASS = "https://rxnav.nlm.nih.gov/REST/rxclass"
OPENFDA = "https://api.fda.gov/drug/drugsfda.json"


def _get(url, params=None, tries=4):
    for i in range(tries):
        r = SESSION.get(url, params=params, timeout=60)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 404:
            return None
        time.sleep(2 ** i)
    r.raise_for_status()


def cached(name: str):
    """Decorator: store a function's DataFrame result as data/raw/<name>[_<args hash>].parquet.

    The arguments are part of the file name, so asking for a different drug list
    never silently reuses an old download.
    """
    import hashlib

    def wrap(fn):
        def inner(*args, refresh=False, **kwargs):
            key = json.dumps([args, kwargs], sort_keys=True, default=str) if (args or kwargs) else ""
            suffix = "_" + hashlib.md5(key.encode()).hexdigest()[:8] if key else ""
            path: Path = RAW / f"{name}{suffix}.parquet"
            if path.exists() and not refresh:
                return pd.read_parquet(path)
            df = fn(*args, **kwargs)
            df.to_parquet(path, index=False)
            return df
        inner.__name__ = fn.__name__
        inner.__doc__ = fn.__doc__
        return inner
    return wrap


# ---------- CMS (data.cms.gov) ----------

def cms_pages(dataset_id: str, filters: dict | None = None, columns: list[str] | None = None, size=5000):
    """Page through one filtered CMS query and return every row."""
    params = {f"filter[{k}]": v for k, v in (filters or {}).items()}
    if columns:
        params["column"] = ",".join(columns)
    rows, offset = [], 0
    while True:
        page = _get(CMS.format(id=dataset_id), {**params, "size": size, "offset": offset}) or []
        rows += page
        if len(page) < size:
            return rows
        offset += size


@cached("cms_spending_by_drug")
def cms_spending_by_drug():
    """Medicare Part D spending, claims and beneficiaries per brand, 2020-2024 (all manufacturers combined)."""
    return pd.DataFrame(cms_pages(CMS_SPENDING_2024, {"Mftr_Name": "Overall"}))


@cached("cms_state_drug")
def cms_state_drug(generic_names: list[str]):
    """Part D claims per state for each listed generic name (2024)."""
    def one(g):
        return cms_pages(CMS_GEO_DRUG_2024, {"Prscrbr_Geo_Lvl": "State", "Gnrc_Name": g})
    with ThreadPoolExecutor(6) as ex:
        rows = [r for chunk in ex.map(one, generic_names) for r in chunk]
    return pd.DataFrame(rows)


@cached("cms_prescriber_drug")
def cms_prescriber_drug(generic_names: list[str]):
    """Every Part D prescriber's 2024 claims for each listed generic name (about 2.2M rows)."""
    cols = ["Prscrbr_NPI", "Prscrbr_Type", "Prscrbr_State_Abrvtn", "Brnd_Name", "Gnrc_Name",
            "Tot_Clms", "Tot_Benes", "Tot_Drug_Cst"]
    def one(g):
        return cms_pages(CMS_PROVIDER_DRUG_2024, {"Gnrc_Name": g}, cols)
    with ThreadPoolExecutor(8) as ex:
        rows = [r for chunk in ex.map(one, generic_names) for r in chunk]
    df = pd.DataFrame(rows)
    for c in ["Tot_Clms", "Tot_Benes", "Tot_Drug_Cst"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


# ---------- CDC PLACES (data.cdc.gov, Socrata) ----------

@cached("cdc_places_county")
def cdc_places_county(measures=("DIABETES", "OBESITY")):
    """Crude adult prevalence per county for the given PLACES measures."""
    where = "datavaluetypeid='CrdPrv' AND measureid in(" + ",".join(f"'{m}'" for m in measures) + ")"
    rows = _get(f"https://data.cdc.gov/resource/{CDC_PLACES_COUNTY_2025}.json",
                {"$where": where, "$limit": 50000,
                 "$select": "year,stateabbr,statedesc,locationname,locationid,measureid,data_value,totalpop18plus"})
    df = pd.DataFrame(rows)
    df["data_value"] = pd.to_numeric(df["data_value"])
    df["totalpop18plus"] = pd.to_numeric(df["totalpop18plus"])
    return df


# ---------- NLM RxClass (drug classes) ----------

@cached("rxclass_atc")
def rxclass_members(class_ids: list[str]):
    """Ingredients in each ATC class (e.g. A10BJ = GLP-1 analogues)."""
    out = []
    for cid in class_ids:
        js = _get(f"{RXCLASS}/classMembers.json", {"classId": cid, "relaSource": "ATC", "ttys": "IN"})
        info = _get(f"{RXCLASS}/class/byId.json", {"classId": cid})
        cname = info["rxclassMinConceptList"]["rxclassMinConcept"][0]["className"]
        for m in (js or {}).get("drugMemberGroup", {}).get("drugMember", []):
            c = m["minConcept"]
            out.append({"atc_id": cid, "atc_name": cname, "ingredient": c["name"].lower(), "rxcui": c["rxcui"]})
    return pd.DataFrame(out)


# ---------- openFDA (approval dates) ----------

@cached("openfda_first_approval")
def first_approvals(ingredients: list[str]):
    """Earliest original FDA approval date found for each ingredient (NDA/BLA applications)."""
    out = []
    for ing in ingredients:
        js = _get(OPENFDA, {"search": f'openfda.generic_name:"{ing}"', "limit": 100})
        dates = []
        for app in (js or {}).get("results", []):
            if not app["application_number"].startswith(("NDA", "BLA")):
                continue
            for s in app.get("submissions", []):
                if s.get("submission_type") == "ORIG" and s.get("submission_status") == "AP":
                    dates.append((s["submission_status_date"], app["application_number"],
                                  ", ".join(app.get("openfda", {}).get("brand_name", [])[:2])))
        if dates:
            d, appno, brand = min(dates)
            out.append({"ingredient": ing, "first_approval": pd.to_datetime(d), "application": appno, "brand": brand})
        time.sleep(0.3)
    return pd.DataFrame(out)


def save_json(obj, path: Path):
    path.write_text(json.dumps(obj, indent=2, default=str))
