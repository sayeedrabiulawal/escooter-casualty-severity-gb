"""
Generate a sentence-level worksheet for the literature review.

WHY THIS EXISTS
---------------
Writing a literature review is hard for a specific reason: you have to make an
argument USING other people's work, not just list it. This turns the 100-paper reading
list into a paragraph-by-paragraph scaffold that tells you, for each paragraph:

  * the argumentative job it has to do in the paper
  * the word budget, so the section cannot sprawl
  * the exact candidate papers, with their abstracts inline
  * the specific questions to answer while reading them

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
It does not write the review. It does not state what any paper found beyond quoting
the publisher's own abstract verbatim. Every prompt is in imperative voice
("Establish that...", "Summarise..."), left for the author to complete.

The reason is not pedantry. A literature review is the one section where a reader can
check your competence against the record, and it is the section a reviewer or an
interviewer probes first. Prose written from abstracts that nobody has read cannot be
defended, and misattributing a finding to a real author is misconduct.

Usage:
    python src/make_lit_review_worksheet.py
"""

from __future__ import annotations

import csv
import json
import textwrap
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
READING_CSV = PROJECT_ROOT / "docs" / "reading-list.csv"
READING_MD = PROJECT_ROOT / "docs" / "reading-list.md"
OUTPUT = PROJECT_ROOT / "docs" / "literature-review-worksheet.md"

# ---------------------------------------------------------------------------
# The structure of the review, and the argument each part must make.
#
# `job` is what the paragraph has to accomplish in the paper's overall argument.
# `questions` are what to extract while reading.
# `connects_to` is the paper's own contribution that this paragraph sets up.
# ---------------------------------------------------------------------------

SECTIONS: list[dict] = [
    {
        "id": "2.1",
        "title": "E-scooter injury epidemiology",
        "words": 450,
        "themes": ["escooter_epi", "escooter_severity"],
        "job": (
            "Establish that the existing evidence is dominated by single-centre clinical "
            "series, which describe injury patterns well but cannot supply a population "
            "denominator, a same-source comparison group, or national coverage. This is "
            "the foundation of your gap."
        ),
        "questions": [
            "What population did they study, and how many cases?",
            "What did they report about the mechanism of injury (rider fall vs collision)?",
            "Which injuries were most common or most serious?",
            "What is the key limitation for your purposes: single centre, no denominator, "
            "no comparison group, or selected by severity?",
        ],
        "must_cite": [
            "Zhao et al. (2026) — DOI 10.1016/j.aap.2026.108517. This is the closest "
            "prior work to your own. It MUST appear here, be described accurately, and be "
            "explicitly distinguished from your study.",
        ],
        "connects_to": (
            "Positions your national, collision-based, three-mode comparison as filling "
            "the population-denominator gap that clinical series cannot."
        ),
    },
    {
        "id": "2.2",
        "title": "Comparative injury severity across modes",
        "words": 400,
        "themes": ["vru_severity", "cycling_severity", "severity_methods"],
        "job": (
            "Show that comparing severity across road-user modes with a killed-or-"
            "seriously-injured outcome is established practice, and that pedal cycling "
            "and motorcycling are the standard comparison groups for a new two-wheel "
            "mode. This paragraph justifies your design choices."
        ),
        "questions": [
            "Which modes are compared, and why those?",
            "How is the outcome defined and what model is used?",
            "Which covariates recur across studies? (Use this to check your own list.)",
            "Do any of these studies include e-scooters at all?",
        ],
        "must_cite": [
            "At least one methods reference for logistic regression with a KASI outcome, "
            "to cite in §3.6 rather than re-describing the method from scratch.",
        ],
        "connects_to": (
            "Justifies comparing against BOTH pedal cycles and motorcycles, which is one "
            "of the four things distinguishing your study from Zhao et al."
        ),
    },
    {
        "id": "2.3",
        "title": "Police-reported collision data as a research source",
        "words": 350,
        "themes": ["police_reported_bias", "spatial_analysis"],
        "job": (
            "Demonstrate that you understand the weaknesses of your own data source "
            "before a reviewer points them out. Under-reporting, differential reporting "
            "by mode, and the difficulty of interpreting trends are the three things to "
            "cover."
        ),
        "questions": [
            "How large is under-reporting for non-injury and slight collisions?",
            "Is under-reporting differential by mode, and in which direction?",
            "What do studies conclude about the validity of trend analysis on this data?",
        ],
        "must_cite": [
            "The STATS19 dataset itself, for provenance: Department for Transport, "
            "Road safety open data, Open Government Licence v3.0.",
        ],
        "connects_to": (
            "Sets up §5.4 limitations, and shows that your caution about exposure "
            "denominators is informed rather than defensive."
        ),
    },
    {
        "id": "2.4",
        "title": "Spatial and environmental determinants",
        "words": 300,
        "themes": ["speed_limit", "scooter_regulation"],
        "job": (
            "Establish why speed limit, lighting, road type, urban/rural classification "
            "and junction detail belong in the model, since a reviewer will ask why you "
            "included exactly those covariates."
        ),
        "questions": [
            "What is the evidence for speed limit affecting severity?",
            "What is known about lighting and the road environment?",
            "What does the micromobility policy literature say about rental schemes and "
            "regulation? (Needed for §5.3.)",
            "Does any of it address helmet use? (STATS19 has no helmet field, so if the "
            "literature does, that is a gap you must acknowledge.)",
        ],
        "must_cite": [],
        "connects_to": (
            "Justifies the covariate set, and feeds the policy discussion in §5.3. "
            "Also explains why speed limit turned out non-significant within your "
            "e-scooter cohort."
        ),
    },
]


