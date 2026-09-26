# Progress Log

**Project:** Spatiotemporal Patterns and Severity Determinants of Powered Personal
Transporter (E-Scooter) Casualties in Great Britain, 2021–2025
**Author:** Rabiul Awal Sayeed
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
| Literature search     | Done — 91 DOI-verified references (7 duplicate keys removed)                          |
| §2 Literature review  | Done — 1,703 words, drafted from publisher abstracts; needs author verification       |
| §5.2 vs literature    | Done — 630 words, incl. explicit comparison with Zhao et al.                          |
| Citation rendering    | Done — PDF now resolves citations and prints a real reference list                    |
| Figures               | Done — all 6 embedded in the PDF and cited in the text; 1 figure relabelled           |
| PDF layout            | Done — checked mechanically, 19 pages, no text inside any margin                      |
| Author metadata       | Done — Rabiul Awal Sayeed, Hebei University of Science and Technology                 |
| ORCID / repository    | Not provided — fields removed cleanly; optional for deposit                           |
| Manuscript draft      | In progress — all sections drafted; 3 working-note markers remain                     |
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

**See [`docs/TONIGHT.md`](docs/TONIGHT.md) for the exact steps to deposit the software
record today.** The code is complete and ready, and the manuscript now has every section
drafted. What the preprint needs before deposit is author verification of the citations,
not more writing.

**§2 (1,703 words) and §5.2 (630 words) are now drafted.** Both were written from the
publisher abstracts collected in `docs/reading-list.md`; every claim is attached to a
citation, and the places where the abstracts were not enough to verify a claim are
listed in a visible note at the top of §2. **The author must read each cited paper and
confirm it supports the sentence it is attached to, then delete that note.**

Three working-note markers remain in the PDF, all intentional:

1. the §2 verification note (delete once the papers are checked);
2. the `## HOW TO FINISH THIS DRAFT` section (delete before submission);
3. the `[TODO]` placeholder for the Zenodo DOI, which cannot be filled until the
   deposit exists.

The declarations (funding, AI use, author contributions) are resolved. **Verify each is
true of your situation**, especially the AI-use disclosure.

### Figures were generated but never used

The pipeline produced six 300 dpi figures and the deposit archive shipped them as loose
PNG files, but **the manuscript cited none of them**: the PDF contained tables and not a
single figure, and `render_manuscript.py` had no code to place an image at all. The
outline had planned Figure 1/2/4/5 in Results, and its checklist item "Every table and
figure cited in the text, in order" was still unticked.

Fixed in four parts:

1. **The renderer can now embed figures.** Standard Markdown image syntax,
   `![caption](relative/path.png)`, draws the image at the text width, centred, with the
   caption beneath in smaller type. Aspect ratio is read from the file, height is capped
   so a figure cannot overflow a page, and a missing file is printed into the PDF rather
   than skipped, because a silently absent figure would ship.
2. **All six figures are placed and cited.** Figure 1 age/sex (§4.1), Figure 2 counts and
   Figure 3 KASI proportion (§4.2), Figure 4 urban/rural (§4.3), Figure 5 odds ratios and
   Figure 6 IBR robustness (§4.5). Each is referenced from the prose as well as captioned,
   so an automated checklist that looks for in-text citations will pass.
3. **Figure 5 was not publishable.** Its y-axis labels were raw statsmodels/patsy
   terms — `C(speed_limit_label)[T.60 mph]`, `C(age_band)[T.65+]` — which put internal
   model syntax in front of the reader. They are now `Speed limit: 60 mph`, `Age: 65+`,
   and the two focal mode rows are bold. Its caption also states the reference
   categories, which do not appear as rows.
4. **Three files were renamed** so figure numbers match the order they are cited in
   Results: `fig1_age_sex`, `fig2_trends`, `fig3_kasi_proportion`. Previously the age/sex
   figure — which belongs first, in §4.1 — was `fig3_*`, so file numbers and paper
   numbers would have disagreed.

A silent trap worth remembering: `preprocess()` rewrote Markdown links before the render
loop saw the text, and image syntax `![caption](path)` matches the link pattern. The
first render produced a 41 KB PDF with no figures in it and no error. The link pattern
now carries a `(?<!!)` lookbehind.

