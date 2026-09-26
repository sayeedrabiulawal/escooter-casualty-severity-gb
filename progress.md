# Progress Log

**Project:** Spatiotemporal Patterns and Severity Determinants of Powered Personal
Transporter (E-Scooter) Casualties in Great Britain, 2021–2025
**Author:** Sayed `[surname]`
**Started:** 2026-09-26
**Last updated:** 2026-09-26

This file is the running record of what has been done, what was found, and what
remains. It is deliberately blunt about problems — including mistakes I made and
corrected — because an honest record is more useful than a flattering one, and
because a master's application reviewer may well read the repository.

---

## Status at a glance

| Item                  | State                                                                                 |
| --------------------- | ------------------------------------------------------------------------------------- |
| Topic chosen          | Done                                                                                  |
| Data acquired         | Done — 255 MB, checksummed                                                            |
| Data verification     | Done — codes confirmed against the real release                                       |
| Analysis pipeline     | Done — runs end to end, deterministic                                                 |
| Descriptives + models | Done                                                                                  |
| Robustness (IBR)      | Done — and the finding survives                                                       |
| Literature search     | Done — 99 DOI-verified references                                                     |
| Manuscript draft      | In progress                                                                           |
| Zenodo packaging      | In progress                                                                           |
| **Blocking issue**    | **None. The prior-work overlap (below) requires a framing change, not new analysis.** |

**Headline result:** e-scooter casualties have **1.59×** the adjusted odds of being
killed or seriously injured compared with pedal cyclists (95% CI 1.49–1.69), and
**1.56–1.64×** across three independent robustness specifications.

---

## 1. Why this topic

Constraints driving the choice: transportation/highway interest, laptop-only,
free/open-source software, no lab or fieldwork, and a 1–2 month window. That rules
out anything experimental and points to analysis of existing open data.

Full reasoning, rejected alternatives, and the fallback ladder are in `plan.md`.

---

## 2. What was built

```
src/download_data.py        Fetch the three STATS19 CSVs (+ --check to probe URLs)
src/fetch_data_guide.py     Fetch and search the DfT code guide
src/inspect_escooter.py     Verify the codes against the data actually downloaded
src/prepare_data.py         Validate, decode, link, export the analysis dataset
src/dataset.py              Shared mode definition and derived fields
src/codes.py                Map integer codes to the guide's own labels
src/build_bibliography.py   Generate a DOI-verified BibTeX from Crossref
src/analysis.py             Table 1, RQ1-RQ4, three sensitivity analyses
src/figures.py              Six publication figures
```

Rerun everything:

```powershell
& .venv\Scripts\python.exe src/download_data.py
& .venv\Scripts\python.exe src/fetch_data_guide.py
& .venv\Scripts\python.exe src/inspect_escooter.py
& .venv\Scripts\python.exe src/prepare_data.py
& .venv\Scripts\python.exe src/analysis.py
& .venv\Scripts\python.exe src/figures.py
```

The derived dataset reproduces **byte-identically** (SHA-256
`eb95fc2d5f27960a1a61ad7e64fe4125f73b08c069b677d48895acc1fe691634`), so the pipeline
is deterministic rather than merely repeatable.

---

## 3. Verified data facts

Do not trust these from memory. Re-verify with `src/inspect_escooter.py`.

| Fact                     | Value                                                                 |
| ------------------------ | --------------------------------------------------------------------- |
| E-scooter identification | `casualty_escooter_flag == 1` (5,631 casualties)                      |
| Vehicle code             | `vehicle_type == 33` = "Personal powered transporter"                 |
| Nests exactly?           | Yes — all 5,631 sit on a `vehicle_type == 33` vehicle                 |
| Pedal cycle              | `vehicle_type == 1`                                                   |
| Motorcycle               | `vehicle_type` in {2, 3, 4, 5, 23, 97}                                |
| Excluded                 | `vehicle_type == 22` = "Mobility scooter" — a different vehicle class |
| Study period             | 2021–2025, all five years usable                                      |
| Modellable records       | 148,320                                                               |