GAP_STATEMENT = {
    "id": "Gap",
    "title": "Gap statement",
    "words": 150,
    "job": (
        "Synthesise the four themes into one precise, checkable gap that your research "
        "questions answer directly. This must not be a repeat of the Introduction: it "
        "should be an EVIDENCE-BASED conclusion from the literature, not an assertion."
    ),
    "template": [
        "Across these four strands, the evidence is characterised by [what pattern you "
        "found — e.g. clinical dominance, single-mode focus, absence of national "
        "comparison].",
        "Specifically, [name the gap] . Zhao et al. (2026) provide [what they provide] "
        "for England, but do not [what they do not do — state this accurately after "
        "reading their abstract].",
        "This study therefore [what you do], addressing [the gap] by [your method], and "
        "testing [the threat to validity you handle, i.e. the reporting-method change].",
    ],
    "connects_to": "Leads directly into §3. A reader should be able to check §4 against it.",
}

DISCUSSION_TODO = {
    "title": "§5.2 — Comparison with existing literature",
    "words": 400,
    "job": (
        "Put your findings back into the literature. This is NOT a second review: it "
        "compares what you found with what others found, and offers mechanisms for any "
        "disagreement."
    ),
    "questions": [
        "Does your young, urban, male-dominant profile agree with the clinical "
        "literature? If not, why might that be?",
        "How does your e-scooter odds ratio compare with Zhao et al., and what does "
        "your study add beyond theirs?",
        "Where you disagree with published work, what is the mechanism? A disagreement "
        "left unexplained reads as an error.",
    ],
    "must_cite": ["Zhao et al. (2026) again, explicitly."],
}


def load_papers() -> list[dict]:
    if not READING_CSV.exists():
        raise SystemExit(
            f"Missing {READING_CSV}.\nRun first: python src/build_reading_list.py"
        )
    with READING_CSV.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def abstracts() -> dict[str, str]:
    """Pull verbatim abstracts out of the generated reading list."""
    if not READING_MD.exists():
        return {}

    found: dict[str, str] = {}
    current_doi = None
    buffer: list[str] = []

    for line in READING_MD.read_text(encoding="utf-8").splitlines():
        if "doi.org/" in line:
            match = line.strip()
            # DOI appears inside a markdown link: [doi.org/10.x](https://doi.org/10.x)
            if "](https://doi.org/" in match:
                current_doi = match.split("](https://doi.org/")[1].rstrip(")").strip()
                buffer = []
        elif current_doi and line.startswith("> ") and "verbatim" not in line:
            text = line[2:].strip()
            if text and not text.startswith("*Publisher"):
                buffer.append(text)
        elif current_doi and line.strip() == "" and buffer:
            if current_doi not in found:
                found[current_doi] = " ".join(buffer)
            current_doi = None
            buffer = []

    for doi, text in list(found.items()):
        found[doi] = " ".join(text.split())
    return found


