# Where does a GLP-1 or SGLT2 drug pay for itself?

**Problem statement.** For which diabetic patients does adding a GLP-1 or SGLT2 drug pay for itself by preventing hospital stays, and what is that worth to a payer? The case is framed as a consulting engagement for a diabetes-drug manufacturer building its value case for Medicare plans and health systems.

**Answer.** At Medicare's negotiated prices, adding an SGLT2 drug pays for itself through avoided hospital stays for diabetic patients with **at least one other hospital stay in the past year**: 11.7% of diabetic inpatients, who account for 20% of 30-day readmissions. About +$1,800 net per patient-year, or about $214K per 1,000 diabetic discharges. The robust core is the 3.4% with **2+** prior stays, who stay at or near break-even in every stress test. At gross 2024 prices, the case fails for almost everyone.

## The storyline: three parts, each feeding the next

| Part | Question | Output carried forward | Notebooks |
|---|---|---|---|
| **A** | Who keeps coming back to hospital? | Each patient's hospital stays in the past 12 months, and a readmission risk score | 01, 03, 04 |
| **B** | What could change it, and what does it cost? | Annual cost of treatment: gross 2024 vs. Medicare negotiated price | 02, 05 |
| **C** | Where does it pay for itself? | Break-even, net value by patient group, rule sized per 1,000 discharges, sensitivity | 06 |

## Data

| Source | How | Used for |
|---|---|---|
| [Kaggle · Diabetes 130-US Hospitals, 1999–2008](https://www.kaggle.com/datasets/brandao/diabetes) | `kagglehub` download | A: patients, readmissions, prior stays |
| CMS Part D Prescribers by Geography & Drug, national, **2013–2024** | data.cms.gov API (12 yearly files) | B: same-source trend in use and cost |
| CMS Part D Spending by Drug, 2020–2024 | data.cms.gov API | B: spending by drug class |
| CMS Part D Prescribers by Provider & Drug, 2024 (2.2M rows) | data.cms.gov API | Appendix: prescribers and specialties |
| CMS Part D Prescribers by Geography & Drug, 2024 (by state) | data.cms.gov API | Appendix: state adoption |
| CDC PLACES county data, 2025 release | data.cdc.gov API | Appendix: disease burden by state |
| NLM RxClass (ATC) | rxnav.nlm.nih.gov API | One drug-class mapping for all data (`src/classes.py`) |
| openFDA Drugs@FDA | api.fda.gov | When each class arrived |
| `reference/assumptions.csv` | Sourced outside inputs | C: trial effect (EMPA-REG, 11%), cost per admission (AHRQ HCUP, $15,200), negotiated prices (CMS) |

API clients: `src/apis.py`; raw pulls are cached in `data/raw/` (not committed). No patient-identifying information anywhere: the hospital data is de-identified, and the CMS files are totals by prescriber, state or drug. Notebooks 01–02 run the privacy checks.

## Notebooks

| # | Notebook | Part |
|---|---|---|
| 01 | `01_clean_hospital_data` | A · clean, one stay per patient, privacy check |
| 02 | `02_collect_market_data` | B · all API pulls, shared drug classifier, sample rows, privacy check |
| 03 | `03_patient_profile_and_journey` | A · who is readmitted (DuckDB SQL), A1C → meds → readmission |
| 04 | `04_readmission_models_and_segments` | A · L1 logistic vs. random forest vs. neural network; risk deciles for every patient |
| 05 | `05_the_lever_use_and_cost` | B · 2013–2024 trend, spending, cost per patient-year |
| 06 | `06_value_of_treatment` | C · break-even, net value, rule per 1,000 discharges, sensitivity |
| 07 | `07_appendix_prescriber_targeting` | Appendix · prescriber segments and headroom |
| 08 | `08_build_presentation` | **The presentation**: every word and chart of `docs/story.html`, previewed as Markdown |

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./run_all.sh          # runs 01–08 in order; 08 writes docs/story.html
```

About 4–5 minutes with cached data; the first run adds about 10 minutes of API pulls.

## Limitations

The hospital data is 1999–2008 and observational. The 11% effect comes from a trial in patients with heart disease. Next year's admissions are assumed to match the past year (tested at 50%). Only hospital savings are counted. Gross Medicare cost is before confidential rebates.