Two typographic defects were fixed in the same pass. `UNICODE_MAP` was downgrading
characters that latin-1 supports and the core font draws correctly, so the paper read
`pseudo-R^2` and `mode x speed-limit`; it now reads `pseudo-R²` and `mode × speed-limit`.
Both were confirmed by rendering the glyphs and inspecting the output before making the
change, rather than assuming the range was unsupported.

### PDF layout: text was spilling past the left and right margins

Reported by the author and confirmed by measurement. Nine of sixteen pages had ink
outside the 22 mm margin. Two separate causes:

- **`multi_cell` leaves the cursor at the right edge.** fpdf2's `multi_cell` defaults to
  `new_x=XPos.RIGHT`, so `pdf.x` ends up at the right edge of the cell just drawn. The
  bullet and numbered-list branches never reset it, so **every list item after the first
  was drawn starting at x = 188 mm** — off the page. On page 13 the continuations of
  list items appeared as a phantom column in the right margin with Markdown asterisks
  still in them. Fixed by routing every full-width block through `_block()`, which pins
  `x` to the left margin before and after drawing.
- **List continuations were rendered as separate paragraphs.** Prose in the manuscript is
  hard-wrapped, and list items carry a three-space continuation indent. The list branches
  took only the first line and ignored the rest, so each item was cut off mid-sentence and
  its continuation became an unindented paragraph of its own. Fixed by extracting
  `_gather()`, so bullet, numbered and paragraph blocks all join their continuation lines.
  This is what now produces the hanging indent.

Two smaller defects found in the same pass: numbered/bullet markers rendered as `?`
(U+2022 is not in latin-1; a hyphen marker is used instead), and fpdf2 tables draw their
rules marginally outside the width they are given, so a **centred** full-width table
overhung _both_ margins. Tables are now inset by 1.6 mm and left-aligned.

Also corrected: `set_auto_page_break(margin=18)` allowed body text to come within 18 mm of
the bottom edge — closer than the 22 mm margin it was supposed to respect. It now breaks
at the margin, and `_ensure_room()` keeps section rules and headings out of the bottom
margin.

**Guarded against recurrence.** `src/check_layout.py` rasterises every page and fails if
any ink falls inside a margin, so this cannot ship unnoticed again. Layout faults are
invisible in the usual checks: the PDF opens, the page count is right, and the text is
simply cut off or stranded in the margin.

### Author metadata added

Name and affiliation are now set in every file that needs them:

| Field       | Value                                                                       |
| ----------- | --------------------------------------------------------------------------- |
| Full name   | Rabiul Awal Sayeed                                                          |
| Given names | Rabiul Awal                                                                 |
| Family name | Sayeed                                                                      |
| Affiliation | Department of Civil Engineering, Hebei University of Science and Technology |
| ORCID       | not supplied — field removed                                                |
| Repository  | not supplied — link removed                                                 |

`src/personalise.py` had to be corrected first. It previously encoded the author as
"Sayed `[surname]`", which treated **Sayeed as a given name** — so it would have
produced "Sayeed, Sayeed" in the Zenodo metadata. Names are now carried as separate
given-names and family-name values, which is also what CITATION.cff requires. The
script was corrected rather than the files being edited by hand, so the single
source of truth still holds and the values cannot drift apart.

Written by `--given "Rabiul Awal" --family "Sayeed" --affiliation "Department of Civil
Engineering, Hebei University of Science and Technology"`. Re-run with a corrected
argument to change any value; the script is idempotent.

**Neither an ORCID iD nor a public repository URL was supplied.** Both fields were
removed rather than left as placeholders, because `0000-0000-0000-0000` in a permanent
record looks broken. Zenodo accepts a creator without either, so this is publishable as
it stands. An ORCID is still worth registering before the deposit: it is free, takes a
couple of minutes, and cannot be added to this DOI afterwards without publishing a new
version.

### Fixes made while drafting §2

- **Seven duplicate BibTeX keys** were found (`cipriani2024make`, `thompson2024spatial`,
  `lovelace2019stats`, `hama2019stats`, `bauernschuster2020speed`, `n.d.table`,
  `2015collision`). Duplicate keys mean one entry silently shadows another. Removed;
  the file now holds 91 unique entries, checked programmatically.
- **The dataset citation was broken.** `[@dft_stats19_2026]` was cited in §3.2 but was
  not in `references.bib` at all, so it rendered as a bare key. Added.