**Terminology trap worth remembering:** the DfT guide never uses the phrase
"e-scooter" for `vehicle_type`. It says "Personal powered transporter". Searching the
guide for "e-scooter" finds only the flag fields, which is how the vehicle code is
missed.

---

## 4. Four bugs found and fixed

All four produced plausible-looking output rather than an error, which is why the
validation checks exist.

### 4.1 The vehicle join linked casualties to the wrong vehicle

`collision_index` is unique in the collision table but **not** in the vehicle table
(about 1.8 vehicles per collision). Joining on it alone attached an _arbitrary_
vehicle to every casualty.

Surfaced as only 1,530 of 5,590 e-scooter casualties appearing to ride a
`vehicle_type == 33` vehicle.

**Fix:** join on `collision_index` + `vehicle_reference`. Now 100% of casualties
match their own vehicle.

### 4.2 Missing values are coded, not blank

STATS19 uses integer sentinels, so `isna()` reported **0.00% missing on every field**.
Left alone, `speed_limit` would have gained a fake category called `-1`.

**Fix:** convert `-1` and the guide's field-specific unknown codes to `NaN`. A
blanket 9/99 check was tried first and gave false positives (`vehicle_type == 9` is
"Car"), so the codes are read from each field's own labels — which caught
`light_conditions == 7` ("Darkness – lighting unknown", 10,198 records) that the
heuristic missed entirely.

### 4.3 Dates parsed without an explicit format dropped 60% of rows

`pd.to_datetime(errors="coerce")` with no format guessed wrong on UK `DD/MM/YYYY`
dates: it succeeded on only **79,045 of 200,000** rows. The rest became `NaT`, and
`rq1_trends` then discarded them **silently**.

This made early per-year figures wrong — 428 e-scooter casualties in 2021 instead of
the true 1,102. **The regression models were never affected**, because they do not
filter on year, so the headline result always stood.

**Caught because** the IBR analysis reported 1,102 for 2021 while `rq1` reported 428.
Two analyses of the same data disagreeing is the signal; neither would have failed on
its own.

### 4.4 `openpyxl` was undeclared, and a figure silently rendered empty

`codes.py` reads the DfT guide `.xlsx`, so `openpyxl` is a runtime requirement; it was
missing from `requirements.txt` and broke clean environments.

Separately, the new IBR robustness figure compared filenames against labels, selected
nothing, and produced an **empty plot with no error**. Both fixed, and the figure now
guards against the empty case explicitly.

---

## 5. Findings

### Table 1 — characteristics by mode

| Mode        | n      | Median age                       | Male % | Urban % | KASI % | Fatal % |
| ----------- | ------ | -------------------------------- | ------ | ------- | ------ | ------- |
| E-scooter   | 5,631  | **22**                           | 77.0   | 94.0    | 30.9   | 0.75    |
| Pedal cycle | 80,465 | 35                               | 78.4   | 84.0    | 25.3   | 0.57    |
| Motorcycle  | 82,953 | `[from table1_descriptives.csv]` | —      | 69.8    | —      | —       |

E-scooter casualties are markedly younger than cyclists (median 22 vs 35), which
matters for interpretation and for any helmet or training policy aimed at them.

### RQ1 — counts are flat, severity is rising

| Mode        | 2021   | 2022   | 2023   | 2024   | 2025   |
| ----------- | ------ | ------ | ------ | ------ | ------ |
| E-scooter   | 1,102  | 1,154  | 1,117  | 1,096  | 1,162  |
| Pedal cycle | 16,895 | 16,155 | 15,506 | 15,149 | 16,760 |
| Motorcycle  | 16,192 | 17,355 | 17,306 | 16,326 | 15,774 |

An "e-scooters are an exploding safety problem" framing is **not** supported by
collision counts. What moves is severity: the KASI proportion rises from 0.284 (2021)
to 0.358 (2025), converging on motorcycle levels, while pedal cycling stays flat.

