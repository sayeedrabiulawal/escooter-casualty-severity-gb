# Manuscript

**Title:** Severity of Powered Personal Transporter (E-Scooter) Casualties in Great
Britain, 2021–2025: A Comparative Analysis with Pedal Cyclists and Motorcyclists Using
STATS19 Data

**Author:** Sayed `[surname]`
**ORCID:** `[add before release]`
**Affiliation:** `[add before release]`
**Status:** Draft — results complete, literature review to be finalised

> Structure and word budget: see [`outline.md`](outline.md).
> Evidence, bugs found, and remaining work: see [`../progress.md`](../progress.md).
> Publishing steps: see [`../plan.md`](../plan.md) §7.

---

## HOW TO FINISH THIS DRAFT

Methods and results below are written from the actual analysis output and can be used
once proofread. Three things remain, and they are **yours to do** — I have deliberately
not done them for you:

1. **The literature review (§2).** 99 real references are in `references.bib`, each with
   a DOI verified against Crossref. But a citation is only legitimate if you have read
   the paper. **Do not cite anything you have not read**, and do not accept another
   party's characterisation of a paper's findings.
2. **The prior-work positioning in §1 and §5.2.** Zhao et al. (2026) overlaps this study
   substantially — see `progress.md` §6. It must be cited and positioned against, and the
   novelty claim narrowed accordingly.
3. **Verification of every number** against `outputs/tables/` and `outputs/logs/`.

---

## Abstract

**Background.** Powered personal transporters (PPTs), commonly e-scooters, have become a
visible road user group in Great Britain. Their safety profile is poorly characterised
at national scale, particularly in comparison with established two-wheel modes.

**Methods.** We analysed five years (2021–2025) of police-reported personal-injury
collisions from the STATS19 open dataset, using the casualty-level PPT identifier that
this release back-fills to 2021. Casualties were classified as e-scooter, pedal cycle,
or motorcycle. The outcome was killed or seriously injured (KASI). Logistic regression
models adjusted for casualty age, sex, speed limit, lighting, road type, urban/rural
classification, and junction detail. Three sensitivity analyses addressed the
mid-series change to injury-based reporting (IBR).

**Results.** There were 5,631 e-scooter, 80,465 pedal-cycle, and 82,953 motorcycle
casualties. E-scooter casualty counts were stable across the period (1,102 in 2021 to
1,162 in 2025), but the KASI proportion rose from 0.284 (95% CI 0.258–0.311) to 0.358
(0.331–0.386). E-scooter casualties were younger than cyclists (median age 22 vs 35) and
overwhelmingly urban (94.0%). After adjustment, e-scooter casualties had **1.59 times
the odds of KASI compared with pedal cyclists (95% CI 1.49–1.69)**, and motorcyclists
1.36 (1.33–1.39). The estimate was robust to IBR adjustment (OR 1.56, 95% CI
1.47–1.66) and to restriction to IBR-reporting forces (OR 1.64, 95% CI 1.50–1.78).

**Conclusions.** In this national dataset, e-scooter casualties were more likely to be
seriously injured than pedal cyclists, and the severity proportion increased over the
study period while casualty counts remained flat. The finding was not attributable to
the concurrent change in severity-recording practice. The absence of an exposure
denominator means these are severity proportions among casualties, not estimates of
risk per trip, and the results should not be read as such.

**Keywords:** e-scooter; powered personal transporter; micromobility; road safety;
injury severity; STATS19

---

## 1. Introduction

Micromobility has expanded rapidly across British cities, and the powered personal
transporter — the e-scooter — is its most conspicuous form. Great Britain presents an
unusual regulatory situation: rental e-scooter schemes operate under government trials,
while private e-scooter use on public roads remains illegal. The resulting population of
riders therefore mixes lawful rental users with unlawful private users, in proportions
that are not measured.

Two features of the evidence base motivate this study.

First, much of what is known about e-scooter injury comes from clinical settings —
emergency department series and trauma registries. These describe injury patterns well
but cannot place them in a population denominator, and rarely include a comparison group
drawn from the same source. Studies comparing e-scooter injuries with bicycle injuries do
exist, but are predominantly clinical and single-centre (`references.bib`: see themes
`escooter_epi`, `escooter_severity`).

