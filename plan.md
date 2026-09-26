# Research Plan — E-Scooter Casualties in Great Britain

**Author:** Sayed `[surname — fill in]`
**Started:** 2026-09-26
**Target completion:** 2026-11-21 (8 weeks)
**Deliverable:** One preprint with DOI on Zenodo + submission to one indexed journal

---

## 0. Decision summary

### Chosen topic

> **Spatiotemporal Patterns and Severity Determinants of Powered Personal Transporter (E-Scooter) Casualties in Great Britain, 2021–2025: A Comparative Analysis with Pedal Cyclists and Motorcyclists using STATS19 Data**

### Why this topic (and not another)

| Criterion                                     | How this topic scores                                                                                                                                                                                                                                          |
| --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fits constraints (laptop, free tools, no lab) | Fully open data + open-source Python. Zero fieldwork.                                                                                                                                                                                                          |
| Feasible in 8 weeks                           | Data download is a single script; analysis is standard regression.                                                                                                                                                                                             |
| Genuine novelty                               | The e-scooter flag in the Sept 2026 STATS19 release is **back-filled to 2021**, even though the data guide says it was introduced in 2023/2025. **BUT SEE THE WARNING BELOW** — Zhao et al. (2026) already published an England-wide e-scooter severity study. |
| Relevant to a transport MSc                   | Micromobility, road safety, and sustainable mobility policy are current priorities for transport programmes.                                                                                                                                                   |
| Risk of being scooped                         | **Realised, in part.** Zhao et al. (2026) published an England-wide e-scooter severity study in _Accident Analysis & Prevention_. The novelty claim has been narrowed — see §8.                                                                                |

### CRITICAL — prior work overlaps this study (found 2026-09-26)

> **Zhao, Konstantinoudis, Heydari (2026). "England-wide injury-severity analysis of
> e-scooter riders using a Bayesian spatial field model." _Accident Analysis &
> Prevention._ DOI 10.1016/j.aap.2026.108517** (preprint: 10.2139/ssrn.5937116)

Found via a systematic prior-work scan
(`python src/build_bibliography.py --check-scoop`; report in
`docs/prior-work-scan.txt`). This paper is England-wide, severity-focused, and in the
journal originally named as the primary target.

**What this study still adds beyond it:**

1. A **three-way comparison** — e-scooter vs pedal cycle vs **motorcycle** — on one
   dataset with a single specification. Zhao et al. are e-scooter-focused.
2. A **five-year trend analysis** of both counts and severity proportions.
3. An explicit **injury-based-reporting robustness analysis**, which Zhao et al. do not
   report and which is this study's strongest methodological contribution.
4. Coverage of **Great Britain**, not England alone.

**Consequences:** the novelty claim is narrowed to the above; Zhao et al. is cited and
positioned against in `paper/manuscript.md` §1 and §5.2; and the target journal has
changed (see §8). Finding this now is a much better outcome than claiming novelty a
reviewer could disprove in one search.

### Why the alternatives were rejected

- **Pavement survival analysis (LTPP)** — strong topic, but a longer learning curve (survival models + LTPP table schemas) and the Analysis Ready Datasets still require real data-wrangling. Kept as **Plan B**.
- **Systematic review** — lowest risk, but least distinctive. Reviews are extremely common among master's applicants. Kept as **Plan C**.

---

## 1. Research question and hypotheses

### Primary research question

How do the frequency, severity, and spatial distribution of e-scooter casualties in Great Britain compare with those of pedal cyclists and motorcyclists, and which factors are associated with serious or fatal outcomes?

### Sub-questions

- **RQ1** — How have e-scooter casualty counts and severity proportions changed year-on-year from 2021 to 2025?
- **RQ2** — How does the geographic distribution of e-scooter casualties across police force areas and urban/rural classifications differ from the comparison modes?
- **RQ3** — Which casualty, vehicle, and collision-level factors are associated with KSI (killed or seriously injured) outcomes for e-scooter casualties?
- **RQ4** — After controlling for confounders, is e-scooter use associated with higher or lower severity odds than pedal cycling and motorcycling?

