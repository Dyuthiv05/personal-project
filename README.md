# Diabetes care, then and now

**Which diabetic patients did the old standard of care fail, has today's market caught up for them, and which prescribers should a newer-drug brand call on first?**

A pharmaceutical market-research case study built from one public hospital dataset and six data sources I pulled myself through public APIs. The analysis lives in six Jupyter notebooks; `docs/story.html` is the 15-minute presentation page built from their saved results.

## Data

| Source | How | Rows | Used for |
|---|---|---:|---|
| [Kaggle · Diabetes 130-US Hospitals, 1999–2008](https://www.kaggle.com/datasets/brandao/diabetes) | `kagglehub` download | 101,766 stays | Patient profiling, journey, readmission models |
| CMS Part D Prescribers by Provider & Drug, 2024 | data.cms.gov API | 2,231,207 | Prescriber segments, physician targeting |
| CMS Part D Spending by Drug, 2020–2024 | data.cms.gov API | 142 brands | Market map, spending trend |
| CMS Part D Prescribers by Geography & Drug, 2024 | data.cms.gov API | 6,615 | State adoption |
| CDC PLACES county data, 2025 release | data.cdc.gov (Socrata) API | 2,956 counties | Disease burden by state |
| NLM RxClass (ATC) | rxnav.nlm.nih.gov API | 48 ingredients | Drug → class mapping |
| openFDA Drugs@FDA | api.fda.gov | 19 ingredients | When each class arrived |

API clients are in `src/apis.py`. Each pull is cached in `data/raw/` (not committed) so the notebooks re-run offline.

## Notebooks

| # | Notebook | What it does | Runtime* |
|---|---|---|---:|
| 01 | `01_clean_hospital_data` | Removes deaths/hospice, keeps one stay per patient, groups ICD-9 codes, SQL summary | 5 s |
| 02 | `02_collect_market_data` | All API pulls, drug-class mapping, weight-loss brands excluded | 5 s (≈9 min first run) |
| 03 | `03_patient_profile_and_journey` | Readmission by patient characteristic (DuckDB SQL), A1C → med change → readmission journey | 4 s |
| 04 | `04_readmission_models_and_segments` | L1 logistic vs. random forest vs. neural network; permutation importance; decision-tree patient segments | 1.5 min |
| 05 | `05_market_today` | Then-vs-now treatment mix, 2020–2024 spending, specialty and state adoption vs. CDC burden | 5 s |
| 06 | `06_physician_targeting_and_recommendation` | k-means prescriber segments, ridge vs. random forest expected adoption, headroom, recommendation | 2.3 min |

\*Measured on an M-series MacBook with cached data. About 4 minutes end to end, plus ~9 minutes the first time for the CMS prescriber pull.

## Key findings

- **9.0%** of 69,987 diabetic patients were readmitted within 30 days. Patients with 3+ prior stays came back at **26.5%** (vs. 8.1% with none); patients discharged to a care facility at **15.1%** (vs. 6.9% home). Only **18%** had an A1C test during the stay.
- Readmission models reach ROC-AUC **0.64–0.66**; the neural network adds nothing over simpler models, and the random forest's top risk decile is readmitted at **2.3×** the average.
- GLP-1 and SGLT2 drugs went from **33% → 76%** of Medicare diabetes spending (2020–2024) but only **12% → 33%** of claims. In 1999–2008 hospital patients they were 0%.
- Family practice, internal medicine and nurse practitioners write **77%** of Medicare diabetes claims and trail endocrinology on the newer classes.
- Among 184K prescribers, the **top 20% hold ~76%** of the adoption headroom, and the "traditional orals" segment holds **~78%**. Florida and Ohio are high-burden, low-adoption and top-five for headroom.

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./run_all.sh                     # executes notebooks 01–06 in order, then builds docs/story.html
```

## Limitations

Medicare Part D covers mostly patients 65+. CMS suppresses rows under 11 claims. The hospital data is 1999–2008 and observational. Kentucky and Pennsylvania are missing from the 2025 CDC PLACES county release, so they drop out of the state-burden view only. Headroom compares each prescriber with look-alikes; a low share can be the right clinical choice.
