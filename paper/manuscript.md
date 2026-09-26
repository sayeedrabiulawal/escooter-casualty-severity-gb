# Manuscript

**Title:** Severity of Powered Personal Transporter (E-Scooter) Casualties in Great
Britain, 2021–2025: A Comparative Analysis with Pedal Cyclists and Motorcyclists Using
STATS19 Data

**Author:** Rabiul Awal Sayeed
**Affiliation:** Department of Civil Engineering, Hebei University of Science and Technology
**Status:** Draft — results complete, literature review to be finalised

> Structure and word budget: see [`outline.md`](outline.md).
> Evidence, bugs found, and remaining work: see [`../progress.md`](../progress.md).
> Publishing steps: see [`../plan.md`](../plan.md) §7.

---

## HOW TO FINISH THIS DRAFT

Everything below is written from the actual analysis output. **Two sections remain, and
they are yours to write** — deliberately, because they are the parts that require your
own reading and judgement:

1. **§2, the literature review.** Start from `docs/literature-review-worksheet.md`, which
   breaks it into paragraph-by-paragraph jobs with the candidate papers and their
   publisher abstracts inline. Budget 1,500 words. **Do not cite anything you have not
   read in full**, and do not accept another party's characterisation of a paper's
   findings — including mine.
2. **§5.2, the comparison with existing literature.** Same worksheet, Part 2. Budget
   400 words. Zhao et al. (2026) must be cited and your contribution distinguished from
   theirs.

Two further tasks, neither of them writing:

3. **Verify every number** against `outputs/tables/` and `outputs/logs/`. The pipeline is
   deterministic, so any figure in this manuscript can be traced to a file in that output.
4. **Confirm the declarations.** Funding, AI use, and author contributions are filled in
   with defaults. Check that each is true of your situation, especially the AI-use
   disclosure and the journal's policy on it.

A Zenodo record is permanent and cannot be deleted. Do not deposit this manuscript while
any `TODO` marker remains in the PDF — `src/render_manuscript.py` warns you if one does.

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

> **TODO — VERIFY BEFORE SUBMITTING.** This section was drafted from the publishers'
> deposited abstracts, which are quoted in full in `docs/literature-review-worksheet.md`.
> Every claim below is intended to be traceable to an abstract. **Open each cited paper
> and confirm it supports the sentence it is attached to**, then delete this note.
>
> Two known items could not be resolved from abstracts alone and need a decision:
>
> 1. **Zhao et al.** — the bibliography holds the SSRN preprint
>    (`@zhao2025england`, DOI 10.2139/ssrn.5937116). A journal version appears to exist
>    at DOI 10.1016/j.aap.2026.108517. Check which should be cited, and check whether the
>    prose description here (England-wide Bayesian spatial field model) still matches the
>    published version.
> 2. **Cicchino et al.** reported injury proportions for e-scooters versus bicycles from a
>    single emergency department. The comparison drawn here is between that study's
>    _clinical_ proportions and this study's _police-reported_ proportions. Confirm the
>    figures quoted (13.1%/37.7%, 24.5%/50.7%, 34.3%/22.6%) before submission.
>
> Claims deliberately **not** made: that this is the first national e-scooter severity
> analysis (Zhao et al. precludes it), and any statement about risk per trip or per
> kilometre, which these data cannot support.

### 2.1 E-scooter injury epidemiology

The evidence base on e-scooter injury is dominated by single-centre clinical series
drawn from emergency departments and trauma registries. These studies have been
valuable in characterising how e-scooter injuries present, but they share structural
limitations that constrain what they can say about population-level risk.

The most consistent finding is rapid growth following the introduction of shared
services. Shichman et al. report a six-fold increase in e-scooter presentations at a
level I trauma centre, from an average of 26.9 per month before shared services were
introduced to 152.6 per month afterwards, across 3,331 patients [@shichman2022emergency].
Beck et al. found 56 e-scooter presentations in a six-week period that had recorded none
the previous year, a volume comparable to the 62 bicycle presentations in the same
window [@beck2019emergency]. McConnell et al. similarly observed that hospital
admissions rose from 9% to 32% of e-scooter presentations after hire scooters were
introduced [@mcconnell2026retrospective]. This recurrence across settings and countries
establishes that a new injury mechanism appeared with micromobility, but a rise in
presentations is not evidence about severity per trip, because none of these studies has
a denominator.

