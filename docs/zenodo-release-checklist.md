# Zenodo Release Checklist

Everything on the technical side is already done. What remains requires **your
identity and accounts** — I cannot create an ORCID iD or authenticate to Zenodo on
your behalf, and you should not route credentials through an assistant.

Repository state: committed and tagged **`v1.0.0`** (commit `5c3c647`).

---

## Before you start: the irreversibility warning

**A published Zenodo record cannot be deleted.** You can only publish a _new version_,
which mints a _new_ DOI; the original remains permanently. Proofread the title, your
name (as you want it cited, forever), and the abstract before clicking publish.

---

## Step 1 — Personalise the metadata `[YOUR ACTION]`

Four placeholders must be filled. All are marked `[TODO]` or `[bracketed]`.

### 1a. `CITATION.cff`

```yaml
authors:
    - family-names: "[Surname]" # your actual surname
      given-names: "Sayed"
      orcid: "https://orcid.org/0000-0000-0000-0000" # uncomment and fill
      affiliation: "[Your University]" # uncomment and fill
repository-code: "https://github.com/[username]/[repo]"
```

### 1b. `.zenodo.json`

- `creators[0].name` → `"[Surname], Sayed"`
- `creators[0].orcid` → your real ORCID
- `creators[0].affiliation` → your institution
- `related_identifiers[0].identifier` → your GitHub URL

### 1c. `LICENSE`

Replace `Copyright (c) 2026 Sayed [surname]` with your full name.

### 1d. `paper/manuscript.md`

- Author block and ORCID
- The two `[TODO]` declarations: **funding** and **AI use**
- **The literature review (§2)** — see the warning below
- **§5.2 comparison with literature**
- The Zenodo DOI once minted

---

## Step 2 — Get an ORCID iD `[YOUR ACTION]`

<https://orcid.org> — free, takes about two minutes. Use the same form of your name
everywhere: ORCID, Zenodo, GitHub, CV, and manuscripts. Inconsistent name forms make
your publication record hard to find, which defeats the purpose.

---

## Step 3 — Create a public GitHub repository `[YOUR ACTION]`

```bash
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
git push origin v1.0.0
```

Make it **public**. A private repository mints a DOI that nobody can verify, which
defeats the CV purpose.

---

## Step 4 — Link GitHub to Zenodo `[YOUR ACTION]`

1. Sign in at <https://zenodo.org> using **GitHub** (not a separate account — the
   linking depends on it).
2. Go to **Settings → GitHub**.
3. Find the repository and flip the toggle to **ON**.
4. Zenodo only archives repositories _after_ the toggle is enabled, and only for
   tags pushed afterwards.

## Step 5 — Create the release `[YOUR ACTION]`

Tag `v1.0.0` already exists locally. If it was pushed before Step 4, Zenodo will have
missed it. In that case create a new tag:

```bash
git tag -a v1.0.1 -m "v1.0.1 - release for Zenodo archiving"
git push origin v1.0.1
```

Zenodo will archive it and mint a DOI within a few minutes. It appears under
**Upload → My uploads**.

---

## Step 6 — Deposit the manuscript `[YOUR ACTION]`

The GitHub archive covers the **code**. The **paper** should be its own record so it can
be cited as a publication.

1. Zenodo → **New upload**
2. Upload the manuscript. Export a PDF from `paper/manuscript.md` (Pandoc or LaTeX).
3. **Resource type: Publication → Preprint**
4. Click **Load metadata from `.zenodo.json`**, or paste the fields manually.
5. Set **Licence: CC-BY-4.0**
6. Under **Related identifiers**, link the GitHub/software record and the STATS19
   dataset URL.
7. Publish.

---

## What NOT to upload

- **The raw STATS19 CSVs (255 MB).** They are already archived by the Department for
  Transport under the Open Government Licence. `src/download_data.py` retrieves the
  exact snapshot and `data/raw/checksums.sha256` fixes it. Re-uploading adds nothing
  and makes the deposit unwieldy. It is also `.gitignore`d, so it will not be included
  by accident.
- **The derived dataset (117 MB).** Reproducible byte-identically from the raw data by
  `src/prepare_data.py`, and the resulting SHA-256 is recorded. Also `.gitignore`d.

## What SHOULD be in the deposit

- Manuscript (PDF)
- All of `src/`
- `README.md`, `plan.md`, `progress.md`
- `docs/` including `data-notes.md` and `prior-work-scan.txt`
- `outputs/figures/` and `outputs/tables/`
- `paper/references.bib`
- `requirements.txt` and `requirements-lock.txt`

All of this is already in the `v1.0.0` tag.

---

## After publishing

1. Copy the DOI into `CITATION.cff` (`doi:` field) and into the manuscript's
   data-availability declaration.
2. Add the DOI to `progress.md` and your CV.
3. Commit and push; create a new tag if you want the DOI captured in the archive.
4. **Know which DOI is which:**
    - **Version DOI** — points to one specific version. Use in a CV entry for a
      specific release.
    - **Concept DOI** — always resolves to the latest version. Use when referring to
      "the project".

---

## Before depositing — a warning about the literature review

The results and methods in `paper/manuscript.md` are complete and written from the
actual analysis output. **The literature review is not, and should not be rushed.**

`references.bib` contains 99 references whose DOIs are all real and were verified
against Crossref. But a reference being real does not make citing it legitimate:

- **Do not cite a paper you have not read.** Citing on the basis of a title or abstract
  is a common way to misrepresent prior work, and reviewers notice.
- **Do not let anything other than the paper itself tell you what it found.** This
  applies to assistants, including me.
- **Prune the list.** 99 references is a search yield, not a bibliography. A tight 40
  well-understood citations is stronger than 99 thin ones.
- **Read `docs/prior-work-scan.txt` first**, and cite Zhao et al. (2026) in §1 and §5.2.

A preprint with an honest, narrower novelty claim will be judged far better than one
that overreaches and gets caught.

---

## Quick reference: what is already verified

| Check                                       | Status                        |
| ------------------------------------------- | ----------------------------- |
| Pipeline runs end to end                    | Passes                        |
| Derived dataset reproduces byte-identically | SHA-256 `eb95fc2d…`           |
| E-scooter codes verified against real data  | 5,631 of 5,631 nest correctly |
| Vehicle join integrity                      | 100% matched to own vehicle   |
| `openpyxl` declared                         | Added to `requirements.txt`   |
| Dependency versions pinned                  | `requirements-lock.txt`       |
| Bibliography DOIs real                      | 99 verified via Crossref      |
| Prior-work scan completed                   | `docs/prior-work-scan.txt`    |
| `.zenodo.json` valid JSON                   | Validated                     |
| Figures                                     | Six, 300 dpi, greyscale-safe  |
| Git commit and tag                          | `v1.0.0`, commit `5c3c647`    |
| Large files excluded from git               | Raw and derived data ignored  |