Second, national collision datasets offer a population-scale alternative, but until
recently British data did not identify e-scooters separately. The September 2026 release
of the STATS19 open data carries a casualty-level e-scooter identifier that has been
**back-filled to 2021**, even though the accompanying data guide states the field was
introduced in 2023 (vehicle table) and 2025 (casualty table). This creates a five-year
window that was previously not analysable, and an older data snapshot cannot reproduce
it.

**Prior work.** Zhao et al. (2026) present an England-wide injury-severity analysis of
e-scooter riders using a Bayesian spatial field model. That work is severity-focused and
geographically focused on England. The present study is differentiated in four ways: it
compares e-scooter casualties against **both** pedal cyclists and motorcyclists within a
single specification; it examines five-year trends in both counts and severity; it
reports an explicit robustness analysis of the concurrent change to injury-based
severity reporting; and it covers Great Britain rather than England alone. Where the two
studies overlap, this paper should be read as complementary, and it does not claim to be
the first report of e-scooter severity in this setting.

**Objectives.**

- **RQ1** — How have e-scooter casualty counts and severity proportions changed from 2021
  to 2025, relative to pedal cyclists and motorcyclists?
- **RQ2** — How does the geographic distribution of e-scooter casualties (urban/rural, by
  police force area) differ from the comparison modes?
- **RQ3** — Which casualty, vehicle, and collision-level factors are associated with KASI
  among e-scooter casualties?
- **RQ4** — After adjustment, is e-scooter involvement associated with higher or lower
  odds of KASI than pedal cycling and motorcycling?

**Contribution.** A like-for-like comparison of severity across three two-wheel modes over
five years in a national collision dataset, with evidence that the result is not an
artefact of a mid-series change in how severity was recorded.

---

## 2. Literature Review

> **TODO — YOU MUST WRITE THIS SECTION.**
>
> Four themes, matching `outline.md` §2:
>
> - **2.1 E-scooter injury epidemiology** — themes `escooter_epi`, `escooter_severity`
> - **2.2 Comparative injury severity across modes** — themes `vru_severity`,
>   `cycling_severity`
> - **2.3 Police-reported collision data as a research source** — theme
>   `police_reported_bias`
> - **2.4 Spatial and environmental determinants** — themes `speed_limit`,
>   `spatial_analysis`
> - **Gap statement** — end with an evidence-based gap that RQ1–RQ4 answer directly.
>
> **Rules:** read each paper before citing it; cite the specific claim it supports; prefer
> the last 10 years except for methods and dataset provenance.
>
> Zhao et al. (2026) belongs in §2.1 and must be discussed explicitly.

---

## 3. Data and Methods

### 3.1 Study design and setting

Cross-sectional analysis of five years of police-reported personal-injury road collisions
in Great Britain (England, Scotland, Wales), 2021–2025. Northern Ireland is excluded
because it uses a separate collision reporting system not present in this dataset.

### 3.2 Data source

The STATS19 road safety open dataset, published by the UK Department for Transport under
the Open Government Licence v3.0 [@dft_stats19_2026]. Three linked tables were used:
collisions, vehicles, and casualties. The September 2026 release was downloaded on
26 September 2026; the exact snapshot is fixed by SHA-256 checksums recorded in the
project repository, and the analysis dataset reproduces byte-identically from it.

### 3.3 Case definition

The unit of analysis is the **casualty record** — one row per injured person. This
matters: mixing casualty-level and collision-level counts inflates or deflates
comparisons depending on occupancy, and is a common error.

Casualties were assigned to mode using verified code values from the DfT data guide,
confirmed against the downloaded release rather than assumed:

| Mode        | Definition                            |
| ----------- | ------------------------------------- |
| E-scooter   | `casualty_escooter_flag == 1`         |
| Pedal cycle | `vehicle_type == 1`                   |
| Motorcycle  | `vehicle_type ∈ {2, 3, 4, 5, 23, 97}` |