The reported injury profile is dominated by falls rather than collisions with vehicles.
Shichman et al. record rider fall as the mechanism in 79.1% of cases, with 2,637
orthopaedic injuries of which 599 (22.7%) were fractures, and 8.9% of patients
hospitalised [@shichman2022emergency]. Beck et al. found fractures or dislocations in
32% of patients and head injury in 26%, while nonetheless concluding that the majority
of presentations were for minor injury [@beck2019emergency]. The contrast between those
two observations within a single study is instructive: most e-scooter injuries are
minor, and a meaningful minority are not.

Two sub-populations recur. Alcohol features prominently in adult cases: Andersson et al.
found a positive alcohol history in 28% of 369 patients in Stockholm, and those patients
were more likely to arrive at night and by ambulance [@andersson2023electric]. Children
feature prominently too, with Reykjavik data showing 45% of patients under 18
[@anon2021emergency] and US national data showing e-scooter injuries concentrated among
males aged 12 to 18 [@douglas2026pediatric]. Helmet use is markedly lower among adults
than children — 17% versus 79% in the Reykjavik sample [@anon2021emergency]. In the UK
specifically, McGalliard et al. document increasing paediatric presentations despite
rental scooters being unavailable to under-16s and private use being lawful only on
private land [@mcgalliard2022electric].

Three limitations run through this body of work. It is almost entirely single-centre and
often single-city; it selects on presentation, so cases that do not reach an emergency
department are invisible; and it rarely includes a comparison group drawn from the same
source. Cicchino et al. are an exception, comparing e-scooter with bicycle presentations
at one emergency department, and their findings complicate the assumption that
e-scooters are simply more dangerous — e-scooter incidents less often involved a moving
vehicle (13.1% versus 37.7%) and less often occurred on the road (24.5% versus 50.7%)
[@cicchino2021injuries]. More recently, Zhao et al. have moved the literature toward
national-scale severity modelling, presenting an England-wide injury-severity analysis of
e-scooter riders using a Bayesian spatial field model [@zhao2025england]. That work
addresses the geographical limitation of the clinical literature but remains focused on
a single mode.

### 2.2 Comparative injury severity across modes

Treating injury severity as an ordered or binary outcome and modelling its determinants
with regression is long-established in road safety research. Asare et al. use ordinal
logistic regression on three decades of national collision records and identify vehicle
type, road class, speeding, and urban or rural location as significant correlates of
severity [@asare2020crash]. Chen et al. compare logistic regression against classification
trees and random forests for the same purpose, finding that the statistical model remains
competitive and offers more interpretable coefficients [@chen2020modeling]. More recent
work has moved toward interpretable machine learning, although Budzyński et al., using
152,567 Polish cyclist records, report only modest ordinal discrimination (quadratic
weighted kappa of approximately 0.20) and flag a substantial false-positive trade-off for
fatal outcomes [@budzyski2026explainable]. That result is a useful caution: severity is
predicted from environmental and casualty covariates with limited accuracy, which argues
for parsimonious, interpretable models over complex ones.

Comparisons across road user modes are also well established. Motorcyclists are the most
frequently used benchmark for elevated severity risk, being estimated at 28 times more
likely to die than car occupants while representing under 3% of registered vehicles
[@geary2023infrastructure]. Freeman et al. review the evidence that motorcyclists share
with younger and older drivers an elevated risk of crash or serious injury
[@freeman2012vulnerable]. Jackson et al. show that severity within a single mode varies
substantially by casualty age, finding a threefold increase in the odds of hospitalisation
among motorcyclists aged 60 and over compared with younger riders (OR 3.05, 95% CI
2.58–3.59) [@jackson2013injury]. For cyclists specifically, Fuad et al. apply latent class
and random-parameter models to 11,433 bicyclist collisions and demonstrate that
conventional single-model approaches can mask context-dependent severity mechanisms
[@fuad2026unraveling].

This literature supports two design choices made here: severity modelled as a binary
outcome with an established regression approach, and comparison against more than one
mode, since the choice of benchmark materially affects the resulting contrast. It also
supplies a directly relevant benchmark, Cicchino et al.'s e-scooter versus bicycle
comparison, which is clinical rather than population-based [@cicchino2021injuries].

