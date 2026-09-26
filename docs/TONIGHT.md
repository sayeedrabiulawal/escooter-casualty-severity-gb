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

## Good news: you don't need ORCID, an affiliation, or GitHub

None of those are required to deposit on Zenodo. The tooling now handles their
absence by **removing** the fields cleanly, because a placeholder like
`0000-0000-0000-0000` in a permanent record looks broken.

| Thing        | Required?                   | What happens if you skip it                                  |
| ------------ | --------------------------- | ------------------------------------------------------------ |
| Your surname | **Yes** — the one essential | Author name would read as a placeholder                      |
| ORCID iD     | No                          | The `orcid` field is removed from the metadata               |
| Affiliation  | No                          | Defaults to **"Independent Researcher"**                     |
| GitHub repo  | No                          | The GitHub link is removed; the code is still in the deposit |

**"Independent Researcher" is the correct and honest affiliation** for someone not
currently enrolled or employed at an institution. It is a standard value on Zenodo, and
it is what you are. Do not invent an affiliation.

You can add ORCID and an affiliation later by publishing a new version — so registering
one is worth doing when you have five minutes, but it should not hold up tonight.

---

## Step 1 — Fill in your surname (1 minute)

Replace `YourSurname` with your actual family name. Everything else is optional, so
this is a complete command:

```powershell
cd 'd:\Apply\Sayed'
& .venv\Scripts\python.exe src/personalise.py --dry-run --surname "YourSurname"
```

Check the dry run, then run it again **without** `--dry-run`.

### If you do have an ORCID, add it

Registering takes about two minutes at <https://orcid.org> and is genuinely worth doing
— it links your publications to you permanently. If you have one:

```powershell
& .venv\Scripts\python.exe src/personalise.py `
    --surname "YourSurname" `
    --orcid "0000-0000-0000-0000"
```

Add `--affiliation "University Name"` if you are currently at an institution, and
`--github "https://github.com/you/repo"` if you make a public repo.

The script **verifies** afterwards that `.zenodo.json` still parses and contains no
placeholders. It also prints anything it could not resolve, including the manuscript
`TODO` markers, so nothing is left behind silently.

---

## Step 2 — Build the archive (30 seconds)

```powershell
& .venv\Scripts\python.exe src/make_deposit.py --include-pdf paper/manuscript.pdf
```

This produces:

| File                                                       | What it is                       |
| ---------------------------------------------------------- | -------------------------------- |
| `outputs/deposit/escooter-casualty-severity-gb-v1.0.0.zip` | The archive to upload (~0.85 MB) |
| `outputs/deposit/zenodo-metadata-SOFTWARE.txt`             | Field-by-field metadata to paste |
| `outputs/deposit/zenodo-metadata-PREPRINT.txt`             | Same, for later                  |

Raw data and the derived dataset are **deliberately excluded**. They are already
published by the Department for Transport and regenerate from the included scripts.
That is why a 380 MB project becomes a 0.85 MB deposit.

---

## Step 3 — Upload to Zenodo (5 minutes)

1. Sign in at <https://zenodo.org>. Signing in **with ORCID** is easiest if you have
   one; otherwise register an account with your email.
2. Click **New upload**.
3. Upload `escooter-casualty-severity-gb-v1.0.0.zip`.
4. Open `outputs/deposit/zenodo-metadata-SOFTWARE.txt` and paste each field into the
   matching box.
5. Set **Resource type: Software**, **Licence: MIT**, **Access: Open**.
6. Add the related identifier for the STATS19 dataset (it is in the sheet).
7. **Proofread the title and your name.** Then click **Publish**.

Zenodo mints the DOI immediately. It appears under **Upload → My uploads**.

---

## Step 4 — Record the DOI (2 minutes)

Once you have it, paste it into:

- `CITATION.cff` → the `doi:` line
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

### Start here: the worksheet

**`docs/literature-review-worksheet.md` (118 KB) is the thing to open first.** It breaks
§2 into paragraph-by-paragraph jobs. For each one it gives you:

- the argument that paragraph has to make in your paper
- the word budget, so the section cannot sprawl
- the candidate papers, with their **publisher abstracts quoted verbatim, inline**
- the specific questions to answer while reading
- what each paragraph sets up in your own contribution

Generate or regenerate it:

```powershell
& .venv\Scripts\python.exe src/make_lit_review_worksheet.py
```

**It is a scaffold, not a draft.** No prose has been written for you and no paper has
been characterised beyond quoting its own abstract. Every prompt is a job for you to do
— which is the point, because §2 is the section a reviewer or interviewer probes first,
and prose written from abstracts nobody has read cannot be defended.

Rough budget: **six to eight hours** for the whole remaining job, spread however you
like. Time estimates per subsection are in the worksheet.

### Also useful: the raw reading list

`docs/reading-list.md` (**120 KB**) is the thing that unlocks the review. It holds
**100 entries across 99 papers, 61 of them with the publisher's abstract quoted
verbatim**, grouped by the manuscript section each one feeds, most-cited first.

Regenerate or refresh it:

```powershell
& .venv\Scripts\python.exe src/build_reading_list.py
& .venv\Scripts\python.exe src/build_reading_list.py --offline   # cache only
```

How to use it:

1. **Work theme by theme.** Each theme maps to one section (`2.1` epidemiology,
   `2.2` methods, `2.3` under-reporting, `2.4` spatial). You finish a section's
   reading and can write it straight away.
2. **Start with 2.1 and 2.2.** They carry the most weight and set up your three-way
   comparison.
3. **Use `docs/reading-list.csv` to track progress.** It has a blank `read` column
   and a `notes` column.
4. **38 papers have no abstract** in the source. Open the DOI for those.

**The abstracts are the publishers' own words, quoted verbatim — not my summaries.**
I have not read these papers. An abstract is a claim by an author about their own
work, and abstracts routinely omit the limitations, the sample, and the direction of
an effect that does not flatter the framing. For anything you cite as a finding, open
the paper and check that it supports the exact sentence you are attaching it to.

A review that misrepresents three papers is worse than one that cites fifteen
accurately.

### Then

1. **Prune `paper/references.bib`.** Pick the ~40 that genuinely support a point and
   delete the rest. A tight 40 is stronger than a loose 99.
2. **Read `docs/prior-work-scan.txt`** and cite Zhao et al. (2026) in §1 and §5.2.
   Your novelty claim depends on how you position against it.
3. **Resolve the remaining `TODO` markers** in `paper/manuscript.md`: funding,
   AI-use disclosure, and author contributions.
4. **Re-render and check no TODOs remain:**

```powershell
& .venv\Scripts\python.exe src/render_manuscript.py
```

The renderer **warns you** if any `TODO` marker would appear in the PDF. When that
warning is gone, the preprint is ready to deposit as a second Zenodo record.

---

## The one-line summary

| Record       | Ready now?                            | Action                         |
| ------------ | ------------------------------------- | ------------------------------ |
| **Software** | **Yes**                               | Deposit tonight — Steps 1 to 5 |
| Preprint     | Not yet — needs the literature review | Deposit after §2 is written    |

A software DOI tonight is a genuine result you can put on your CV tomorrow. The
preprint becomes a second DOI when it is worth reading in full.