def wrap(text: str, width: int = 96, indent: str = "") -> list[str]:
    """Wrap text, optionally as a Markdown bullet.

    For bullets the first line gets "- " and continuation lines get spaces of the
    same width. Using the bullet marker for both would render each continuation as
    a separate bullet, which silently changes the meaning of a list.
    """
    if indent == "- ":
        return textwrap.wrap(
            text, width=width, initial_indent="- ", subsequent_indent="  "
        )
    return textwrap.wrap(
        text, width=width, initial_indent=indent, subsequent_indent=indent
    )


def render_section(section: dict, papers: list[dict], abstract_map: dict[str, str]) -> list[str]:
    lines: list[str] = [
        "",
        "---",
        "",
        f"## {section['id']} — {section['title']}",
        "",
        f"**Word budget: {section['words']}.** "
        f"{len([p for p in papers if p['theme'] in section['themes']])} candidate paper(s).",
        "",
        "### The job this section must do",
        "",
    ]
    lines += wrap(section["job"])
    lines += [
        "",
        "### What to extract while reading",
        "",
    ]
    for question in section["questions"]:
        lines += wrap(question, indent="- ")

    if section.get("must_cite"):
        lines += ["", "### Must be cited here", ""]
        for item in section["must_cite"]:
            lines += wrap(item, indent="- ")

    lines += [
        "",
        "### What this sets up in your own paper",
        "",
    ]
    lines += wrap(section["connects_to"])

    lines += ["", "### Candidate papers", ""]
    relevant = [p for p in papers if p["theme"] in section["themes"]]
    seen: set[str] = set()
    for index, paper in enumerate(relevant, 1):
        if paper["doi"] in seen:
            continue
        seen.add(paper["doi"])
        title = paper["title"]
        lines.append(f"**{section['id']}.{index}** {title}")
        lines.append("")
        lines.append(
            f"*{paper['author']} ({paper['year']})*"
            + (f", {paper['venue']}" if paper["venue"] else "")
            + f". Cited {paper['citations']}x. https://doi.org/{paper['doi']}"
        )
        lines.append("")
        body = abstract_map.get(paper["doi"], "")
        if body:
            lines.append(
                "*Publisher abstract, quoted verbatim. Read the full paper before "
                "citing any finding.*"
            )
            lines.append("")
            for chunk in wrap(body, width=95):
                lines.append(f"> {chunk}")
        else:
            lines.append(
                "> *No abstract available. Open the DOI and read it.*"
            )
        lines.append("")
        lines.append("→ *Notes (what did it find? usable for which claim?):*")
        lines.append("")
        lines.append("")

    return lines