### 2.3 Police-reported collision data as a research source

National police-reported collision databases are widely used for population-scale road
safety research. STATS19, the Great Britain casualty database, is sufficiently established
that dedicated tooling exists to access and clean it [@lovelace2019stats]. Its principal
advantages are national coverage, linkage between collision, vehicle, and casualty
records, and a long unbroken series.

Its principal weakness is under-reporting, and the magnitude is not uniform. Dandona et al.
compared population and hospital records with police records in urban India and found that
only 2.3% of non-fatal injuries treated as outpatients and 17.2% of those treated as
inpatients had been reported to the police, against 77.8% of fatal injuries
[@dandona2008under]. The pattern is critical for interpreting the present study: reporting
probability rises steeply with severity. Severity proportions computed from police data are
therefore inflated relative to the true injury distribution, and the degree of inflation
depends on how severely injured the affected mode typically is.

Under-reporting is also plausibly differential by mode, which is the more serious problem
for a cross-mode comparison. Modes whose injuries are comparatively minor, or which are
less likely to involve a reported party, will be under-represented, which biases the
severity proportions of the modes being compared in opposite directions. Municipal
officials interviewed by Cipriani et al. identified obtaining accurate e-scooter safety
data as one of four principal safety challenges they face, alongside riders constituting a
new category of vulnerable road user [@cipriani2024make]. This study's own analysis of
severity-recording practice, described in §3.7 and §4.5, addresses one specific measurement
change but cannot correct for general under-reporting.

### 2.4 Spatial, environmental, and regulatory determinants

The road environment is an established determinant of injury severity, which is why
environmental covariates belong in a severity model. Speed limit is the most studied.
Keall et al., comparing 2,682 pedestrian injury outcomes against vehicle safety ratings
across speed limit areas, found that the reduced risk associated with safer vehicles
appeared only in areas limited to 40 km/h or below, concluding that both lower speed
limits and a safer vehicle fleet are required for meaningful risk reduction
[@keall2022association]. The interaction between speed environment and other protective
factors is thus conditional rather than additive.

Spatial structure matters independently of the road environment. Thompson et al. analysed
killed-or-seriously-injured collisions in Toronto using Moran's I and Getis-Ord statistics,
finding that such casualties were not randomly distributed and that global spatial
autocorrelation was present only in the downtown area, with land use, infrastructure
density, and demographics explaining variation in KSI rates [@thompson2024spatial]. This
supports the urban concentration observed in the present study and indicates that urban
form, not merely road class, is relevant to where severe casualties occur.

For e-scooters specifically, the regulatory and behavioural literature is comparatively
young. Siebert et al. exploited Denmark's mandatory helmet law to measure helmet use before
and after implementation using computer vision on video footage [@siebert2023computer].
Sievert et al. surveyed 329 riders and found protected cycle lanes rated as the safest
infrastructure by 62.4% of respondents, though preferred by fewer (49.7%), with a
relationship between riding frequency and helmet use [@sievert2023survey]. Speak et al.,
studying a UK shared-scheme trial with 222 participants, found e-scooters regarded as
useful, affordable, and flexible, and substituting for some urban car trips
[@speak2023scooter]. These studies establish that rider behaviour and infrastructure
preference are measurable, but they also make visible a gap in the present analysis:
STATS19 records no helmet-use field, so protective-equipment effects cannot be tested here,
and the helmet literature cannot be used to interpret these findings.

### 2.5 Gap statement

Across these four strands the evidence is characterised by a consistent imbalance. The
e-scooter literature is dominated by single-centre clinical series that select on
presentation, lack a comparison group from the same source, and cannot supply a
population denominator [@shichman2022emergency; @beck2019emergency; @mcconnell2026retrospective].
Where national-scale analysis exists, as in Zhao et al.'s England-wide severity model
[@zhao2025england], it remains focused on a single mode and does not provide a
like-for-like contrast against other two-wheel modes. The comparative severity literature,
meanwhile, is well developed for motorcyclists [@geary2023infrastructure; @jackson2013injury]
and cyclists [@fuad2026unraveling], but has largely not been extended to e-scooters in a
population dataset. Finally, although under-reporting in police data is well documented
and known to rise with severity [@dandona2008under], the specific effect of the concurrent
change to injury-based severity recording on e-scooter casualty comparisons does not appear
to have been quantified.

