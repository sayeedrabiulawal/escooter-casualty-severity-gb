# E-Scooter Casualty Severity in Great Britain

Reproducible analysis of powered personal transporter (e-scooter) casualties using
UK STATS19 road safety open data, compared with pedal cyclists and motorcyclists.

**Status:** In progress — see [`plan.md`](plan.md) for the full research plan.

## Research question

How do the frequency, severity, and spatial distribution of e-scooter casualties in
Great Britain compare with those of pedal cyclists and motorcyclists, and which
factors are associated with serious or fatal outcomes?

## Data

UK Department for Transport **STATS19 road safety open data**
(<https://www.gov.uk/government/statistical-data-sets/road-safety-open-data>),
released under the Open Government Licence v3.0.

Raw data is **not** stored in this repository. Run the download script to fetch it.

## Reproducing the analysis

```bash
# 1. Create and activate an environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download the raw data (~255 MB) and the DfT code guide
python src/download_data.py
python src/fetch_data_guide.py

# 4. VERIFY the e-scooter code against the real data before anything else
python src/inspect_escooter.py

# 5. Build the analysis dataset (validates joins, converts missing codes)
python src/prepare_data.py

# 6. Descriptives, spatial analysis, and severity models
python src/analysis.py

# 7. Figures
python src/figures.py

# 8. Render the manuscript to PDF and PROVE it respects the page margins
python src/render_manuscript.py
python src/check_layout.py
```

Step 4 is not optional. It confirms which code identifies an e-scooter **in the data
you actually downloaded**, rather than trusting the guide or a remembered value.

Step 8 is not optional either. `render_manuscript.py` resolves the `[@key]` citations
in `manuscript.md` against `references.bib` into author-year text and generates the
reference list from the works actually cited. `check_layout.py` then rasterises every
page and fails if any ink landed inside a margin — layout errors are otherwise
invisible, because the PDF still opens and simply has text cut off or stranded.

## Repository layout

```
.
├── plan.md                    Full research plan, timeline, publishing, applications
├── progress.md                Running log: what was done, what broke, what remains
├── README.md
├── requirements.txt
├── requirements-lock.txt      Pinned versions of the exact environment used
├── CITATION.cff               Citation metadata for GitHub/Zenodo
├── LICENSE                    MIT (code)
├── LICENSE-CC-BY-4.0.md       CC-BY-4.0 (manuscript, figures, documentation)
├── .zenodo.json               Zenodo deposit metadata
├── data/
│   ├── raw/                   Downloaded STATS19 CSVs (git-ignored)
│   └── processed/             Analysis-ready dataset (git-ignored, ~117 MB)
├── docs/
│   ├── data-notes.md          AUDIT TRAIL: codes, decisions, bugs found, findings
│   ├── prior-work-scan.txt    Papers that may overlap — READ BEFORE CLAIMING NOVELTY
│   ├── crossref-results.json  Raw Crossref metadata behind references.bib
│   ├── data-guide/            The DfT data guide XLSX
│   ├── guide-search-report.txt      Search results for the e-scooter code
│   └── escooter-inspection.txt      Verification against the real data
├── src/
│   ├── download_data.py       Fetch raw STATS19 files (+ --check to probe URLs)
│   ├── fetch_data_guide.py    Fetch and search the DfT code guide
│   ├── inspect_escooter.py    Verify the e-scooter codes against the real data
│   ├── prepare_data.py        Validate, decode, link, and export
│   ├── dataset.py             Shared mode definition and derived fields
│   ├── codes.py               Map integer codes to the guide's labels
│   ├── build_bibliography.py  Generate DOI-verified BibTeX from Crossref
│   ├── analysis.py            Table 1, RQ1-RQ4, sensitivity analyses
│   ├── figures.py             Publication figures
│   ├── render_manuscript.py   Markdown -> print-ready PDF, resolving citations
│   └── check_layout.py        Fail if rendered text falls inside a page margin
├── outputs/
│   ├── figures/               Six 300 dpi greyscale-safe figures
│   ├── tables/                Ten result tables as CSV
│   └── logs/                  Run logs from each stage
└── paper/
    ├── outline.md             Section-by-section outline with word budget
    ├── manuscript.md          The draft
    ├── manuscript.pdf         Rendered preprint (16 pages)
    └── references.bib         91 DOI-verified references, keys checked unique
```

## Key decisions (all detailed in `docs/data-notes.md`)

- E-scooter casualties are identified by `casualty_escooter_flag == 1`, which nests
  exactly inside `vehicle_type == 33` ("Personal powered transporter").
- Casualties are linked to their **own** vehicle on
  `collision_index` + `vehicle_reference`. Both keys are required: `collision_index`
  alone is not unique in the vehicle table.
- STATS19 codes missing values as integer sentinels, not blanks. `-1` and the
  guide's field-specific unknown codes are converted to `NaN` before modelling.
- STATS19 dates are parsed with an explicit `%d/%m/%Y` format. Format-less parsing
  silently dropped ~60% of rows from the trend tables.
- Model predictors are labelled from the DfT data guide rather than left as raw
  integer codes.
- Reference category for mode comparisons is **pedal cycle**.

## Headline result

After adjustment for age, sex, speed limit, light conditions, road type, urban/rural
and junction detail, e-scooter casualties have **1.59 times the odds of being killed
or seriously injured compared with pedal cyclists (95% CI 1.49-1.69)**, versus 1.36
(1.33-1.39) for motorcyclists. N = 148,320.

The estimate is **robust to the concurrent change in severity reporting**, which is the
most plausible competing explanation:

| Specification                      | E-scooter OR (95% CI) |
| ---------------------------------- | --------------------- |
| Raw outcome                        | 1.587 (1.490 - 1.690) |
| DfT severity-adjusted outcome      | 1.562 (1.468 - 1.663) |
| Injury-based-reporting forces only | 1.635 (1.502 - 1.780) |

**Important:** no exposure denominator exists for this mode, so these are severity
proportions among casualties, **not** estimates of risk per trip or per kilometre.

## Prior work — read before claiming novelty

Zhao et al. (2026), _Accident Analysis & Prevention_ (DOI 10.1016/j.aap.2026.108517),
published an England-wide e-scooter injury-severity study using a Bayesian spatial field
model. This project overlaps it, and the novelty claim is narrowed accordingly: the
distinct contributions are the three-way mode comparison including motorcyclists, the
five-year trend analysis, and the injury-based-reporting robustness analysis. See
`docs/prior-work-scan.txt` and `progress.md` §6.

## Licence

- **Code:** MIT — see [`LICENSE`](LICENSE)
- **Manuscript, figures, documentation:** CC-BY-4.0 — see [`LICENSE-CC-BY-4.0.md`](LICENSE-CC-BY-4.0.md)
- **Source data:** Open Government Licence v3.0, (c) Crown copyright. Not relicensed here.

## Citation

See [`CITATION.cff`](CITATION.cff). A DOI will be minted on Zenodo at release.

**Author:** Rabiul Awal Sayeed — Department of Civil Engineering, Hebei University of
Science and Technology, Shijiazhuang, China.

## Status

Analysis complete and reproducible. The manuscript's methods and results are written;
the literature review and the prior-work positioning need completion by the author. See
[`progress.md`](progress.md) for the full state and remaining work.