def main() -> int:
    papers = load_papers()
    abstract_map = abstracts()

    header = [
        "# Literature Review Worksheet",
        "",
        "A paragraph-by-paragraph scaffold for `paper/manuscript.md` §2 and §5.2.",
        "",
        f"Generated by `python src/make_lit_review_worksheet.py` from "
        f"`docs/reading-list.csv` ({len(papers)} entries).",
        "",
        "---",
        "",
        "## How to use this",
        "",
        "**This is a scaffold, not a draft.** No prose here has been written for you, and",
        "no paper has been characterised beyond quoting its own abstract. Every prompt is",
        "a job for you to do.",
        "",
        "Work in order. Each section below maps to one place in the manuscript, so you",
        "finish a section's reading and can write that part immediately.",
        "",
        "For each paper: read the abstract, decide if it earns a place, then **open the",
        "full paper** before citing it as a finding. Record your notes in",
        "`docs/reading-list.csv` (there is a `read` column and a `notes` column).",
        "",
        "### The five rules that matter",
        "",
        "1. **Read before you cite.** An abstract is the authors' claim about their own",
        "   work. Abstracts routinely omit the sample, the limitations, and any result",
        "   that does not flatter the framing.",
        "2. **Cite the claim you verified.** If you have not confirmed that a paper says",
        "   what you are about to write, do not attach its name to the sentence.",
        "3. **Never let a summary stand in for a source** — including mine, and including",
        "   anything an assistant tells you a paper found.",
        "4. **Prune hard.** A tight 40 accurate citations beats 100 loose ones. Delete",
        "   unused entries from `paper/references.bib` as you go.",
        "5. **Report disagreement honestly.** Where your finding conflicts with the",
        "   literature, say so and offer a mechanism. An unexplained conflict reads as an",
        "   error.",
        "",
        "### Rough time budget",
        "",
        f"| Section | Words | Papers | Reading | Writing |",
        f"|---|---|---|---|---|",
        f"| 2.1 | 450 | {len([p for p in papers if p['theme'] in SECTIONS[0]['themes']])} | 1.5 h | 1 h |",
        f"| 2.2 | 400 | {len([p for p in papers if p['theme'] in SECTIONS[1]['themes']])} | 1.5 h | 1 h |",
        f"| 2.3 | 350 | {len([p for p in papers if p['theme'] in SECTIONS[2]['themes']])} | 1 h | 0.75 h |",
        f"| 2.4 | 300 | {len([p for p in papers if p['theme'] in SECTIONS[3]['themes']])} | 1 h | 0.75 h |",
        f"| Gap | 150 | — | — | 0.5 h |",
        f"| 5.2 | 400 | reuse | — | 1 h |",
        "",
        "About **six to eight hours** in total, spread however you like. That is the whole",
        "remaining job on the preprint.",
        "",
        "---",
        "",
        "# Part 1 — the Literature Review (§2)",
    ]

    lines = header
    for section in SECTIONS:
        lines += render_section(section, papers, abstract_map)

    lines += [
        "",
        "---",
        "",
        f"## {GAP_STATEMENT['id']} — {GAP_STATEMENT['title']}",
        "",
        f"**Word budget: {GAP_STATEMENT['words']}.** One paragraph. End of §2.",
        "",
        "### The job this section must do",
        "",
    ]
    lines += wrap(GAP_STATEMENT["job"])
    lines += [
        "",
        "### Sentence structure to complete",
        "",
        "*Fill the brackets with what you actually found. Delete any sentence that does "
        "not hold.*",
        "",
    ]
    for index, sentence in enumerate(GAP_STATEMENT["template"], 1):
        lines += wrap(f"{index}. {sentence}", width=95, indent="  ")
        lines.append("")
    lines += wrap(GAP_STATEMENT["connects_to"])

    lines += [
        "",
        "---",
        "",
        "# Part 2 — the Discussion comparison (§5.2)",
        "",
        f"## {DISCUSSION_TODO['title']}",
        "",
        f"**Word budget: {DISCUSSION_TODO['words']}.**",
        "",
        "### The job this section must do",
        "",
    ]
    lines += wrap(DISCUSSION_TODO["job"])
    lines += ["", "### What to extract", ""]
    for question in DISCUSSION_TODO["questions"]:
        lines += wrap(question, indent="- ")
    lines += ["", "### Must be cited here", ""]
    for item in DISCUSSION_TODO["must_cite"]:
        lines += wrap(item, indent="- ")

    lines += [
        "",
        "---",
        "",
        "# When you have finished",
        "",
        "1. Replace the `TODO` block in `paper/manuscript.md` §2 and the `TODO` in §5.2",
        "   with your prose.",
        "2. Delete unused entries from `paper/references.bib`.",
        "3. Re-render and check the warning has cleared:",
        "",
        "```powershell",
        "& .venv\\Scripts\\python.exe src/render_manuscript.py",
        "```",
        "",
        "The renderer warns if any `TODO` marker would appear in the PDF. When that",
        "warning is gone, the preprint is ready to deposit as a second Zenodo record.",
        "",
        "Do not deposit the preprint while the warning is still showing. A Zenodo record",
        "is permanent and cannot be deleted.",
    ]

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Worksheet written to {OUTPUT}")
    print(f"  {OUTPUT.stat().st_size / 1024:.0f} KB, {len(lines)} lines")
    print(f"  {len(papers)} papers mapped: ", end="")
    print(", ".join(f"{s['id']}={len([p for p in papers if p['theme'] in s['themes']])}" for s in SECTIONS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