### Hypotheses (state these before analysis, and report honestly if disconfirmed)

**Pre-specified, then tested against the data on 2026-09-26. Outcomes recorded below
rather than quietly rewritten — a hypothesis corrected after the fact is worthless,
and an admissions reader who spots a retro-fitted hypothesis discounts the whole
paper.**

- **H1** — E-scooter casualty counts increased substantially over 2021–2025 as ownership grew, but the _severity proportion_ (KASI share) is more stable than the raw count suggests.
    - **Status: DISCONFIRMED, in both halves.** Counts are flat (1,102 → 1,162, range 1,096–1,162). The severity proportion is the part that moves, rising from 0.284 to 0.358. So both halves are wrong, and in the same direction. **Report it that way** — it undercuts the "e-scooters are an exploding safety problem" framing that the flat counts fail to support, which is the more interesting finding.
- **H2** — E-scooter casualties are disproportionately concentrated in dense urban areas and on 30 mph roads, more so than motorcyclists but similarly to pedal cyclists.
    - **Status: SUPPORTED on urban/rural, UNSUPPORTED on speed limit.** 94.0% urban vs 84.0% (pedal cycle) and 69.8% (motorcycle). But speed limit is not a significant predictor within the e-scooter subset, so the "30 mph" half of the hypothesis fails.
- **H3** — After adjustment, e-scooter casualties have lower KASI odds than motorcyclists but comparable or higher odds than pedal cyclists.
    - **Status: DISCONFIRMED.** Adjusted OR is 1.59 (1.49–1.69) versus pedal cycling — higher, not comparable — and higher than motorcycling at 1.36 (1.33–1.39). Report this plainly.
- **H4** — Lighting condition, speed limit, and casualty age are the strongest predictors of severity within the e-scooter subset.
    - **Status: PARTLY SUPPORTED.** Age dominates (65+ OR 5.24 vs 0-15). Darkness and urban/rural matter. Speed limit does **not**, which is itself worth discussing.

### Scope boundaries (state these explicitly in the paper)

- **In scope:** Great Britain (England, Scotland, Wales). Police-reported personal injury collisions only.
- **Out of scope:** Northern Ireland (separate reporting system); non-injury collisions; hospital admissions data (not publicly linked); any causal claims.
- **Unit of analysis:** The casualty record (one row per injured person). Be explicit — mixing casualty-level and collision-level counts is a common and easily-caught error.

---

## 2. Data

### Primary source

**STATS19 — Road safety open data**, UK Department for Transport.

- Landing page: <https://www.gov.uk/government/statistical-data-sets/road-safety-open-data>
- Licence: **Open Government Licence v3.0** — free to use, redistribute, and publish, with attribution.
- Coverage: 1979–2025, three linked tables (collisions, vehicles, casualties).
- Format: coded CSVs. **All fields are integer codes.** You must decode them using the DfT data guide.

### Files to download

Use the **"last 5 years"** bundle (~250 MB total), _not_ the complete 1979–present set (the collision file alone is 1.5 GB and you do not need it):

| File                                                      | Approx. size |
| --------------------------------------------------------- | ------------ |
| `dft-road-casualty-statistics-collision-last-5-years.csv` | 98 MB        |
| `dft-road-casualty-statistics-vehicle-last-5-years.csv`   | 104 MB       |
| `dft-road-casualty-statistics-casualty-last-5-years.csv`  | 52 MB        |

### Essential references for correct interpretation

- **Open dataset data guide** (XLSX) — decodes every coded field. Download before writing any cleaning code.
- **Severity adjustment guidance** — explains that injury-based reporting (IBR) introduced by some police forces changed recorded severity, so raw year-on-year severity trends are partially artefactual.
- **Understanding historical road safety data** — documents specification changes over time.
- **Historical revisions log** — note that the November 2025 release had a `junction_detail` coding error, fixed from November 2025 onward.

