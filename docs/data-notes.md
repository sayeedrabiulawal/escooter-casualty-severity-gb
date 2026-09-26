# Data Notes — Audit Trail

Keep this file up to date. If anyone ever questions the analysis, this is the
record of what was decided, when, and on what evidence.

---

## Snapshot record

| Item                    | Value                                                              |
| ----------------------- | ------------------------------------------------------------------ |
| Download date           | 2026-09-26                                                         |
| Release ingested        | September 2026 (last 5 years bundle, 2021-2025)                    |
| Files                   | collision 97.7 MB, vehicle 103.7 MB, casualty 53.7 MB              |
| Checksums               | see `data/raw/checksums.sha256`                                    |
| Derived dataset SHA-256 | `eb95fc2d5f27960a1a61ad7e64fe4125f73b08c069b677d48895acc1fe691634` |
| Derived dataset size    | 117.0 MB, 652,821 rows, 43 columns                                 |

Re-verify every fact below with `python src/inspect_escooter.py` before trusting it.

---

## RESOLVED - the design questions, with answers

### Q1. Which years carry the e-scooter code? -> ALL FIVE, via back-filling

The guide states `escooter_flag` was introduced in 2023 (vehicle table) and 2025
(casualty table). The actual September 2026 release has it populated for
**2021-2025 in both tables**.

**It has therefore been back-filled.** Two consequences:

1. Good news: the full five-year study period 2021-2025 is usable.
2. Important for the paper: **anyone using an older snapshot cannot reproduce this
   analysis.** That is a genuine novelty claim, and it must also be stated as a
   reproducibility limitation. Say both, and cite the download date.

### Q2. Exact code values (verified - do not guess these)

| Mode         | Field                    | Code               | Guide label                                                                                       |
| ------------ | ------------------------ | ------------------ | ------------------------------------------------------------------------------------------------- |
| E-scooter    | `casualty_escooter_flag` | 1                  | "Casualty was using an e-scooter"                                                                 |
| E-scooter    | `vehicle_escooter_flag`  | 1                  | "Vehicle was an e-scooter"                                                                        |
| E-scooter    | `vehicle_type`           | **33**             | "Personal powered transporter"                                                                    |
| Pedal cycle  | `vehicle_type`           | **1**              | "Pedal cycle"                                                                                     |
| Motorcycle   | `vehicle_type`           | 2, 3, 4, 5, 23, 97 | 50cc and under; 125cc and under; over 125cc to 500cc; over 500cc; electric motorcycle; unknown cc |
| **EXCLUDED** | `vehicle_type`           | **22**             | "Mobility scooter" - not an e-scooter                                                             |

The guide never uses the phrase "e-scooter" for `vehicle_type`; it says "Personal
powered transporter". Searching the guide for "e-scooter" finds only the flag
fields, which is exactly how the vehicle code is missed.

### Q3. Do the flag and vehicle_type agree? -> Perfectly, in one direction

| Combination                                           | Count |
| ----------------------------------------------------- | ----- |
| `vehicle_escooter_flag == 1` AND `vehicle_type == 33` | 6,786 |
| `vehicle_escooter_flag == 1` AND `vehicle_type != 33` | 0     |
| `vehicle_escooter_flag != 1` AND `vehicle_type == 33` | 115   |

So `flag == 1` always implies `type == 33`, but not the reverse. **Decision: use the
casualty-level flag as the primary definition**, because this is a casualty-level
study (5,631 casualties vs 6,786 vehicles). The 115-record difference is quantified
by `sensitivity_alternative_definition` in `src/analysis.py`.

At casualty level the nesting is exact: **5,631 of 5,631** e-scooter casualties sit on
a `vehicle_type == 33` vehicle. `src/dataset.py` asserts this and warns if it ever
stops being true.

### Q4. Injury-based reporting -> ANALYSED, and the finding survives

The release includes `casualty_injury_based` (1 = the force used injury-based
reporting), plus `casualty_adjusted_severity_serious` and
`casualty_adjusted_severity_slight`. These are the DfT's own severity adjustment
fields and are now used in three sensitivity analyses in `src/analysis.py`.

See the "Injury-based reporting" section below for the results and for the trap in
using the adjustment columns naively.

---

## Three bugs found and fixed in the pipeline

Recorded because all three would have silently corrupted the results, and none
raised an error - they produced plausible-looking output.

### 1. The vehicle join linked casualties to the wrong vehicle