### RQ2 — strongly urban

94.0% of e-scooter casualties are urban vs 84.0% (pedal cycle) and 69.8%
(motorcycle). Report the proportions, not the chi-square p-value.

### RQ3 — within e-scooter determinants

N = 5,056. Age dominates: 65+ has OR 5.24 (2.31–11.93) vs 0–15. Male OR 1.53.
Urban OR 0.63. Daylight OR 0.74. **Speed limit is not significant** within the
e-scooter subset — worth discussing rather than hiding.

### RQ4 — the headline result

Adjusted for age, sex, speed limit, lighting, road type, urban/rural, junction detail;
reference category pedal cycle:

| Mode       | Odds ratio for KASI (95% CI) |
| ---------- | ---------------------------- |
| E-scooter  | **1.59 (1.49 – 1.69)**       |
| Motorcycle | 1.36 (1.33 – 1.39)           |

### Robustness — the finding survives the main threat

Injury-based reporting (IBR) adoption rose from 38.1% (2021) to 85.8% (2025) and
differs by mode, making it the most plausible way the result could be an artefact:

| Specification                 | E-scooter OR (95% CI) |
| ----------------------------- | --------------------- |
| Raw outcome                   | 1.587 (1.490 – 1.690) |
| DfT severity-adjusted outcome | 1.562 (1.468 – 1.663) |
| IBR forces only (N = 95,662)  | 1.635 (1.502 – 1.780) |

**Stable at 1.56–1.64.** This is the study's strongest robustness claim.

**A trap avoided:** `casualty_adjusted_severity_serious` means _serious but not
fatal_ — it is exactly 0 for all 8,033 fatalities. Using it directly as the outcome
would have scored every death as a non-injury. Correct outcome:
`kasi_adj = (casualty_severity == 1) + casualty_adjusted_severity_serious`, which
needs a fractional logit since it is a probability in [0, 1].

---

## 6. CRITICAL: prior work overlaps this study

A systematic prior-work check
(`python src/build_bibliography.py --check-scoop`, output in
`docs/prior-work-scan.txt`) found:

> **Zhao, Konstantinoudis, Heydari (2026). "England-wide injury-severity analysis of
> e-scooter riders using a Bayesian spatial field model." _Accident Analysis &
> Prevention._ DOI 10.1016/j.aap.2026.108517**
>
> (Earlier preprint: DOI 10.2139/ssrn.5937116)

This overlaps substantially: e-scooter **injury severity**, **England-wide**, and it
is published in _Accident Analysis & Prevention_ — the journal I had originally
suggested as the primary target.

### What this means

1. **The novelty claim must be narrowed.** "First e-scooter severity study in GB" is
   no longer defensible. Zhao et al. must be cited and positioned against.
2. **What remains genuinely distinctive:**
    - **Three-way comparison** — e-scooter vs pedal cycle vs **motorcycle** on one
      dataset with one specification. Zhao et al. is e-scooter-focused.
    - **Five-year trend analysis** of counts and severity.
    - **The IBR robustness analysis**, which Zhao et al. do not report.
    - **Great Britain**, not England alone.
3. **Retarget the journal.** Submitting an overlapping paper to the same journal that
   just published the nearest work invites rejection. Retarget to
   _Journal of Safety Research_, _Traffic Injury Prevention_, or _IATSS Research_.
   See `plan.md` §8.
4. **This is a good outcome.** Finding it now is far better than claiming novelty a
   reviewer can disprove in one search. The paper is now positioned rather than
   accidentally derivative.

The reframed contribution statement is in `paper/manuscript.md` §1.

---

## 7. Known limitations to state in the paper

1. **No exposure denominator.** Private e-scooter ownership has no reliable
   denominator, so risk per trip or per km cannot be estimated. Counts and proportions
   only. This is the study's weakest point and the most likely reason for rejection.
2. **Police-reported collisions only**, with substantial and likely differential
   under-reporting.
