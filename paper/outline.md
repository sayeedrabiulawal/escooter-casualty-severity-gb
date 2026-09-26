# Paper Outline

**Working title:** Spatiotemporal Patterns and Severity Determinants of Powered Personal Transporter (E-Scooter) Casualties in Great Britain, 2021–2025: A Comparative Analysis with Pedal Cyclists and Motorcyclists using STATS19 Data

**Target length:** 6,500–8,000 words (journal). ~4,500 words for a conference version.
**Primary target venue:** _Transportation Research Record_ (see `plan.md` §8)

---

## Abstract (250 words)

Structure it in five moves. Write this **last** — but write it twice: once in
Week 2 as a plan (to clarify your own thinking) and once at the end as a summary.

1. **Context** (1–2 sentences) — micromobility growth; e-scooters now a visible mode in GB.
2. **Gap** (1 sentence) — the September 2026 STATS19 revision newly separates powered personal transporters from the "other" category; no comparative GB severity study yet published on this categorisation.
3. **Method** (2 sentences) — study period; data source; statistical approach.
4. **Findings** (2–3 sentences) — **with numbers**. Never write "results show significant differences" without the direction and magnitude.
5. **Implication** (1 sentence) — what a regulator or transport authority should take from it.

---

## 1. Introduction (900 words)

Funnel structure. Do not start with "Since the dawn of time..."

- **Para 1 — Context.** Growth of micromobility; e-scooter rental trials; private ownership. Keep this to what a reader outside the UK needs.
- **Para 2 — The safety concern.** What is known about e-scooter injury patterns internationally. Cite broadly (Europe, US, Australia) so the paper is not seen as parochial.
- **Para 3 — The regulatory oddity.** Private e-scooter use on public roads in GB is illegal, while rental schemes are legal. This creates an unusual natural experiment and a genuine measurement problem. State it early; it shapes the whole paper.
- **Para 4 — The gap.** Be precise and checkable:
    - No published study uses the new PPT categorisation.
    - Existing GB studies group e-scooters with "other" or rely on hospital data.
    - Comparative severity against both pedal cycles and motorcycles, on the same dataset and period, is absent.
- **Para 5 — Objectives.** List RQ1–RQ4 explicitly as a numbered list. A reader should be able to check your results section against this list.

**Last sentence of the section** should state the contribution, plainly and without hype.

---

## 2. Literature review (1,500 words)

Thematic, **not** chronological. Four themes:

### 2.1 E-scooter injury epidemiology (≈450 words)

Studies from emergency-department series, hospital admissions, and trauma registries. Note the consistent finding that a large share of e-scooter injuries involve no other vehicle and that head injury features heavily. Flag the key weakness in this body of work: it is almost entirely clinical, with no denominator and no comparison group.

### 2.2 Comparative injury severity across modes (≈400 words)

Work comparing cyclists, motorcyclists, and pedestrians. This is where you establish that severity modelling with logistic regression and KASI outcome is standard practice — cite the method sources you rely on.

### 2.3 Police-reported collision data as a research source (≈350 words)

STATS19's strengths (population-level, linked, long-running) and its well-documented weaknesses (under-reporting, differential by mode and severity, the IBR transition). **Be candid here.** Showing you understand the limitations of your own data is the single strongest credibility signal in the paper.

### 2.4 Spatial and environmental determinants (≈300 words)

Speed limit, lighting, junction type, urban form. Establishes why your covariates belong in the model.

### Gap statement (1 paragraph, ≈150 words)

Not a repeat of the introduction but an _evidence-based_ version: "Across these four strands, the literature is characterised by X, Y, and Z. This study addresses these by …"

---

## 3. Data and methods (1,500 words)

### 3.1 Study design and period

Cross-sectional comparative analysis of police-reported casualties, [years]. Justify the start year by when the current PPT coding became available — cite the DfT revision note.

### 3.2 Data source

STATS19 open data. Cite the dataset properly, state the OGL licence, and include the SHA-256 hash of the exact snapshot used.

### 3.3 Case definition

Who counts as an e-scooter casualty. Give the exact code and its source in the data guide. State how you handled records where the mode is ambiguous or the casualty flag and vehicle flag disagreed. This paragraph will be scrutinised — write it carefully.

### 3.4 Outcome

KASI = killed or seriously injured vs. slight. State the severity codes and how unknown-severity records were handled.

### 3.5 Covariates

Table 1: every variable, its source field, its codes, its categories, and the proportion missing. Give the reference category for each.

### 3.6 Statistical analysis

- Descriptives; Wilson intervals for proportions.
- Chi-square for urban/rural; note that with large n it is nearly always significant, so report proportions too.
- Logistic regression specification for Models A and B; state the interaction tested in Model C.
- ORs with 95% CI; report model fit (pseudo-R², AIC); VIF check.
- Software and versions. Give the exact `pandas` / `statsmodels` versions.

### 3.7 Sensitivity analyses

List them before you report them, so they read as pre-specified rather than fished for.