### ~~CRITICAL first task — data availability check~~ DONE, 2026-09-26

All three questions resolved against the DfT data guide and the real September 2026
release. Full detail in `docs/data-notes.md`; re-verify with
`python src/inspect_escooter.py`.

1. **Which years carry the e-scooter code?** All five, 2021-2025, in **both** the
   vehicle and casualty tables. The guide claims the field was introduced in 2023 and
   2025, but the current release is **back-filled**. Two consequences: the full
   five-year period is usable, and **an older snapshot cannot reproduce this study**.
   That second point is both the novelty claim and a reproducibility limitation.
2. **How do the two mechanisms relate?** `vehicle_escooter_flag == 1` always implies
   `vehicle_type == 33`, never the reverse (6,786 vs 6,901). At casualty level the
   nesting is exact: 5,631 of 5,631. Use `casualty_escooter_flag` as primary.
3. **The exact code values** — `vehicle_type 33` = "Personal powered transporter",
   `1` = pedal cycle, `22` = mobility scooter (excluded).

**Note the terminology trap:** the guide never says "e-scooter" for `vehicle_type`.
It says "Personal powered transporter". Searching for "e-scooter" finds only the
flag fields, which is how the vehicle code gets missed.

### Verified cohort sizes

| Group                        | Casualties, 2021-2025 |
| ---------------------------- | --------------------- |
| E-scooter                    | 5,631                 |
| Pedal cycle                  | 80,465                |
| Motorcycle                   | 82,953                |
| Total modellable (all modes) | 148,320               |

A cohort of 5,631 is ample for the within-mode model (Model A). It is comfortably
enough for roughly 8-10 predictors, so RQ3 needs no trimming.

**Warning on per-year figures.** An earlier version of this pipeline parsed STATS19
dates without an explicit `DD/MM/YYYY` format, which silently coerce-dropped about
60% of rows from the trend tables (reporting 428 e-scooter casualties in 2021 rather
than 1,102). The regression models were unaffected, but **every per-year count and
proportion must come from the current run.** See bug 3 in `docs/data-notes.md`.

### Injury-based reporting: tested, and the finding holds

IBR adoption rose from 38.1% of casualties (2021) to 85.8% (2025), and it differs by
mode, so it was the most plausible threat to the headline result. Three separate
specifications now test it:

| Specification                                             | E-scooter OR for KASI (95% CI) |
| --------------------------------------------------------- | ------------------------------ |
| Model B, raw outcome                                      | 1.587 (1.490 - 1.690)          |
| Model B, DfT severity-adjusted outcome (fractional logit) | 1.562 (1.468 - 1.663)          |
| Model B, IBR forces only (N = 95,662)                     | 1.635 (1.502 - 1.780)          |

The estimate is stable between 1.56 and 1.64 across all three. **The finding is not
an artefact of the reporting-method change** - that is the strongest robustness claim
in the study and belongs in the abstract. Detail in `docs/data-notes.md`.

### Secondary/contextual sources (optional, only if time allows)

- Police force area boundaries (ONS Open Geography Portal) — for mapping.
- DfT vehicle licensing statistics — for exposure denominators. **Note:** e-scooter ownership has no reliable denominator, so avoid claiming rates per vehicle unless you can source one honestly. Report counts and proportions instead, and say why.

---

## 3. Methodology

### Step 1 — Data preparation

1. Read the DfT data guide, build a code→label mapping for every variable used.
2. Load all three CSVs with explicit `dtype` specifications (all coded fields as category or nullable Int).
3. **Validate the join key** — confirm `collision_index` is unique in the collision table before joining. If it is not unique, stop and investigate.
4. Left-join casualty → vehicle → collision on `collision_index`.
5. Flag the three analysis groups: e-scooter (PPT), pedal cycle, motorcycle.
6. Derive outcome `is_kasi` = 1 if severity is killed or serious, 0 if slight.
7. Handle missing and "unknown" codes explicitly. **Report the count and proportion of unknown values for every variable used** — do not silently drop them.
8. Export to `data/processed/analysis_dataset.csv` and record its SHA-256 hash.