`collision_index` is unique in the collision table but **not** in the vehicle table:
the average collision has about 1.8 vehicles. The original merge joined on
`collision_index` alone and called `drop_duplicates`, so every casualty was attached
to one **arbitrary** vehicle from their collision.

That is fatal for any vehicle-level variable. It surfaced as only 1,530 of 5,590
e-scooter casualties appearing to ride a `vehicle_type == 33` vehicle.

**Fix:** join on `collision_index` + `vehicle_reference`. Both tables carry
`vehicle_reference` precisely for this. After the fix, 100% of casualties match their
own vehicle and the e-scooter nesting check passes exactly.

### 2. Missing values are coded, not blank

STATS19 encodes missing data as integer sentinels, so `frame.isna()` reported **0.00%
missing on every field**. Left alone, `speed_limit` and `urban_or_rural_area` would
have gained a real category called `-1`, and the models would have reported a "-1
level" as though it meant something.

**Fix:** two passes in `apply_missing_sentinels`:

1. `-1` = "Data missing or out of range", applied across the analysis fields.
2. Field-specific unknown codes, **read from the data guide** rather than guessed.

A blanket check for 9/99 was tried first and produced false positives, because
`vehicle_type == 9` is "Car" and `10` is "Minibus". Reading each field's own labels
found genuine unknowns the heuristic had missed entirely - notably
`light_conditions == 7` ("Darkness - lighting unknown", 10,198 records).

Converted to NaN: `sex_of_driver` 9.99%, `vehicle_manoeuvre` 6.78%,
`junction_detail` 3.53%, `weather_conditions` 2.43%, `road_type` 2.17%,
`age_of_casualty` 2.16%, `light_conditions` 1.56%, smaller amounts elsewhere.

### 3. Dates were parsed without an explicit format, silently dropping 60% of rows

`pd.to_datetime(series, errors="coerce")` with no format guessed the wrong
convention on UK `DD/MM/YYYY` dates. Measured directly on this data: format-less
parsing succeeded on only **79,045 of 200,000** rows, while `format="%d/%m/%Y"`
succeeded on **200,000 of 200,000**.

The failures became `NaT`, so `year` became NaN, and `rq1_trends`'s
`dropna(subset=["mode", "year"])` then discarded them **in silence**. The trend
tables were computed on a ~40% subsample of the data without any warning.

**Fix:** always pass an explicit format for STATS19 dates. Implemented in
`dataset.py::add_derived_fields`. There is also a redundancy worth keeping: the
staging tables carry `collision_year` as an integer, which can be cross-checked
against the parsed date. They agree on all 652,821 rows.

**Blast radius:** only `rq1_trends` was affected, because it is the only analysis
that filters on the parsed year. The `urban_or_rural` result and every regression
are unchanged. The reported per-year counts and KASI proportions were wrong and have
been corrected below.

**How it was caught:** the IBR analysis reported 1,102 e-scooter casualties in 2021
while `rq1` reported 428 for the same year from the same frame. Two analyses of one
dataset disagreeing is the signal; neither would have failed on its own.

### 4. `openpyxl` was an undeclared dependency

`codes.py` and `prepare_data.py` read the DfT data guide `.xlsx`, so `openpyxl` is a
runtime requirement, not just a helper for the download step. It was missing from
`requirements.txt`, and a clean virtual environment therefore failed at
`codes.py` with `ImportError`. Added to `requirements.txt`.

---

## Findings (2026-09-26, full pipeline)

All figures below are from the run after the date-parsing fix. Earlier numbers were
computed on a partial subsample and have been corrected.

**Cohort sizes (casualties, 2021-2025):** e-scooter 5,631; pedal cycle 80,465;
motorcycle 82,953. Modellable total 148,320.

**RQ1 - counts are flat, severity is rising.** E-scooter casualty counts barely move
across five years:

| Mode        | 2021   | 2022   | 2023   | 2024   | 2025   |
| ----------- | ------ | ------ | ------ | ------ | ------ |
| E-scooter   | 1,102  | 1,154  | 1,117  | 1,096  | 1,162  |
| Pedal cycle | 16,895 | 16,155 | 15,506 | 15,149 | 16,760 |
| Motorcycle  | 16,192 | 17,355 | 17,306 | 16,326 | 15,774 |

So an "e-scooters are an exploding safety problem" framing is **not** supported by
collision counts. What moves is the KASI proportion, from 0.284 (2021, 95% CI
0.258-0.311) to 0.358 (2025) - converging on motorcycle levels, while pedal cycling
stays flat around 0.245-0.297.

