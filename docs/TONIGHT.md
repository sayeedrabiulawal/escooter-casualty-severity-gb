# Tonight: Deposit to Zenodo

**Read this first — one recommendation, then the steps.**

---

## Do the software record tonight. Do the preprint next.

You can have a **real, citable DOI tonight**, and I recommend you take it. But it should
be for the **code**, not the paper.

### Why not the paper tonight

The manuscript's PDF currently contains **six visible `TODO` markers**, including this
one, which is the entire literature review section:

```
## 2. Literature Review

> TODO — YOU MUST WRITE THIS SECTION.
```

A Zenodo record is **permanent**. It cannot be deleted — only superseded by a new
version with a different DOI. So if you deposit the preprint tonight and a professor
clicks the DOI tomorrow, they will read a paper with no literature review and a
heading that says "you must write this section."

That is worse for your application than having no publication yet. It signals that the
work was rushed, which is the opposite of what this project currently demonstrates.

### Why the software record is fine tonight

The code is genuinely complete:

- It runs end to end and rebuilds every output from scratch
- The derived dataset reproduces **byte-identically** (SHA-256 verified)
- It catches and documents its own edge cases
- Every method is explained in the docstrings

A software DOI is a normal, respected deposit. It is honest, and it is finished.

**Result: you get a DOI tonight, with zero risk.**

---

## Step 1 — Get an ORCID iD (2 minutes)

<https://orcid.org> → Register. Free. **Do this first** — several of the steps below
need it, and it is the one thing you cannot do without.

Use the same form of your name everywhere: ORCID, Zenodo, GitHub, CV.

---

## Step 2 — Fill in your details (1 minute)

One command writes your name, ORCID, and affiliation into all eight files. Check it
first with `--dry-run`:

```powershell
cd 'd:\Apply\Sayed'
& .venv\Scripts\python.exe src/personalise.py --dry-run `
    --surname "YourSurname" `
    --orcid "0000-0000-0000-0000" `
    --affiliation "Your University" `
    --github "https://github.com/yourname/your-repo"
```

If the dry run looks right, run the same command **without** `--dry-run`.

The script prints anything it could not resolve, so nothing is left behind silently.

---

## Step 3 — Build the archive (30 seconds)

```powershell
& .venv\Scripts\python.exe src/make_deposit.py --include-pdf paper/manuscript.pdf
```

This produces:

| File | What it is |
|---|---|
| `outputs/deposit/escooter-casualty-severity-gb-v1.0.0.zip` | The archive to upload (~0.85 MB, 46 files) |
| `outputs/deposit/zenodo-metadata-SOFTWARE.txt` | Field-by-field metadata to paste |
| `outputs/deposit/zenodo-metadata-PREPRINT.txt` | Same, for later |

Raw data and the derived dataset are **deliberately excluded**. They are already
published by the Department for Transport and regenerate from the included scripts.
That is why a 380 MB project becomes a 0.85 MB deposit.

---

## Step 4 — Upload to Zenodo (5 minutes)

1. Sign in at <https://zenodo.org>. **Signing in with GitHub or ORCID is easiest** and
   links your identities automatically.
2. Click **New upload**.
3. Upload `escooter-casualty-severity-gb-v1.0.0.zip`.
4. Open `outputs/deposit/zenodo-metadata-SOFTWARE.txt` and paste each field into the
   matching box.
5. Set **Resource type: Software**, **Licence: MIT**, **Access: Open**.
6. Add the related identifier for the STATS19 dataset (in the sheet).
7. **Proofread the title, your name, and your ORCID.** Then click **Publish**.

Zenodo mints the DOI immediately. It appears under **Upload → My uploads**.

---

## Step 5 — Record the DOI (2 minutes)

Once you have it, paste it into:

- `CITATION.cff` → the `doi:` line and the corresponding URL
- `paper/manuscript.md` → the **Code availability** declaration
- `progress.md` → the status table
- Your CV

Then commit:

```powershell
git add -A
git commit -m "Add Zenodo DOI"
```

---

## Then: finish the preprint

The only substantial thing left is the **literature review** (§2) and the **§5.2
comparison**. Roughly 1,500 words. Everything else — methods, results, discussion,
limitations, figures, tables — is written from the real numbers.

To do it:

1. Open `paper/references.bib`. The 99 entries are grouped by theme name in
   `src/build_bibliography.py` (`SEARCHES`). The theme tells you which section a paper
   belongs in.
2. Skim the candidates, pick the ~40 that genuinely support a point you want to make,
   and **delete the rest**. A tight 40 is stronger than a loose 99.
3. **Read each paper before citing it.** Do not cite from a title or abstract alone,
   and do not accept anyone else's summary of what a paper found — including mine.
4. Read `docs/prior-work-scan.txt` and cite Zhao et al. (2026) in §1 and §5.2.
5. Resolve the remaining `TODO` markers in `paper/manuscript.md`:
   funding, AI-use disclosure, and author contributions.
6. Re-render and check no TODOs remain:

```powershell
& .venv\Scripts\python.exe src/render_manuscript.py
```

The renderer **warns you** if any `TODO` marker would appear in the PDF. When that
warning is gone, the preprint is ready to deposit as a second Zenodo record.

---

## The one-line summary

| Record | Ready now? | Action |
|---|---|---|
| **Software** | **Yes** | Deposit tonight — Steps 1 to 5 |
| Preprint | Not yet — needs the literature review | Deposit after §2 is written |

A software DOI tonight is a genuine result you can put on your CV tomorrow. The
preprint becomes a second DOI when it is worth reading in full.