### Step 2 — Descriptive analysis (addresses RQ1)

- Casualty counts by mode and year; plot as a line chart with the comparison modes indexed to their own 2021 baseline.
- KSI proportion by mode and year, with 95% confidence intervals (Wilson interval).
- Age and sex distribution by mode.
- Month-of-year and hour-of-day patterns for the e-scooter subset.

### Step 3 — Spatial analysis (addresses RQ2)

- Choropleth of e-scooter casualty counts by police force area.
- Urban vs. rural split by mode, with a chi-square test of independence.
- Optional: local Moran's I for spatial autocorrelation, if `geopandas` + police force boundaries come together cleanly. **Treat as optional** — cut it if it threatens the timeline.

### Step 4 — Severity modelling (addresses RQ3, RQ4)

**Model A — within-mode (RQ3).** Logistic regression on the e-scooter subset only.
Outcome: `is_kasi`. Predictors: age band, sex, speed limit, light conditions, road class, junction detail, urban/rural, month.

**Model B — comparative (RQ4).** Logistic regression on the pooled three-mode dataset with mode as a focal predictor, then a mode × covariate interaction model to test whether the effect of, e.g., speed limit differs by mode.

**Model C — robustness.** Mixed-effects logistic regression with a random intercept for police force area, to account for regional heterogeneity in reporting and enforcement. Use `statsmodels` for the fixed-effects models and note that a full mixed model may need `pymer4` or an R fallback via `statsmodels`' limited support — if it becomes a time sink, report it as a limitation instead.

**Reporting standard for all models:**

- Odds ratios with **95% confidence intervals** (never p-values alone).
- State the reference category for every categorical predictor.
- Report model fit (pseudo-R², AIC) and check for multicollinearity (VIF).
- Pre-specify a small number of interactions; do not fish for significance.

### Step 5 — Sensitivity analyses (this is what separates a strong paper from a weak one)

- Exclude records with unknown severity and re-run Model A.
- Restrict to years where the PPT coding is consistent across the whole period.
- Compare Model A with and without the IBR-affected police forces.
- Report how conclusions change — or state that they do not.

---

## 4. Tooling

Deliberately minimal. Everything below is free and open source.

| Purpose         | Tool                                              |
| --------------- | ------------------------------------------------- |
| Language        | Python 3.11+                                      |
| Data handling   | `pandas`, `numpy`                                 |
| Statistics      | `statsmodels`, `scipy`                            |
| Plots           | `matplotlib`, `seaborn`                           |
| Maps (optional) | `geopandas`                                       |
| Environment     | `venv`                                            |
| Version control | Git + GitHub                                      |
| Archiving / DOI | Zenodo                                            |
| Writing         | Markdown → PDF via Pandoc, or LaTeX if you prefer |

**Alternative:** R with the `stats19` package (CRAN) automates download and cleaning. Genuinely convenient, and `stats19::get_stats19()` handles the code decoding for you. If you are already comfortable in R, use it. Python is chosen here because it is the broader CV signal and the scripts below are already written.

---

## 5. Eight-week timeline

| Week  | Dates           | Deliverable                             | Definition of done                                                                                          |
| ----- | --------------- | --------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **1** | Sep 29 – Oct 5  | Data availability check + literature    | `docs/data-notes.md` written; **PPT code confirmed or study period revised**; 20 papers read and summarised |
| **2** | Oct 6 – Oct 12  | Literature review + design frozen       | 40 papers read; hypotheses and variables frozen in writing; data downloaded and loaded                      |
| **3** | Oct 13 – Oct 19 | Clean dataset built                     | `analysis_dataset.csv` exported, joined correctly, unknowns quantified                                      |
| **4** | Oct 20 – Oct 26 | Descriptives + spatial                  | Figures 1–4 final; Table 1 final; RQ1 and RQ2 answered                                                      |
| **5** | Oct 27 – Nov 2  | Models fitted                           | Models A, B, C run; results tables exported; sensitivity analyses done                                      |
| **6** | Nov 3 – Nov 9   | **Full first draft**                    | Complete draft including abstract — rough is fine, complete is mandatory                                    |
| **7** | Nov 10 – Nov 16 | Revision + repo cleanup                 | Draft revised; README reproducible from scratch; code commented                                             |
| **8** | Nov 17 – Nov 21 | **Zenodo release + journal submission** | DOI minted; preprint and code live; manuscript submitted                                                    |