**RQ2 - strongly urban.** 94.0% of e-scooter casualties are urban, versus 84.0% for
pedal cycles and 69.8% for motorcycles (chi-square 5,621 - but report the
proportions, not the p-value).

**RQ3 - within e-scooter determinants.** N = 5,056. Age dominates: 65+ has OR 5.24
(2.31-11.93) versus 0-15, and 45-54 has OR 1.96 (1.52-2.52). Male OR 1.53
(1.31-1.78). Urban OR 0.63 (0.49-0.82). Daylight OR 0.74 (0.65-0.85). Speed limit
is **not** significant within the e-scooter subset - worth discussing rather than hiding.

**RQ4 - the headline result.** Adjusted for age, sex, speed limit, light conditions,
road type, urban/rural and junction detail, reference category pedal cycle:

| Mode       | Odds ratio for KASI (95% CI) |
| ---------- | ---------------------------- |
| E-scooter  | **1.59 (1.49 - 1.69)**       |
| Motorcycle | 1.36 (1.33 - 1.39)           |

N = 148,320. Pseudo R-squared = 0.052.

This **contradicts the pre-specified H3**, which predicted e-scooter odds comparable
to or below pedal cycling. Report that honestly - a disconfirmed hypothesis stated
clearly is worth more than a vague one.

---

## Injury-based reporting (IBR): the confound, and why it does not break the result

### The confound is real and large

IBR adoption rises sharply through the study period:

| Year                       | 2021  | 2022  | 2023  | 2024  | 2025  |
| -------------------------- | ----- | ----- | ----- | ----- | ----- |
| Casualties from IBR forces | 38.1% | 40.5% | 41.1% | 79.1% | 85.8% |

A jump of this size means raw year-on-year severity comparisons are partly measuring
**who recorded the casualty** rather than how badly they were hurt. Worse, adoption
differs **by mode**: 27.9% of 2021 e-scooter casualties came from IBR forces versus
40.1% of pedal-cycle casualties. That is a mode-correlated measurement change, which
is precisely the kind that biases a cross-mode comparison.

### The trap in the DfT adjustment columns

`casualty_adjusted_severity_serious` is the probability of being **serious but NOT
fatal**. It is 0 for slight casualties and 0 for fatalities, and the two adjusted
columns sum to 1 for non-fatal casualties but to 0 for fatalities. Verified: all
8,033 fatalities have `adjusted_serious == 0.000000` exactly.

Taking that column directly as the outcome would score **every fatality as a
non-KASI case**, understating the adjusted KASI rate by 5.6% (0.2192 correct versus
0.2069 naive). The correct outcome adds fatalities back:

```
kasi_adj = (casualty_severity == 1) + casualty_adjusted_severity_serious
```

This yields an expected probability in [0, 1], so the models use a fractional
quasi-likelihood logit (Papke-Wooldridge) rather than standard logistic regression.
Implemented as `add_adjusted_outcome` in `src/analysis.py`.

### The central finding survives all three specifications

| Specification                          | E-scooter OR for KASI (95% CI) | Motorcycle OR         |
| -------------------------------------- | ------------------------------ | --------------------- |
| Model B, raw outcome                   | 1.587 (1.490 - 1.690)          | 1.360 (1.327 - 1.394) |
| Model B, DfT severity-adjusted outcome | **1.562 (1.468 - 1.663)**      | 1.342 (1.309 - 1.376) |
| Model B, IBR forces only (N = 95,662)  | **1.635 (1.502 - 1.780)**      | 1.463 (1.416 - 1.511) |

The odds ratio is stable between 1.56 and 1.64 across every specification. **The
finding is not an artefact of the reporting-method change.** That is the single
strongest robustness claim available in this study, and it should be stated
prominently in the abstract and discussion.

The rising e-scooter KASI proportion also survives adjustment (0.3006 in 2021 to
0.3614 in 2025), though the raw-to-adjusted gap shrinks from +0.0165 to +0.0034 as
IBR coverage approaches saturation.

**Caveat to keep:** restricting to IBR forces also changes which forces are in the
sample, so it is a different population, not merely a cleaner measurement of the
same one. Both the reduced power (2,946 e-scooter records) and the shifting force
composition belong in the limitations.

---

## Warning on interpretation (applies throughout)

These are police-reported casualties with **no exposure denominator**. A higher KASI
_proportion_ may reflect greater injury severity, or differential reporting of slight
injuries, or both. The paper cannot distinguish these, and must say so.

---

## Coding decisions log

Add a dated entry for every non-obvious decision. Format: date, decision, why.