### 3.8 Ethics and reproducibility

Secondary analysis of fully anonymised, aggregate, publicly available data — no ethics approval required. State this plainly. Then: hypotheses pre-specified, code and derived data deposited at Zenodo (DOI).

---

## 4. Results (2,000 words)

> **Note — this outline predates the finished Results.** The manuscript gained a
> subsection for cohort characteristics and now numbers Results as 4.1 Cohort
> characteristics, 4.2 RQ1, 4.3 RQ2, 4.4 RQ3, 4.5 RQ4 (with the sensitivity analyses
> inside 4.5). Figures are numbered by the order they are cited, and files are named to
> match: `fig1_age_sex`, `fig2_trends`, `fig3_kasi_proportion`, `fig4_urban_rural`,
> `fig5_odds_ratios`, `fig6_ibr_robustness`. All six are embedded in the PDF and cited
> in the text.

Answer the RQs **in order**. One subsection each. No interpretation here — save it for the discussion.

### 4.1 RQ1 — Trends

Figure 2 (counts), Figure 3 (KASI proportion with CI), Table 2.
Report counts, the direction of change, and whether the change is in counts, severity, or both. Note explicitly that a rising count with a stable proportion means growth in exposure, not deteriorating safety.

### 4.2 RQ2 — Spatial distribution

Figure 4 (urban/rural), Table 3 (police force areas).
Report proportions, not just significance.

### 4.3 RQ3 — Within e-scooter determinants

Table 4 (Model A odds ratios).
Walk through the significant predictors in order of effect size. State the reference categories again in the text.

### 4.4 RQ4 — Comparative severity

Table 5 (Model B), Table 6 (Model C), Figure 5 (forest plot).
Give the key odds ratio for e-scooter vs. the reference mode, with its CI, in a sentence.

### 4.5 Sensitivity analyses

Report whether conclusions held. If they did not, **say so clearly**. A paper that reports a failed robustness check honestly is more trustworthy than one that hides it.

---

## 5. Discussion (1,300 words)

### 5.1 Principal findings

One paragraph. Answer each RQ in a sentence.

### 5.2 Comparison with existing literature

Do the patterns agree with international findings? Where they disagree, offer a mechanism. This section demonstrates you can situate your work in a field.

### 5.3 Interpretation and policy implications

Be specific but appropriately hedged:

- Speed-limit and infrastructure implications.
- Helmet policy — note that helmet-use data is not in STATS19, so you cannot test it. Say so.
- Rental scheme regulation and geofencing.
- The private-use legality issue and its effect on both behaviour and measurement.

Do not overreach. "These findings are consistent with" is usually better than "these findings prove".

### 5.4 Limitations

Write these as a numbered list so a reviewer can see you have thought about each:

1. Police-reported collisions only; under-reporting is substantial and likely differential by mode and severity.
2. Injury-based reporting changed severity recording mid-series; partially corrected via the DfT adjustment, but not fully.
3. Private e-scooter use is illegal, so the e-scooter population mixes rental use, illegal private use, and misclassified pedal cycles in unknown proportions.
4. No exposure denominator exists for private e-scooters, so risk per trip or per km cannot be estimated. Counts and proportions are reported instead.
5. Coding changes across STATS19 releases may affect comparability.
6. Residual confounding from unmeasured factors (helmet use, rider experience, vehicle speed, deprivation).
7. Observational design — associations only, no causal claims.

### 5.5 Future research

Two or three concrete, specific suggestions. "More research is needed" is not a suggestion.

---

## 6. Conclusion (400 words)

No new material. Restate the contribution in two sentences, the main finding in one, and the policy implication in one. End on the most interesting open question.

---

## Declarations

- **Data availability** — STATS19 via the DfT landing page (URL), OGL v3.0. Derived dataset and code at Zenodo: DOI 10.5281/zenodo.XXXXXXX.
- **Code availability** — GitHub URL, version tag.
- **Funding** — "This research received no external funding." (If accurate, say so. If you are self-funded, say "self-funded".)
- **Conflicts of interest** — "The author declares no conflict of interest."
- **AI use declaration** — Check the target journal's policy. If you used AI tooling for code or language editing, disclose it in the terms the journal specifies. Many publishers now require this.

---

## Submission checklist

- [ ] Word count within the journal's limit
- [ ] Abstract self-contained, with numbers
- [x] Every table and figure cited in the text, in order — Figures 1–6 embedded and cited
- [ ] Reference list complete, DOIs where available
- [ ] Reference style matches the target journal exactly
- [ ] Author name, ORCID, and affiliation correct
- [ ] ORCID added to the title page and metadata
- [ ] Line numbers on (most journals require this for review)
- [ ] Figures 300 dpi, greyscale-safe, readable in print
- [ ] Limitations section honest and specific
- [ ] `plan.md` and code pushed, tag created, Zenodo DOI minted
- [ ] Preprint uploaded before journal submission
- [ ] Cover letter written, short and factual