**Rule:** every Friday, produce something. A half-finished draft on time beats a perfect draft in December.

### Hard deadlines inside the timeline

- **End of Week 1** — if the PPT coding is not present or not usable, switch to Plan B (LTPP) _immediately_. Do not drift.
- **End of Week 2** — research question frozen. No scope changes after this point.
- **End of Week 6** — complete draft exists, regardless of quality.
- **Week 8, Monday** — Zenodo release uploaded. This cannot slip; it is your CV deliverable.

---

## 6. Paper structure

Target: **6,000–8,000 words**, ~8,000 for a journal and ~4,500 if cut down for a conference paper.

| Section              | Words | Notes                                                                                                                                                                                         |
| -------------------- | ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Title + abstract     | 250   | Structure: context → gap → method → key findings with numbers → implication. No citations, no vague claims.                                                                                   |
| 1. Introduction      | 900   | Funnel: micromobility growth → safety concern → **the specific gap** (new PPT categorisation, no comparative GB study yet) → objectives                                                       |
| 2. Literature review | 1,500 | Thematic, not chronological. End with an explicit gap statement that your RQs answer directly.                                                                                                |
| 3. Data and methods  | 1,500 | Data source, study period, definitions, variable operationalisation, model specification, ethics (aggregate public data, no ethics approval required — state this), reproducibility statement |
| 4. Results           | 2,000 | RQ1 → RQ2 → RQ3 → RQ4, in order. Every table and figure referenced in the text.                                                                                                               |
| 5. Discussion        | 1,300 | Answer each RQ; compare to published literature; policy implications (helmet law, speed limits, rental scheme regulation); limitations.                                                       |
| 6. Conclusion        | 400   | No new material. Concrete next research step.                                                                                                                                                 |
| References           | —     | 40–60, majority from the last 10 years                                                                                                                                                        |
| Declarations         | —     | Data availability (Zenodo DOI), code availability (GitHub), conflicts of interest, funding                                                                                                    |

### Limitations to state explicitly

1. Police-reported collisions only — under-reporting is substantial for cyclists and e-scooter riders, and likely differential.
2. Severity recording changed with the shift to injury-based reporting; partially corrected, not fully.
3. Private e-scooter use is illegal on public roads in Great Britain. Casualties therefore reflect illegal use, rental-scheme use, and misclassification as pedal cycles, in unknown proportions. **This is a major caveat — address it head-on rather than burying it.**
4. No exposure denominator, so no true risk-per-trip estimates are possible.
5. Coding changes across releases may affect comparability.

---

## 7. Publishing to Zenodo

### Two ways to do it — pick Git-integration

**Option A (recommended): GitHub → Zenodo automatic archiving**

1. Create an **ORCID** iD if you do not have one: <https://orcid.org>. Free, takes 2 minutes. Link it to Zenodo.
2. Create a public GitHub repository with your code, `plan.md`, `README.md`, and the paper source.
3. Add a `LICENSE` file to the repo. **MIT for code, CC-BY-4.0 for the paper text.**
4. Add a `CITATION.cff` file in the repo root so GitHub and Zenodo can auto-format your citation.
5. Sign in to Zenodo with GitHub, go to **Settings → GitHub**, find your repo, and flip the switch to **ON**.
6. On GitHub, create a **release** with a tag like `v1.0.0`.
7. Zenodo automatically archives that release and mints a DOI within a minute or two. It appears under **Upload → My uploads**.