This study addresses that combination directly. It compares e-scooter casualties against
both pedal cyclists and motorcyclists within a single national dataset and a single
specification; it reports five-year trends in both counts and severity proportions; and it
tests explicitly whether the central severity contrast survives the mid-series change in
severity-recording practice. It does not claim to be the first national analysis of
e-scooter severity, and should be read alongside Zhao et al. rather than in place of it.
Consistent with the under-reporting evidence, it reports severity proportions among
casualties and makes no claim about risk per trip or per kilometre.

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
proportion (0.75%) was closer to cycling (0.57%) than to motorcycling (2.08%). Figure 1
shows the age and sex distributions underlying those differences.

![Figure 1. Age and sex distribution by mode, as a proportion within each sex. E-scooter casualties peak sharply at ages 16-24 (33.3% of male and 33.0% of female casualties) and fall away rapidly with age, whereas pedal cyclists peak at 25-34 and are spread across all adult ages. Around a quarter of e-scooter casualties were under 16 (22.3% of males, 25.2% of females), a higher share than for either pedal cycling (12.0%, 8.0%) or motorcycling (1.2%, 4.0%).](outputs/figures/fig1_age_sex.png)

### 4.2 RQ1 — counts stable, severity rising

| Year | E-scooter casualties | KASI proportion (95% CI) |
| ---- | -------------------- | ------------------------ |
| 2021 | 1,102                | 0.284 (0.258–0.311)      |
| 2022 | 1,154                | 0.296 (0.271–0.323)      |
| 2023 | 1,117                | 0.287 (0.262–0.315)      |
| 2024 | 1,096                | 0.316 (0.289–0.344)      |
| 2025 | 1,162                | **0.358 (0.331–0.386)**  |

Casualty counts were **flat** across the five years (Figure 2), varying by less than 6%
around their mean. This does not support a narrative of rapidly escalating e-scooter
casualties in this dataset. What changed was **severity**: the KASI proportion rose from
0.284 to 0.358 (Figure 3), an increase whose 2021 and 2025 confidence intervals do not
overlap. The e-scooter KASI proportion thus converged toward the motorcycle level while
pedal cycling remained essentially flat across the period.

![Figure 2. Reported casualties by mode and year. E-scooter counts are essentially flat across 2021-2025, on a much smaller base than the pedal cycle and motorcycle series, both of which vary considerably more in absolute terms.](outputs/figures/fig2_trends.png)

![Figure 3. KASI proportion by mode and year, with 95% Wilson score intervals. The e-scooter series rises from 0.284 in 2021 to 0.358 in 2025, and those two intervals do not overlap, whereas the pedal cycle series stays broadly level.](outputs/figures/fig3_kasi_proportion.png)

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
London and other major conurbations. Figure 4 shows the urban/rural split for all three
modes.

![Figure 4. Urban and rural distribution of casualties by mode. E-scooter casualties are the most urban of the three groups, and motorcyclists the least.](outputs/figures/fig4_urban_rural.png)

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
estimate. Figure 5 shows the full set of adjusted coefficients.

![Figure 5. Adjusted odds ratios for killed or seriously injured (Model B, 95% CI, log scale). Rows in bold are the focal mode comparison. Reference categories, which do not appear as rows: pedal cycle, age 0-15, female, 20 mph, darkness with lights lit, dual carriageway, rural, crossroads.](outputs/figures/fig5_odds_ratios.png)

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
change in severity-recording practice. Figure 6 shows the three specifications side by
side.

![Figure 6. E-scooter and motorcycle odds ratios for KASI against pedal cycling, across three specifications. Whichever correction is applied, the e-scooter estimate stays between 1.56 and 1.64, and its interval does not reach 1 in any specification.](outputs/figures/fig6_ibr_robustness.png)

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

The age and urban profile reported here agrees closely with the clinical literature.
A median age of 22 and a 94.0% urban concentration match the young, urban-dominant
populations described in emergency department series: Andersson et al. found 49% of
patients under 30 [@andersson2023electric], Reykjavik data found 45% under 18
[@anon2021emergency], and United States national data found injuries concentrated among
males aged 12 to 18 [@douglas2026pediatric]. The profile appears robust across settings
and data sources.