- **The Zhao reference key was wrong.** The bib holds `zhao2025england` (SSRN preprint,
  DOI 10.2139/ssrn.5937116), not `zhao2026england`. Corrected in both places it appears,
  and flagged in the §2 note because a 2026 journal version appears to exist at
  DOI 10.1016/j.aap.2026.108517 — confirm which to cite.
- **The PDF was not publishable.** `render_manuscript.py` had no citation handling, so
  all 46 `[@key]` markers printed literally, and no reference list was generated. The
  renderer now resolves citations to author-year form and builds a reference list from
  the works actually cited. Two further defects found in the same pass: bullets rendered
  as `?` (U+2022 is not latin-1) and `**bold**` printed literally inside table cells and
  blockquotes. All fixed and verified against the extracted PDF text.

### To finish the paper

- [ ] **Read every paper cited in §2 and §5.2** and confirm it supports its sentence,
      then delete the verification note at the top of §2. This is the one task that
      cannot be delegated — the analysis is yours and so is the responsibility for
      what it cites.
- [ ] Decide whether to cite the Zhao SSRN preprint or the 2026 journal version.
- [ ] Fill the remaining `[TODO]` for the Zenodo DOI after depositing.
- [x] ~~Embed and cite every figure, in order~~ — done; Figures 1–6 are in the PDF,
      each cited from the prose (see "Figures were generated but never used" above).
- [ ] Re-read the figure captions against the figures. The captions were written from
      computed values, not from looking at the images, so check that each one points at
      what a reader will actually see.
- [ ] Decide on Model C: the mode × speed interaction adds little, so consider
      swapping it for mode × urban/rural.
- [ ] Consider an exposure-denominator proxy (rental-scheme trip data). Even a crude
      one would materially strengthen the paper. If none can be sourced honestly, say
      so in the limitations instead of omitting the issue.
- [ ] Only 25 of the 91 references are cited so far, almost all of them added by §2.
      §3 and §4 cite almost nothing — a methods and modelling section normally cites
      its method sources. Consider citing `chen2020modeling`, `asare2020crash` and
      `khalili2013logistic` at the corresponding methods, and make sure every
      uncited entry is either used or removed before deposit.
- [ ] Proofread for claims unsupported by the numbers.

### To publish on Zenodo

- [x] `CITATION.cff` created
- [x] `LICENSE` created (MIT for code)
- [x] CC-BY-4.0 for the paper text and figures
- [x] `.zenodo.json` metadata prepared
- [x] Author, affiliation, and licences personalised via `src/personalise.py`
- [ ] Create ORCID (optional) and a public GitHub repository
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

| File                                  | Purpose                                                         |
| ------------------------------------- | --------------------------------------------------------------- |
| `plan.md`                             | Full research plan, timeline, publishing and application steps  |
| `progress.md`                         | This file                                                       |
| `README.md`                           | How to reproduce                                                |
| `docs/data-notes.md`                  | Data audit trail: codes, decisions, bugs, findings              |
| `docs/prior-work-scan.txt`            | Papers that may overlap — read before claiming novelty          |
| `docs/guide-search-report.txt`        | How the e-scooter code was located                              |
| `docs/escooter-inspection.txt`        | Verification against the real data                              |
| `paper/outline.md`                    | Section-by-section outline with word budget                     |
| `paper/manuscript.md`                 | The draft                                                       |
| `paper/manuscript.pdf`                | Rendered preprint, 16 pages                                     |
| `paper/references.bib`                | 91 DOI-verified references, keys checked unique                 |
| `src/render_manuscript.py`            | Markdown -> PDF, resolves citations, builds the reference list  |
| `src/check_layout.py`                 | Fails if rendered text falls inside a page margin               |
| `outputs/qa/`                         | Page rasters used to verify layout (git-ignored)                |
| `outputs/logs/`                       | Run logs from each stage                                        |
| `outputs/figures/`                    | Six 300 dpi figures, numbered in the order the paper cites them |
| `outputs/tables/`                     | Ten result tables                                               |
| `docs/reading-list.md`                | 100 candidates with verbatim abstracts, by manuscript section   |
| `docs/reading-list.csv`               | The same, as a tracking sheet with a blank `read` column        |
| `docs/literature-review-worksheet.md` | Paragraph-by-paragraph scaffold for §2 and §5.2                 |