**Option B: manual upload**

1. Zenodo → **New upload**.
2. Upload: the manuscript PDF, `plan.md`, and a code archive (`.zip` of the repo).
3. Resource type: **Publication → Preprint** for the paper; upload the code as a **separate record** with resource type **Software**.
4. Fill in metadata (below).
5. Publish.

### Metadata to prepare in advance

| Field               | Value                                                                                         |
| ------------------- | --------------------------------------------------------------------------------------------- |
| Title               | The paper title exactly                                                                       |
| Authors             | Your full name as you want it cited, with ORCID                                               |
| Description         | The abstract                                                                                  |
| Keywords            | e-scooter; micromobility; road safety; STATS19; injury severity; powered personal transporter |
| Licence             | CC-BY-4.0 (paper), MIT (code)                                                                 |
| Language            | English                                                                                       |
| Access              | Open Access                                                                                   |
| Related identifiers | The GitHub repo URL                                                                           |

### Zenodo gotchas — read before you click publish

- **Publishing is effectively irreversible.** You cannot delete a published record; you can only publish a _new version_, which mints a _new_ DOI. Proofread the title, author name, and abstract before publishing.
- **Do not upload the raw STATS19 CSVs to Zenodo.** They are 250 MB, they are already archived by DfT, and re-uploading them adds nothing. Instead, include the download script plus a checksum of the source files. This is the correct professional practice.
- **The DOI is permanent and citable.** Cite it in your CV, SOP, and any email to a professor.
- Use the **version DOI** for internal reference and the **concept DOI** when you want to point at "the project" across versions. Know which is which before you share it.

---

## 8. Journal submission

### Updated after the prior-work scan (2026-09-26)

Zhao et al. (2026) is an England-wide e-scooter injury-severity study published in
**Accident Analysis & Prevention**, DOI 10.1016/j.aap.2026.108517. That journal has
therefore just published the closest existing work to this study. Submitting an
overlapping paper to it invites a rejection on novelty grounds, so it has been moved
down the list. The first-choice target is now a journal that publishes comparative
mode-severity work.

### Realistic targets (revised)

| Venue                                                          | Type       | Fit                | Notes                                                                         |
| -------------------------------------------------------------- | ---------- | ------------------ | ----------------------------------------------------------------------------- |
| _Journal of Safety Research_                                   | Journal    | **Primary**        | Elsevier; welcomes applied safety analysis; comparative mode work is in scope |
| _Traffic Injury Prevention_                                    | Journal    | Strong             | Taylor & Francis; explicitly publishes injury-severity comparison work        |
| _IATSS Research_                                               | Journal    | Strong             | Open access, no fee; practical transport safety                               |
| _International Journal of Injury Control and Safety Promotion_ | Journal    | Good               | Taylor & Francis; safety-specific                                             |
| _Transportation Research Record_ (TRR)                         | Journal    | Good               | SAGE; accepts solid empirical papers; review ~2-4 months                      |
| _Case Studies on Transport Policy_                             | Journal    | Moderate           | Elsevier; policy angle                                                        |
| _Accident Analysis & Prevention_                               | Journal    | **Lower priority** | Just published Zhao et al. (2026); novelty risk                               |
| TRB Annual Meeting                                             | Conference | Strong             | Indexed proceedings; abstract deadline ~1 August, so not this cycle           |
| _Sustainability_ / MDPI titles                                 | Journal    | **Avoid**          | See warning below                                                             |

### Required framing change

Wherever novelty is claimed, it must be limited to what this study adds **beyond**
Zhao et al.: the three-way mode comparison including motorcyclists, the five-year trend
analysis, and the injury-based-reporting robustness analysis. Claiming a first national
e-scooter severity analysis is no longer defensible and would be caught in review.

### Avoid

Any journal that (a) guarantees acceptance in under two weeks, (b) emails you an invitation to submit unsolicited, or (c) charges a high APC without indexing in Scopus or Web of Science. **A predatory publication is worse for your application than no publication at all** — an admissions tutor who spots one will discount your entire CV.