The casualty-level flag was used as the primary definition because the outcome is
casualty-level severity. It nests exactly inside the vehicle-level classification: all
5,631 flagged casualties were riding a `vehicle_type == 33` vehicle ("Personal powered
transporter"). The vehicle-level flag identifies 6,786 e-scooter _vehicles_, and
`vehicle_type == 33` identifies 6,901; the 115-record difference is quantified in a
sensitivity analysis (§3.7).

`vehicle_type == 22` ("Mobility scooter") is a different vehicle class and was
deliberately excluded.

Records were joined across tables on `collision_index` **and** `vehicle_reference`. Both
keys are required: `collision_index` is unique in the collision table but not in the
vehicle table, which averages approximately 1.8 vehicles per collision. Joining on
`collision_index` alone attaches an arbitrary vehicle to each casualty and corrupts every
vehicle-level variable. After the correct join, 100% of casualties matched their own
vehicle.

### 3.4 Outcome

The outcome was killed or seriously injured (KASI), contrasting severity codes 1 (fatal)
and 2 (serious) against 3 (slight). Severity is recorded for every casualty, so no
records were lost to an undefined outcome.

### 3.5 Covariates

Casualty age (analysed in bands: 0–15, 16–24, 25–34, 35–44, 45–54, 55–64, 65+), sex,
speed limit, light conditions, road type, urban/rural classification, and junction
detail. Category labels follow the DfT data guide so that coefficients are interpretable
without a code lookup. Reference categories are reported alongside the model output.

### 3.6 Statistical analysis

- **Table 1** describes the three mode cohorts.
- **RQ1** — casualty counts by mode and year; KASI proportions with 95% Wilson score
  intervals, which behave correctly for proportions unlike the normal approximation.
- **RQ2** — urban/rural proportions by mode; chi-square test reported alongside
  proportions, since with n of this magnitude the test is significant almost irrespective
  of effect size.
- **RQ3** — logistic regression of KASI within the e-scooter cohort.
- **RQ4** — logistic regression on the pooled three-mode cohort with mode as the focal
  predictor. **Pedal cycle is the reference category**, chosen because it is the most
  directly comparable mode to an e-scooter: similar speed, no protective shell, and
  similar road position.
- A mode × speed-limit interaction was fitted to test whether the effect of speed limit
  differs by mode.
- Odds ratios are reported with 95% confidence intervals. Model fit is summarised by
  pseudo-R² and AIC.

Analysis used Python 3.14 with pandas 3.0 and statsmodels 0.15. All code is archived and
the pipeline reruns from raw data.

### 3.7 Sensitivity analyses

Pre-specified and reported in full:

1. **Severity-adjustment.** Refit RQ4 using the DfT's own injury-based-reporting severity
   adjustment. Because the adjusted outcome is an expected probability in [0, 1] rather
   than a 0/1 flag, a fractional (quasi-likelihood) logit was used.
2. **Restriction to IBR-reporting forces.** Refit RQ4 using only casualties from forces
   using injury-based reporting, where the recording method is internally consistent.
3. **Unknown-severity exclusion.** Refit RQ3 excluding records with unknown severity.
4. **Alternative cohort definition.** Refit RQ3 using `vehicle_type == 33` instead of the
   casualty flag.

A methodological detail worth stating explicitly: the DfT column
`casualty_adjusted_severity_serious` is the probability of being **serious but not
fatal**. It is zero for slight casualties _and_ zero for fatalities; all 8,033 fatalities
in this dataset have a value of exactly zero, and the two adjusted columns sum to one
only for non-fatal casualties. Used directly as the outcome it would score every fatality
as a non-KASI case, understating the adjusted rate by 5.6%. The outcome used here adds
fatalities back:

$$\text{kasi}_{\text{adj}} = \mathbb{1}[\text{severity} = \text{fatal}] + p_{\text{serious}}$$

### 3.8 Ethics

Secondary analysis of fully anonymised, aggregate, publicly available data. No
individuals are identifiable and no ethical approval was required.

---

## 4. Results

### 4.1 Cohort characteristics (Table 1)

| Characteristic      | E-scooter  | Pedal cycle | Motorcycle |
| ------------------- | ---------- | ----------- | ---------- |
| Casualties, n       | 5,631      | 80,465      | 82,953     |
| Median age (IQR)    | 22 (16–33) | 35 (23–50)  | 31 (23–44) |
| Age not recorded, % | 4.3        | 3.2         | 0.9        |
| Male, %             | 77.0       | 78.4        | 88.1       |
| Urban, %            | 94.0       | 84.0        | 69.8       |
| KASI, %             | 30.9       | 25.3        | 33.8       |
| Fatal, %            | 0.75       | 0.57        | 2.08       |

E-scooter casualties were **substantially younger** than pedal cyclists (median 22 vs 35
years) and markedly more urban (94.0% vs 84.0% and 69.8%). Their KASI proportion (30.9%)
sat between pedal cycling (25.3%) and motorcycling (33.8%), while their fatality
proportion (0.75%) was closer to cycling (0.57%) than to motorcycling (2.08%).

### 4.2 RQ1 — counts stable, severity rising

| Year | E-scooter casualties | KASI proportion (95% CI) |
| ---- | -------------------- | ------------------------ |
| 2021 | 1,102                | 0.284 (0.258–0.311)      |
| 2022 | 1,154                | 0.296 (0.271–0.323)      |
| 2023 | 1,117                | 0.287 (0.262–0.315)      |
| 2024 | 1,096                | 0.316 (0.289–0.344)      |
| 2025 | 1,162                | **0.358 (0.331–0.386)**  |

Casualty counts were **flat** across the five years, varying by less than 6% around their
mean. This does not support a narrative of rapidly escalating e-scooter casualties in
this dataset. What changed was **severity**: the KASI proportion rose from 0.284 to
0.358, an increase whose 2021 and 2025 confidence intervals do not overlap. The e-scooter
KASI proportion thus converged toward the motorcycle level while pedal cycling remained
essentially flat across the period.

Because a rising severity proportion can be produced either by more severe collisions or
by changing reporting practice, §4.5 tests the second explanation directly.

### 4.3 RQ2 — predominantly urban

| Mode        | Urban % | Rural % |
| ----------- | ------- | ------- |
| E-scooter   | 94.0    | 6.0     |
| Pedal cycle | 84.0    | 16.0    |
| Motorcycle  | 69.8    | 30.2    |

The urban/rural mix differed by mode (χ² = 5,621, df = 2, p < 0.001). Given the sample
size this test is near-certain to be significant, so the proportions — not the p-value —
are the meaningful result. E-scooter casualties were the most urban of the three groups,
consistent with where rental schemes operate and where private use concentrates. Counts
by police force area were also tabulated; the largest shares fell in the forces covering
London and other major conurbations.

### 4.4 RQ3 — determinants of severity among e-scooter casualties

N = 5,056. Significant associations with KASI:

| Predictor  | Reference            | Odds ratio (95% CI)   |
| ---------- | -------------------- | --------------------- |
| Age 25–34  | 0–15                 | 1.24 (1.03–1.50)      |
| Age 35–44  | 0–15                 | 1.73 (1.40–2.15)      |
| Age 45–54  | 0–15                 | 1.96 (1.52–2.52)      |
| Age 55–64  | 0–15                 | 1.99 (1.41–2.82)      |
| Age 65+    | 0–15                 | **5.24 (2.31–11.93)** |
| Male       | Female               | 1.53 (1.31–1.78)      |
| Daylight   | Darkness, lights lit | 0.74 (0.65–0.85)      |
| Roundabout | Dual carriageway     | 0.47 (0.33–0.69)      |
| Urban      | Rural                | 0.63 (0.49–0.82)      |

**Age was the dominant correlate.** Odds of KASI rose monotonically across age bands,
reaching 5.24 for casualties aged 65 and over. This is a wide interval, reflecting few
casualties in that band, and should be interpreted cautiously but not dismissed.

Casualties in daylight had lower odds of KASI than in lit darkness, and those on
roundabouts or in urban areas had lower odds than on dual carriageways or in rural areas
respectively — consistent with lower impact speeds.

**Speed limit was not a statistically significant predictor within the e-scooter cohort.**
This is worth stating rather than omitting, because it contrasts with the pooled model,
where speed limit was strongly associated with severity. One reading is that e-scooter
casualties were already concentrated at low speed limits, leaving little variation to
detect an effect within the cohort.

### 4.5 RQ4 — comparative severity, and its robustness

Adjusted for age, sex, speed limit, lighting, road type, urban/rural, and junction detail
(N = 148,320; pseudo-R² = 0.052):

| Mode                    | Odds ratio for KASI (95% CI) |
| ----------------------- | ---------------------------- |
| Pedal cycle (reference) | 1.00                         |
| **E-scooter**           | **1.59 (1.49 – 1.69)**       |
| Motorcycle              | 1.36 (1.33 – 1.39)           |

E-scooter casualties had **1.59 times the odds of being killed or seriously injured**
compared with pedal cyclists after adjustment, and this was higher than the motorcycle
estimate.

The mode × speed-limit interaction was not statistically significant for e-scooters at
any speed limit (all p > 0.29), indicating the elevated odds were not concentrated in a
particular speed environment.

#### Injury-based reporting robustness

IBR adoption rose sharply and unevenly over the study period, from 38.1% of casualties in
2021 to 85.8% in 2025, and it differed by mode (27.9% of 2021 e-scooter casualties came
from IBR forces versus 40.1% of pedal-cycle casualties). This is the most plausible route
by which the headline result could be an artefact, so it was tested three ways:

| Specification                 | E-scooter OR (95% CI) | Motorcycle OR (95% CI) |
| ----------------------------- | --------------------- | ---------------------- |
| Raw outcome                   | 1.587 (1.490 – 1.690) | 1.360 (1.327 – 1.394)  |
| DfT severity-adjusted outcome | 1.562 (1.468 – 1.663) | 1.342 (1.309 – 1.376)  |
| IBR-reporting forces only     | 1.635 (1.502 – 1.780) | 1.463 (1.416 – 1.511)  |

**The estimate was stable between 1.56 and 1.64 across all three specifications.** The
elevated severity odds for e-scooter casualties therefore cannot be attributed to the
change in severity-recording practice.

The rising e-scooter KASI proportion also survived adjustment, though the gap between raw
and adjusted proportions narrowed from +0.017 in 2021 to +0.003 in 2025 as IBR coverage
approached saturation — itself consistent with IBR adoption explaining part, but not all,
of the apparent trend.

#### Other sensitivity analyses

Excluding records with unknown severity left RQ3 conclusions unchanged. Substituting
`vehicle_type == 33` for the casualty flag changed the e-scooter cohort by 115 records and
did not materially alter any estimate.

---

## 5. Discussion

### 5.1 Principal findings

Four results stand out. E-scooter casualty **counts were flat** across 2021–2025, varying
by under 6%, which does not support an escalating-casualty narrative in these data. The
**severity proportion rose** from 0.284 to 0.358, converging on motorcycle levels.
E-scooter casualties were **young and urban** (median age 22; 94.0% urban), distinctly
more so than cyclists. And after adjustment for the available confounders, e-scooter
casualties had **1.59 times the odds of KASI compared with pedal cyclists**, a result that
held under three separate robustness specifications, including correction for the
concurrent change in severity-recording practice.

### 5.2 Comparison with existing literature

> **TODO — write once §2 is written.**
>
> Key points, using sources you have actually read:
>
> - Compare the age and urban profile against the clinical literature, which reports a
>   young, male, urban-dominant e-scooter injury population. State whether this dataset
>   agrees.
> - Compare the severity finding against Zhao et al. (2026), which is England-wide and
>   severity-focused. State explicitly what the present analysis adds: the three-way mode
>   comparison, the five-year trend, and the reporting-method robustness.
> - Compare against comparative clinical studies of e-scooter versus bicycle injuries.
> - Where this study disagrees with published work, offer a mechanism rather than leaving
>   the disagreement unexplained.

### 5.3 Interpretation and implications

If these severity differences are causal rather than compositional, several policy
directions follow, each stated as a consideration rather than a recommendation.

- **Vehicle and rider characteristics.** E-scooters are ridden standing, with a high
  centre of gravity, small wheels, and no protective structure. These are plausible
  mechanisms for greater severity at comparable impact energy, though this dataset cannot
  isolate them.
- **Speed management.** Speed limit was not a significant within-cohort predictor, but
  urban roads dominate the cohort. Where e-scooter casualties concentrate is largely the
  low-speed urban network, so measures aimed at higher-speed roads would not reach most of
  them.
- **Age-targeted measures.** The age gradient within the cohort — raised odds of KASI at
  older ages — suggests older riders may warrant particular attention, though wide
  intervals at the oldest bands mean this is suggestive.
- **Regulation and legality.** Because private e-scooter use on public roads is unlawful
  in Great Britain while rental use is permitted, the cohort mixes lawful and unlawful use
  in unmeasured proportions. Any regulatory inference must acknowledge that.

### 5.4 Limitations

1. **No exposure denominator.** There is no reliable count of e-scooter trips or distance
   travelled, particularly for private vehicles. This study therefore reports severity
   **among casualties**, not risk per trip or per kilometre. A rising proportion does not
   establish that riding became more dangerous; it may reflect changes in who reports,
   how, or which modes are in use. **This is the study's principal limitation and the most
   likely basis for rejection.**
2. **Police-reported collisions only.** Non-injury and minor collisions are substantially
   under-reported, and under-reporting is likely differential by mode, which can bias a
   cross-mode comparison in either direction.
3. **Illegal private use and misclassification.** Because private e-scooter use is unlawful
   on public roads and enforcement is uneven, some e-scooter casualties may be recorded as
   pedal cycles or as "other vehicle", and the composition of the cohort is unknown.
4. **Reporting-method change.** IBR adoption rose from 38.1% to 85.8% and differed by mode.
   The DfT adjustment and the IBR-restricted analysis both support the headline finding,
   but the IBR-only analysis also changes which forces contribute, so it is not a clean
   replication of the same population.
5. **No helmet or rider-experience data.** STATS19 does not record helmet use, so
   protective-equipment effects cannot be tested.
6. **Residual confounding.** Rider experience, vehicle power and speed capability, and
   area-level deprivation are unmeasured.
7. **Observational design.** All estimates are associations. No causal claim is made.
8. **Category changes.** STATS19 specifications change between releases, and the
   back-filling of the e-scooter identifier means an older snapshot cannot reproduce these
   results.

### 5.5 Future research

Three specific directions: linking STATS19 to rental-scheme trip data to construct even a
crude exposure denominator; extending the analysis as the back-filled e-scooter identifier
accumulates further years; and quantifying how much of the observed severity difference is
attributable to vehicle characteristics versus rider and road environment, which would
require vehicle-level data this dataset does not contain.

---

## 6. Conclusion

In five years of national collision data, e-scooter casualties in Great Britain were
markedly younger and more urban than pedal cyclists, and had 1.59 times the adjusted odds
of being killed or seriously injured. The severity proportion rose over the period while
casualty counts stayed flat. The central finding was robust to correction for a concurrent
change in how severity is recorded, which was the most plausible competing explanation.
Because no exposure denominator exists for this mode, these are severity proportions among
casualties rather than estimates of risk, and that distinction should govern how the
results are used.

---

## Declarations

**Data availability.** The STATS19 road safety open dataset is published by the UK
Department for Transport under the Open Government Licence v3.0:
<https://www.gov.uk/government/statistical-data-sets/road-safety-open-data>. Raw data is
not redistributed here; `src/download_data.py` retrieves the exact snapshot, which is
fixed by SHA-256 checksums in `data/raw/checksums.sha256`. The derived analysis dataset and
all code are archived at Zenodo: DOI `[TODO]`.

**Code availability.** `[GitHub URL]`, tag `v1.0.0`. The full pipeline reruns from raw
data and reproduces the derived dataset byte-identically.

**Funding.** `[TODO — state "This research received no external funding" if accurate.]`

**Conflicts of interest.** The author declares no conflict of interest.

**Ethics.** Secondary analysis of anonymised, aggregate, publicly available data; no
ethical approval required.

**AI use.** `[TODO — check the target journal's policy. Many publishers require disclosure
of AI assistance with code or language editing. Disclose in the terms the journal
specifies.]`

**Author contributions.** `[TODO — single author: conceptualisation, methodology, software,
formal analysis, writing.]`

---

## References

Managed in `references.bib` (99 entries, each with a DOI verified against Crossref).
Regenerate or check for prior work with:

```
python src/build_bibliography.py
python src/build_bibliography.py --check-scoop
```

Render the bibliography with Pandoc or LaTeX. **Verify every citation before submission** —
including that each cited paper genuinely supports the claim it is attached to.