| Date       | Decision                                                                | Rationale                                                                          |
| ---------- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| 2026-09-26 | Study scoped to GB; Northern Ireland excluded                           | Separate reporting system (PSNI), not in STATS19                                   |
| 2026-09-26 | Unit of analysis set to the casualty record                             | One row per injured person; avoids mixing casualty- and collision-level counts     |
| 2026-09-26 | Unknown-severity records retained in descriptives, excluded from models | Preserves the full denominator for trends; models need a defined outcome           |
| 2026-09-26 | Study period fixed at 2021-2025                                         | `escooter_flag` is populated for all five years in this release                    |
| 2026-09-26 | E-scooter cohort defined by `casualty_escooter_flag == 1`               | Correct unit for a casualty-level study; nests exactly inside `vehicle_type == 33` |
| 2026-09-26 | `vehicle_type == 22` (mobility scooter) excluded                        | Different vehicle class; conflating the two would be a basic error                 |
| 2026-09-26 | Model reference category set to pedal cycle                             | Most comparable mode to an e-scooter, so the headline OR is the most informative   |
| 2026-09-26 | Vehicle join uses `collision_index` + `vehicle_reference`               | `collision_index` alone is not unique in the vehicle table; see bug 1 above        |
| 2026-09-26 | Category labels read from the data guide, not hard-coded                | A regression table reading `[T.4.0]` is unpublishable; see `src/codes.py`          |
| 2026-09-26 | STATS19 dates parsed with an explicit `format="%d/%m/%Y"`               | Format-less parsing silently coerce-dropped 60% of rows; see bug 3 above           |
| 2026-09-26 | Severity-adjusted outcome = fatal flag + `adjusted_serious`             | `adjusted_serious` excludes fatalities and scores all 8,033 of them as 0           |
| 2026-09-26 | Adjusted-outcome models use a fractional logit, not a standard logit    | `kasi_adj` is an expected probability in [0, 1], not a 0/1 flag                    |
| 2026-09-26 | IBR handled as a sensitivity analysis, not by excluding affected forces | Excluding them would discard 56.6% of classified records and change the population |

---

## Known data quality issues to carry into the write-up

These are documented by DfT and must appear in the paper's limitations section.

- **Injury-based reporting (IBR).** Some police forces changed how severity is
  recorded, which altered the recorded severity mix. Adoption rose from 38.1% to
  85.8% of casualties over the study period. DfT provides severity adjustment
  factors. **This has now been tested** - see the IBR section above - and the
  headline finding is stable across all three specifications. Report the analysis,
  not merely the caveat.
- **`junction_detail` coding error.** The September 2025 release mis-coded
  "other junction" as "no data" in the 2024 files. Fixed from November 2025
  onward. If you use this variable, verify you have the corrected file.
- **`vehicle_location_restricted_lane`.** "Lay-by or hard shoulder" was
  incorrectly recoded as "no data" in 2024 data. Fixed July 2026.
- **Under-reporting.** Non-injury and minor collisions are systematically
  under-reported, and the degree varies by mode and by police force area. This
  affects cyclists and e-scooter riders particularly.

---

## Reproducibility

- [x] `src/download_data.py` re-creates the raw data from the DfT URLs
- [x] `src/fetch_data_guide.py` fetches the DfT code guide
- [x] `src/inspect_escooter.py` verifies the codes against the real data
- [x] `src/prepare_data.py` rebuilds the derived dataset and prints its hash
- [x] `openpyxl` declared in `requirements.txt` (was an undeclared runtime need)
- [ ] Package versions pinned in a lock file (`pip freeze > requirements-lock.txt`)
- [ ] Repository tagged `v1.0.0` and archived on Zenodo
- [ ] Raw data **not** uploaded to Zenodo - the script and checksums are sufficient

### Environment

This project runs in `.venv`. Use it explicitly, since the interpreter on `PATH` is a
different one and package installs aimed at it do not reach this environment:

```powershell
& .venv\Scripts\python.exe src/analysis.py
```

Verified working: Python 3.14.5, pandas 3.0.6, statsmodels 0.15.0, openpyxl 3.1.5.

---

## References consulted

Add a line for every document you read that informed a decision.

- DfT. _Road safety open data._ https://www.gov.uk/government/statistical-data-sets/road-safety-open-data
- DfT. _Open dataset data guide_ (XLSX). `[date accessed]`
- DfT. _Guide to severity adjustments for reported road casualty statistics._
- DfT. _Understanding historical road safety data._
- DfT. _Historical revisions data_ (CSV).