Verify indexing yourself at <https://www.scopus.com/sources> or the Web of Science Master Journal List before submitting anywhere.

### Submission sequence

1. Pick two target journals. Read their author guidelines and one recent paper each.
2. Format to the primary target. Do not try to satisfy two journals at once.
3. Submit with a short, factual cover letter. Do not oversell. Mention explicitly how
   the paper relates to Zhao et al. — reviewers will find it anyway, and addressing it
   first reads as confidence rather than concealment.
4. If rejected, the reviewer comments are free expert feedback. Revise and submit to the second target. This is normal and not a failure.

---

## 9. Using this in your master's application

### CV entry

```
PUBLICATIONS AND RESEARCH

[N. Surname] (2026). Spatiotemporal Patterns and Severity Determinants of Powered
Personal Transporter (E-Scooter) Casualties in Great Britain, 2021–2025.
Preprint. Zenodo. DOI: 10.5281/zenodo.XXXXXXX
  - Under review at [Journal Name]
  - Code and analysis repository: github.com/[username]/[repo]

[N. Surname] et al. (2026). [Repo title] (v1.0.0) [Computer software].
Zenodo. DOI: 10.5281/zenodo.YYYYYYY
```

The phrase **"under review at [Journal]"** is honest, verifiable by the journal, and materially stronger than a Zenodo-only upload.

### Statement of purpose

Do not just list the paper. Use it to demonstrate a specific, transferable capability. Something like:

> "I independently designed and completed an empirical study of e-scooter casualty
> severity using five years of STATS19 police-reported collision data, applying
> logistic regression and geospatial analysis in Python. The work required me to
> reconcile a mid-series coding change in the data specification and to reason
> carefully about exposure denominators, which are unavailable for private
> e-scooters. I pre-registered my hypotheses, published the analysis code openly,
> and documented the sensitivity analyses. I am drawn to [University]'s work on
> [specific research group/paper] because..."

That paragraph shows data handling, statistical judgement, methodological honesty, and reproducibility practice — all four are what a supervisor wants in a master's student.

### Concrete next steps for the application

- Get an **ORCID** now and use it consistently everywhere.
- Build a **GitHub profile** with this repo pinned and a real README.
- Identify **2–3 specific research groups** whose work connects to micromobility or road safety, and name them in your SOP. Generic SOPs do not work.

---

## 10. Risk register

| Risk                                             | Likelihood | Impact | Mitigation                                                                                      |
| ------------------------------------------------ | ---------- | ------ | ----------------------------------------------------------------------------------------------- |
| PPT code is only in the latest year              | Medium     | High   | Check in Week 1; if unusable, switch to Plan B (LTPP) immediately                               |
| The novelty window closes                        | Medium     | High   | Monitor arXiv/engrXiv and Google Scholar alerts weekly; aim to release preprint in Week 8       |
| Data columns differ from expectation             | Medium     | Medium | Validate schema programmatically before any analysis; write to `docs/data-notes.md`             |
| Scope creep into a full mixed model              | High       | Medium | Model C is optional. Fixed-effects models are sufficient. Cut without guilt.                    |
| Losing 2+ weeks to illness or exams              | Medium     | Medium | Week 6 draft rule protects the Zenodo deliverable; the journal submission can slip if it must   |
| Perfectionism delays the release                 | High       | High   | Preprint first, polish later. A released preprint with a DOI beats a perfect unpublished draft. |
| Journal review outlasts the application deadline | High       | Low    | The Zenodo preprint is the CV deliverable. "Under review" is a valid, honest line.              |

**Fallback ladder:** If by end of Week 1 the STATS19 PPT coding proves unusable → switch to the LTPP pavement survival analysis. If by Week 4 the modelling is not working → narrow to RQ1 + RQ2 only (a solid descriptive and spatial paper is publishable). If by Week 6 there is no draft → convert to a systematic review using the literature already gathered.

---

## 11. Status and next actions