Two results sit less comfortably against published work, and both warrant a mechanism
rather than being passed over.

First, the flat casualty counts contrast with the growth reported clinically. Shichman
et al. record a sixfold increase in presentations and McConnell et al. a rise in
admissions after scheme introduction [@shichman2022emergency; @mcconnell2026retrospective].
The likely explanation is that those studies observe the period in which exposure was
expanding, whereas this five-year window begins after shared schemes were already
established in Great Britain. Presentations at a hospital reflect exposure growth and
per-trip risk jointly; with exposure already high at the start of the window, flat counts
are compatible with a large and stable injury burden rather than a small one. This dataset
cannot separate the two, because it contains no exposure denominator.

Second, Cicchino et al. found a larger share of injured e-scooter riders aged 50 and over
than injured cyclists (34.3% versus 22.6%), whereas this cohort is markedly younger than
its cyclist comparison (median 22 versus 35) [@cicchino2021injuries]. The disagreement is
plausibly one of case ascertainment and regulatory context rather than of underlying risk.
Their sample is a single United States emergency department, serving a jurisdiction with
no licensing restriction on shared scooters; in Great Britain rental scooters are
restricted to licence holders and private use on public roads is unlawful
[@mcgalliard2022electric], and this analysis draws on police-reported casualties rather
than emergency department attendances. The same study nevertheless agrees on mechanism:
e-scooter incidents involved moving vehicles less often and occurred on roads less often
than cycling incidents, and produced more distal lower extremity trauma
[@cicchino2021injuries]. That is a fall-dominant, low-speed impact profile, consistent
with the absence of any speed-limit effect in Model A and with the predominance of rider
falls reported elsewhere [@shichman2022emergency].

Against Zhao et al.'s England-wide Bayesian severity model [@zhao2025england], this study
adds three things rather than superseding it: a three-way comparison including
motorcyclists, which supplies the severity benchmark that motorcyclist-focused work
normally provides [@geary2023infrastructure]; a five-year series in both counts and
severity proportions; and an explicit test of whether the severity contrast survives the
concurrent change in severity-recording practice. It is intended as a complement to that
work, and is not the first national analysis of e-scooter severity.

One further comparison concerns what the model can support. Its discriminative performance
is limited (pseudo-R² 0.052), which is consistent with Budzyński et al.'s finding that
severity models built on comparable covariates achieve only modest ordinal discrimination
[@budzyski2026explainable]. The odds ratio should therefore be read as a group-level
association between mode and severity, not as a basis for predicting individual outcomes.
Consistently with the under-reporting literature [@dandona2008under], all severity
proportions reported here are among casualties recorded by the police, and are not
estimates of the severity distribution of all e-scooter injuries.

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

**Code availability.** Included in the archived deposit, tag `v1.0.0`. The full pipeline reruns from raw
data and reproduces the derived dataset byte-identically.

**Figure availability.** Figures 1-6 are embedded in this manuscript and are also
archived individually as 300 dpi PNG files under `outputs/figures/` in the deposit, so
they can be reused or reprinted without extracting them from the PDF.

**Funding.** This research received no external funding.

**Conflicts of interest.** The author declares no conflict of interest.

**Ethics.** Secondary analysis of anonymised, aggregate, publicly available data; no
ethical approval required.

**AI use.** Substantial AI-assisted tooling was used in this project. The analysis and
validation code, the figure and table generation, and a working draft of this manuscript
were developed with AI assistance. All reported quantities are outputs of the archived
pipeline and are reproducible from the raw data without any AI involvement, and the
complete pipeline, including its validation checks, is included in the deposit. The
author is responsible for the content of this manuscript and for any errors in it.

**Author contributions.** Sole author: conceptualisation, methodology, software, formal
analysis, data curation, visualisation, writing (original draft), and writing (review and
editing).

---

## References

Managed in `references.bib` (91 entries, each with a DOI verified against Crossref).
Regenerate or check for prior work with:

```
python src/build_bibliography.py
python src/build_bibliography.py --check-scoop
```

Render the bibliography with Pandoc or LaTeX. **Verify every citation before submission** —
including that each cited paper genuinely supports the claim it is attached to.