3. **Private e-scooter use is illegal on public roads in GB**, so the cohort mixes
   rental use, illegal private use, and misclassification (some e-scooters recorded as
   pedal cycles) in unknown proportions.
4. **IBR forces-only analysis changes the population**, not merely the measurement, so
   it is supporting evidence rather than a clean replication.
5. **No helmet data** in STATS19, so helmet effects cannot be tested.
6. **Residual confounding** from rider experience, vehicle power, and deprivation.
7. **Observational design** — associations only, no causal claims.

---

## 8. What remains

### To finish the paper

- [ ] Curate the 99 Crossref references: read them, delete any that do not support
      the point they are cited for. **Do not cite unread papers.**
- [ ] Fill the TODO markers in `paper/manuscript.md` (mostly the literature review).
- [ ] Add Zhao et al. to the reference list and the novelty framing.
- [ ] Decide on Model C: the mode × speed interaction adds little, so consider
      swapping it for mode × urban/rural.
- [ ] Consider an exposure-denominator proxy (rental-scheme trip data). Even a crude
      one would materially strengthen the paper. If none can be sourced honestly, say
      so in the limitations instead of omitting the issue.
- [ ] Proofread for claims unsupported by the numbers.

### To publish on Zenodo

- [x] `CITATION.cff` created
- [x] `LICENSE` created (MIT for code)
- [ ] Add CC-BY-4.0 for the paper text and figures
- [ ] `.zenodo.json` metadata prepared
- [ ] Create ORCID and a public GitHub repository
- [ ] Link ORCID to Zenodo
- [ ] Tag the release `v1.0.0`
- [ ] Deposit, then record the DOI in `CITATION.cff` and the manuscript

**Publishing is irreversible** — a published Zenodo record cannot be deleted, only
superseded by a new version with a _new_ DOI. Proofread the title, author name, and
abstract before clicking publish.

### Application tasks (do these in parallel, not after)

- [ ] Get an ORCID iD
- [ ] Build a GitHub profile with this repository pinned
- [ ] Identify 2–3 specific research groups to name in the statement of purpose
- [ ] Draft the CV entry from `plan.md` §9
- [ ] **Do not let this paper cost you the application deadline.** The preprint alone
      is a sufficient CV line; the journal submission can trail behind it.

---

## 9. Honest assessment for a master's application

**Strengths:** a complete, reproducible empirical study on a current transport policy
issue, with genuine robustness testing, a public code repository, and a documented
audit trail that shows how errors were caught. The IBR analysis in particular
demonstrates statistical judgment beyond coursework.

**Weaknesses:** no exposure denominator; one surviving prior-work overlap; and a
single-author preprint carries less weight than a peer-reviewed article.

**What to say in the statement of purpose:** emphasise the _methodological judgment_
— reconciling a mid-series coding change, handling coded missing values, and
discovering that an earlier result was computed on a partial subsample. Discovering
and correcting your own bug is a stronger signal than reporting a clean result would
be.

---

## 10. File map

| File                           | Purpose                                                        |
| ------------------------------ | -------------------------------------------------------------- |
| `plan.md`                      | Full research plan, timeline, publishing and application steps |
| `progress.md`                  | This file                                                      |
| `README.md`                    | How to reproduce                                               |
| `docs/data-notes.md`           | Data audit trail: codes, decisions, bugs, findings             |
| `docs/prior-work-scan.txt`     | Papers that may overlap — read before claiming novelty         |
| `docs/guide-search-report.txt` | How the e-scooter code was located                             |
| `docs/escooter-inspection.txt` | Verification against the real data                             |
| `paper/outline.md`             | Section-by-section outline with word budget                    |
| `paper/manuscript.md`          | The draft                                                      |
| `paper/references.bib`         | 99 DOI-verified references                                     |
| `outputs/logs/`                | Run logs from each stage                                       |
| `outputs/figures/`             | Six 300 dpi figures                                            |
| `outputs/tables/`              | Eleven result tables                                           |