**Overall state:** the analysis is complete, reproducible, and committed as `v1.0.0`
(commit `5c3c647`). The manuscript's methods and results are written from the real
numbers. What remains is the literature review, four metadata placeholders, and steps
that require your own accounts. See `progress.md` for the full log and
`docs/zenodo-release-checklist.md` for the release steps.

### Completed 2026-09-26

1. ~~Download the DfT data guide~~ — done; `docs/data-guide/`, search report in `docs/guide-search-report.txt`.
2. ~~Fetch the three CSVs~~ — done; 255 MB in `data/raw/`, checksums written.
3. ~~Confirm the e-scooter code~~ — done; `casualty_escooter_flag`, nesting exactly inside `vehicle_type 33`.
4. ~~Build the analysis dataset~~ — done; 652,821 rows, SHA-256 recorded, reproduces byte-identically.
5. ~~Run descriptives and models~~ — done; Table 1 plus 9 further tables in `outputs/tables/`.
6. ~~Generate figures~~ — done; six 300 dpi figures in `outputs/figures/`.
7. ~~Add the IBR sensitivity analysis~~ — done; three specifications, and the headline
   finding survives all three. This is the strongest robustness claim in the paper.
8. ~~Fix the date-parsing bug~~ — done; this had silently dropped ~60% of rows from
   the trend tables. Per-year figures are now corrected throughout.
9. ~~Literature search~~ — done; 99 DOI-verified references in `paper/references.bib`,
   generated from Crossref with an off-topic filter.
10. ~~Prior-work scan~~ — done; found Zhao et al. (2026). Novelty narrowed, journal
    target changed. See `docs/prior-work-scan.txt`.
11. ~~Write methods and results~~ — done; `paper/manuscript.md` §§3–4 and §6.
12. ~~Zenodo packaging~~ — done; `.zenodo.json`, licences split, `CITATION.cff`,
    dependency lock, release checklist.
13. ~~Git repository and tag~~ — done; `v1.0.0`, 255 MB of data correctly excluded.

### Remaining, in priority order

1. **Write the literature review (§2) and §5.2.** Read the papers; prune the 99
   references to the ~40 you actually use. **Do not cite unread papers.** This is the
   only substantial writing left, and it is the part that most needs your judgement.
2. **Fill the four metadata placeholders**: your surname, ORCID, affiliation, GitHub
   URL. Listed in `docs/zenodo-release-checklist.md` Step 1.
3. **Create an ORCID iD and a public GitHub repository**, then link the repo to Zenodo
   so the `v1.0.0` tag is archived and minted a DOI.
4. **Consider an exposure-denominator proxy.** This remains the study's weakest point
   and the most likely reason a reviewer rejects it. Even a crude denominator would
   materially strengthen the paper. If none can be sourced honestly, the limitations
   section already states the problem plainly — do not paper over it.
5. **Decide on Model C.** Speed limit is not significant within the e-scooter subset, so
   the mode × speed interaction adds little. Consider swapping it for mode × urban/rural,
   which the RQ2 and Model A results suggest is more informative.
6. **Proofread for claims unsupported by the numbers.** Every figure in the manuscript
   traces to `outputs/tables/`; verify before submitting.
7. **Draft the CV entry and SOP paragraph** from §9. Do this in parallel, not after.

### Two cautions before writing

- **Do not over-claim severity.** These are police-reported casualties with no
  exposure denominator. A higher KASI _proportion_ could mean greater injury
  severity, or differential reporting of slight injuries, or both. The paper cannot
  distinguish these, and must say so. Note the IBR analysis rules out one specific
  reporting artefact (the mid-series recording change) but not the general
  under-reporting problem.
- **Do not retro-fit hypotheses.** H1 and H3 are disconfirmed as written. Report them
  as pre-specified and disconfirmed, and explain what the data show instead. That is
  a stronger paper than one whose hypotheses happen to match its results.

---

_Related files: `paper/outline.md`, `docs/data-notes.md`, `README.md`_
