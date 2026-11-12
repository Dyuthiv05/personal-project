# For which patients does a GLP-1 or SGLT2 drug pay for itself?

**Problem statement.** For which diabetic patients does adding a GLP-1 or SGLT2 drug pay for itself by preventing hospital stays, and what is that worth to a payer? The case is framed as a consulting engagement for a diabetes-drug manufacturer building its value case for Medicare plans and health systems.

**Why the payer.** In the US, the doctor chooses the drug but the **payer** decides who can actually get it: formulary coverage, prior authorization, step therapy and copay. So the case is made to payers, through the manufacturer's market access team.

**Answer.** At Medicare's negotiated price, covering an SGLT2 drug pays for itself through avoided hospital stays for diabetic patients with **two or more hospital stays in the past year** (3.4% of diabetic inpatients): about +$2,800 per patient-year, or about $95,000 net per 1,000 diabetic discharges. Covering pays for itself up to about $313 a month for patients with 2 prior stays and $619 with 3+; with one prior stay it falls just short. The stay the patient is leaving is not counted. The result holds for Medicare-insured patients, for patients with heart disease, and if future stays are half the past; it fails at the trial's lowest effect and at 2024 gross prices.

**Reconciling the years.** The hospital data is 1999–2008, drug data 2013–2024, the trial 2015, and the prices 2026/27. Costs use Medicare's own share of the 2024 payment per stay, moved to 2026 dollars with the BLS inpatient-hospital price index, cross-checked against AHRQ HCUP 2018. Prior stays are checked against what happened after discharge.

## The storyline: three parts, each feeding the next

| Part | Question | Output carried forward | Notebook |
|---|---|---|---|
| **A** | Who keeps coming back to hospital? | Each patient's prior hospital stays, what happened after discharge, and a risk score | 02 |
| **B** | What could change it, and what does it cost? | Annual cost of treatment: gross 2024 vs. Medicare negotiated price | 03 |
| **C** | Where does covering it pay for itself, and what rule follows? | Break-even, tiered coverage rule and price, stress tests | 04 |

## Notebooks (5)

| # | Notebook | What it does |
|---|---|---|
| 01 | `01_data` | Every source: Kaggle cleaning, 4 API pulls, shared drug classifier, sample rows, privacy checks |
| 02 | `02_part_a_patients` | SQL profiling of who comes back, the A1C gap, three readmission models, stays per year for every patient |
| 03 | `03_part_b_drugs` | 2013–2024 same-source trend, annual cost per patient (gross vs. negotiated) |
| 04 | `04_part_c_value` | Cost of a stay in 2026 dollars, break-even, check against outcomes, tiered coverage rule and price, stress tests, rule vs. model, GLP-1 effect needed, who captures the savings |
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

About 1.5 minutes with cached data; the first run adds about 2 minutes of API pulls. Notebooks show tables only; every chart is drawn once, in the presentation.

## Limitations

The hospital data is 1999–2008 and observational (costs are aligned to 2026; patient patterns are checked against recent readmission rates). The 11% effect comes from a trial in patients with heart disease. Next year's admissions are assumed to match the past year (tested at 50%). Only hospital savings are counted. Gross Medicare cost is before confidential rebates.
