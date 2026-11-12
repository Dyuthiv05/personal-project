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
CMS_GEO_DRUG_2024 = "c8ea3f8e-3a09-4fea-86f2-8902fb4b0920"      # Part D Prescribers by Geography and Drug, 2024
RXCLASS = "https://rxnav.nlm.nih.gov/REST/rxclass"


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


def save_json(obj, path: Path):
    path.write_text(json.dumps(obj, indent=2, default=str))


# Part D Prescribers by Geography and Drug, one dataset per year (same columns every year).
CMS_GEO_DRUG_BY_YEAR = {
    2013: "9aec2a70-4ef2-438a-bc35-1747fe2492c9", 2014: "63099eb4-6c9e-4fec-8c9e-b6b132f1b7f4",
    2015: "73748d0b-2acb-420a-ac66-27d8e238fdc8", 2016: "c5b3c840-5eb2-4e4c-ac35-c30995dcb051",
    2017: "7863e41c-3f6f-4889-93a8-be65e9f3d073", 2018: "b083c9b6-b841-4676-8d0a-fb03ee1431a1",
    2019: "73a6335e-f16f-4c81-a84b-6b5a986e2bf8", 2020: "83891e77-99cf-4865-b60a-97703b916e09",
    2021: "7dda2a9d-034a-446a-b4b3-e1254e0127b2", 2022: "1fc57194-a51d-4864-aee6-de0889488151",
    2023: "3463648b-1971-478d-84ca-80cadc758153", 2024: CMS_GEO_DRUG_2024,
}


@cached("cms_national_by_year")
def cms_national_by_year(years: list[int]):
    """National Part D totals per brand for each year: same source and definitions across 2013-2024."""
    def one(y):
        rows = cms_pages(CMS_GEO_DRUG_BY_YEAR[y], {"Prscrbr_Geo_Lvl": "National"})
        return [{**r, "year": y} for r in rows]
    with ThreadPoolExecutor(6) as ex:
        rows = [r for chunk in ex.map(one, years) for r in chunk]
    df = pd.DataFrame(rows)
    for c in ["Tot_Prscrbrs", "Tot_Clms", "Tot_30day_Fills", "Tot_Drug_Cst", "Tot_Benes"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


# ---------- Medicare inpatient payments (data.cms.gov) ----------
CMS_INPATIENT_GEO_2024 = "2941ab09-8cee-49d8-9703-f3c5b854e388"   # Medicare Inpatient Hospitals by Geography and Service, 2024


@cached("cms_inpatient_national_2024")
def cms_inpatient_national():
    """National Medicare inpatient discharges and average payments for every DRG (2024)."""
    df = pd.DataFrame(cms_pages(CMS_INPATIENT_GEO_2024, {"Rndrng_Prvdr_Geo_Lvl": "National"}))
    for c in ["Tot_Dschrgs", "Avg_Submtd_Cvrd_Chrg", "Avg_Tot_Pymt_Amt", "Avg_Mdcr_Pymt_Amt"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


# ---------- BLS consumer price index (api.bls.gov, v2, no key needed) ----------
BLS = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
CPI_INPATIENT = "CUUR0000SEMD01"   # CPI-U, inpatient hospital services, US city average, not seasonally adjusted


@cached("bls_cpi")
def bls_series(series_id: str, start: int, end: int):
    """Monthly values of one BLS series (missing months, e.g. Oct 2025, are dropped)."""
    r = SESSION.post(BLS, json={"seriesid": [series_id], "startyear": str(start), "endyear": str(end)}, timeout=60)
    r.raise_for_status()
    rows = [{"year": int(x["year"]), "period": x["period"], "value": x["value"]}
            for x in r.json()["Results"]["series"][0]["data"] if x["period"].startswith("M") and x["period"] != "M13"]
    df = pd.DataFrame(rows)
    df = df[df.value != "-"].astype({"value": float})
    return df.sort_values(["year", "period"]).reset_index(drop=True)
