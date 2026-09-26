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

## Metadata status: done

The author name and affiliation are already set in every file, via
`src/personalise.py`, so there is nothing to fill in here.

| Item         | Value                                                                       |
| ------------ | --------------------------------------------------------------------------- |
| Author       | Rabiul Awal Sayeed                                                          |
| Affiliation  | Department of Civil Engineering, Hebei University of Science and Technology |
| ORCID iD     | not supplied — the `orcid` field was **removed**, not left as a placeholder  |
| GitHub repo  | not supplied — the GitHub link was removed; the code is still in the deposit |

ORCID and a repository URL are **not required** by Zenodo. The tooling handles their
absence by removing the fields cleanly, because a placeholder like
`0000-0000-0000-0000` in a permanent record looks broken.

Registering an ORCID at <https://orcid.org> takes about two minutes and is genuinely
worth doing, but note that it **cannot be added to this DOI afterwards** without
publishing a new version. If you want it on the record, register before you deposit.

To change any value later, re-run `src/personalise.py` with the corrected argument; it
is idempotent.

---

## Step 1 — Optional: add an ORCID before depositing

Everything else is already set. This is the only metadata step left, and it is purely\noptional.

Registering takes about two minutes at <https://orcid.org> and is genuinely worth doing\n— it links your publications to you permanently. If you register one:

```powershell
& .venv\Scripts\python.exe src/personalise.py `
    --given "Rabiul Awal" --family "Sayeed" `
    --orcid "0000-0000-0000-0000"
```

Add `--github "https://github.com/you/repo"` if you make a public repo. Re-running
replaces the existing values, so this is safe to repeat.

The script **verifies** afterwards that `.zenodo.json` still parses and contains no
placeholders. It also prints anything it could not resolve, including the manuscript
`TODO` markers, so nothing is left behind silently.

---

## Step 2 — Tag, then build the archive (1 minute)

The archive name and the version field come from `git describe`, so **tag the commit
first**. Without a tag you get a version like `v1.0.1-7-gd9b86f9`, which is honest but
is not a release version, and that label is permanent once deposited.

```powershell
git tag v1.0.0 -f      # only if the first deposit should be v1.0.0; see the note below
& .venv\Scripts\python.exe src/make_deposit.py
```

This produces:

| File                                                          | What it is                       |
| ------------------------------------------------------------- | -------------------------------- |
| `outputs/deposit/escooter-casualty-severity-gb-<version>.zip` | The archive to upload (~1.4 MB)  |
| `outputs/deposit/zenodo-metadata-SOFTWARE.txt`                | Field-by-field metadata to paste |
| `outputs/deposit/zenodo-metadata-PREPRINT.txt`                | Same, for the preprint record    |

**The manuscript PDF is deliberately excluded** unless you pass
`--include-pdf paper/manuscript.pdf`. The PDF belongs to the publication record, not
the software record, and while the manuscript is a draft it still carries
`TODO — VERIFY BEFORE SUBMITTING` notes. Do not put a draft PDF in a permanent archive.

Raw data and the derived dataset are excluded too. They are already published by the
Department for Transport and regenerate from the included scripts. That is why a
380 MB project becomes a ~1.4 MB deposit.

---

## Step 3 — Upload to Zenodo (5 minutes)

1. Sign in at <https://zenodo.org>. Signing in **with ORCID** is easiest if you have
   one; otherwise register an account with your email.
2. Click **New upload**.
3. Upload the archive, `escooter-casualty-severity-gb-<version>.zip` — take the exact
   filename from the build output, since it carries the version.
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
