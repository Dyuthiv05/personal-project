# Where does a GLP-1 or SGLT2 drug pay for itself?

**Problem statement.** For which diabetic patients does adding a GLP-1 or SGLT2 drug pay for itself by preventing hospital stays, and what is that worth to a payer? The case is framed as a consulting engagement for a diabetes-drug manufacturer building its value case for Medicare plans and health systems.

**Answer.** With every dollar in 2026 terms, adding an SGLT2 drug at Medicare's negotiated price pays for itself through avoided hospital stays for diabetic patients with **at least one other hospital stay in the past year**: 11.7% of diabetic inpatients, who account for 20% of 30-day readmissions. About +$3,300 net per patient-year, or about $390,000 per 1,000 diabetic discharges. First-time patients are roughly break-even (−$92 a year). The 3.4% with **2+** prior stays are positive in every stress test. At gross 2024 prices, the case works only for that 2+ group. The result holds for Medicare-age patients alone, and the simple rule delivers about twice the value of picking patients with a readmission model.

**Reconciling the years.** The hospital data is 1999–2008, drug data 2013–2024, the trial 2015, and the prices 2026/27. All costs are converted to 2026 dollars with the BLS inpatient-hospital price index, and the cost of a stay is Medicare's own 2024 average payment (CMS inpatient data), cross-checked against AHRQ HCUP 2018 (both about $21,000 in 2026 dollars). The 1999–2008 readmission rates run below recent studies, so the patient side likely understates value. Notebook 06, section 0, has the full time-alignment table.

## The storyline: three parts, each feeding the next

| Part | Question | Output carried forward | Notebook |
|---|---|---|---|
| **A** | Who keeps coming back to hospital? | Each patient's hospital stays in the past 12 months, and a readmission risk score | 02 |
| **B** | What could change it, and what does it cost? | Annual cost of treatment: gross 2024 vs. Medicare negotiated price | 03 |
| **C** | Where does it pay for itself? | Break-even, net value by patient group, rule vs. model, sensitivity | 04 |

## Notebooks (5)

| # | Notebook | What it does |
|---|---|---|
| 01 | `01_data` | Every source: Kaggle cleaning, 4 API pulls, shared drug classifier, sample rows, privacy checks |
| 02 | `02_part_a_patients` | SQL profiling, A1C → meds → readmission journey, three readmission models, stays per year for every patient |
| 03 | `03_part_b_drugs` | 2013–2024 same-source trend, annual cost per patient (gross vs. negotiated) |
| 04 | `04_part_c_value` | Time reconciliation (2026 dollars), break-even, net value, rule vs. model, GLP-1 effect needed, sensitivity |
| 05 | `05_presentation` | **The presentation**: every word and chart of `docs/story.html`, previewed as Markdown |

## Data

| Source | How | Used for |
|---|---|---|
| [Kaggle · Diabetes 130-US Hospitals, 1999–2008](https://www.kaggle.com/datasets/brandao/diabetes) | `kagglehub` download | A: patients, readmissions, prior stays |
| CMS Part D Prescribers by Geography & Drug, national, 2013–2024 | data.cms.gov API (12 yearly files) | B: same-source trend in use and cost; gross cost per year |
| CMS Medicare Inpatient Hospitals by Geography & Service, 2024 | data.cms.gov API | C: what a hospital stay costs Medicare |
| BLS CPI, inpatient hospital services, 2017–2026 | api.bls.gov API | C: converts every dollar to 2026 |
| NLM RxClass (ATC) | rxnav.nlm.nih.gov API | One drug-class mapping for all data (`src/classes.py`) |
| `reference/assumptions.csv` | Sourced outside inputs | Trial effect (EMPA-REG, 11%), negotiated prices (CMS), HCUP cross-check, recent readmission benchmark, FDA approval years |

API clients: `src/apis.py`; raw pulls are cached in `data/raw/` (not committed). No patient-identifying information anywhere: the hospital data is de-identified, and every API source is a national total. Notebook 01 runs the privacy checks.

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./run_all.sh          # runs 01–05 in order; 05 writes docs/story.html
```

About 2 minutes with cached data; the first run adds about 2 minutes of API pulls.

## Limitations

The hospital data is 1999–2008 and observational (costs are aligned to 2026; patient patterns are checked against recent readmission rates). The 11% effect comes from a trial in patients with heart disease. Next year's admissions are assumed to match the past year (tested at 50%). Only hospital savings are counted. Gross Medicare cost is before confidential rebates.
