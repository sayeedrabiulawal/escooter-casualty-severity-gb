"""
Build a reading list of candidate papers for the literature review.

WHY THIS EXISTS
---------------
`references.bib` holds 99 DOI-verified references, but a list of 99 titles is not
something you can write a literature review from. This produces a per-theme reading
list with each paper's **verbatim publisher abstract**, so you can decide what to read
in minutes rather than opening 99 tabs.

WHAT THIS DOES NOT DO
---------------------
It does not summarise, interpret, or characterise any paper. It quotes the abstract
exactly as the publisher deposited it, with attribution and a DOI. Writing the review
from these abstracts alone would be misrepresentation, so the output says so at the top.

Abstracts are fetched from OpenAlex, which reconstructs them from each publisher's
deposited word positions. Crossref's own abstract coverage is poor (31 of 99 here).

Usage:
    python src/build_reading_list.py
    python src/build_reading_list.py --refresh     # ignore the cache and re-fetch
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CROSSREF_JSON = PROJECT_ROOT / "docs" / "crossref-results.json"
CACHE_JSON = PROJECT_ROOT / "docs" / "reading-list-cache.json"
OUTPUT_MD = PROJECT_ROOT / "docs" / "reading-list.md"
OUTPUT_CSV = PROJECT_ROOT / "docs" / "reading-list.csv"

OPENALEX = "https://api.openalex.org/works"
HEADERS = {
    "User-Agent": "escooter-lit-review/1.0 (mailto:researcher@example.org)",
    "Accept": "application/json",
}

# Which manuscript section each search theme feeds. This is the link that makes the
# reading list actionable: it tells you WHY you are reading a paper.
THEME_TO_SECTION: dict[str, tuple[str, str]] = {
    "escooter_epi": (
        "2.1",
        "E-scooter injury epidemiology. Establishes what is known clinically and what "
        "a collision dataset can add that a hospital series cannot.",
    ),
    "escooter_severity": (
        "2.1 / 5.2",
        "Severity modelling for e-scooters specifically. This is where Zhao et al. "
        "belongs, and where you must state what your study adds beyond it.",
    ),
    "micromobility_safety": (
        "2.1 / 5.3",
        "Micromobility safety and policy. Use for the regulatory context: rental "
        "schemes legal, private use not.",
    ),
    "vru_severity": (
        "2.2",
        "Comparative severity across modes. Justifies comparing against both pedal "
        "cycles and motorcycles rather than one.",
    ),
    "cycling_severity": (
        "2.2",
        "Cyclist severity determinants. Your reference category is pedal cycling, so "
        "this is the benchmark your odds ratio is measured against.",
    ),
    "severity_methods": (
        "2.2 / 3.6",
        "Methods: logistic regression with a killed-or-seriously-injured outcome. "
        "Cite for method, not for findings.",
    ),
    "police_reported_bias": (
        "2.3",
        "Police-reported data as a source: under-reporting and its differential "
        "nature. Essential for your limitations section.",
    ),
    "speed_limit": (
        "2.4 / 5.3",
        "Speed limit and the road environment. Note that speed limit is NOT "
        "significant within your e-scooter cohort: this literature helps explain why.",
    ),
    "spatial_analysis": (
        "2.4",
        "Spatial analysis of collisions. Supports the urban/rural finding and any "
        "mapping.",
    ),
    "scooter_regulation": (
        "2.4 / 5.3",
        "Regulation, helmets, and rental schemes. STATS19 has no helmet field, so "
        "this is where you explain what you cannot test.",
    ),
}

# Sort within each theme by citation count, which puts the influential work a referee
# will expect you to have engaged with at the top.
UNTITLED = "(no title recorded)"


def load_crossref() -> dict[str, list[dict]]:
    if not CROSSREF_JSON.exists():
        raise SystemExit(
            f"Missing {CROSSREF_JSON}. Run first:\n  python src/build_bibliography.py"
        )
    return json.loads(CROSSREF_JSON.read_text(encoding="utf-8"))


class BudgetExhausted(RuntimeError):
    """Raised when OpenAlex's shared free daily budget is used up.

    OpenAlex grants an anonymous daily request budget that is **shared by everyone
    on the same network IP address**. Once it is gone, no amount of retrying helps,
    and continuing to hammer the endpoint only delays the next success. The run
    stops and uses whatever the cache already holds.
    """


# Consecutive 429s tolerated before concluding the budget is gone.
MAX_CONSECUTIVE_429 = 3
_consecutive_429 = 0


def request_json(url: str, tries: int = 6) -> dict | None:
    """GET JSON with backoff. Aborts when the shared OpenAlex budget is exhausted."""
    global _consecutive_429

    for attempt in range(1, tries + 1):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=60) as response:
                _consecutive_429 = 0
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                _consecutive_429 += 1
                body = ""
                try:
                    body = exc.read().decode("utf-8", errors="replace")[:200]
                except Exception:  # noqa: BLE001
                    pass
                if "budget" in body.lower() or _consecutive_429 >= MAX_CONSECUTIVE_429:
                    raise BudgetExhausted(body or "HTTP 429") from exc
                time.sleep(min(2 * attempt, 15))
                continue
            return None
        except Exception:  # noqa: BLE001 - network problems must not abort the run
            time.sleep(2 * attempt)
    return None


def reconstruct_abstract(inverted_index: dict | None) -> str:
    """Rebuild abstract text from OpenAlex's word-position index.

    OpenAlex stores abstracts as {word: [positions]} to avoid redistributing the
    publisher's full text. Sorting by position restores the original order.
    """
    if not inverted_index:
        return ""
    positioned: list[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        for position in positions:
            positioned.append((position, word))
    positioned.sort()
    text = " ".join(word for _, word in positioned)
    return re.sub(r"\s+", " ", text).strip()


def fetch_openalex(dois: list[str], refresh: bool, offline: bool = False) -> dict[str, dict]:
    """Return {doi: {abstract, citations, oa_url}} for as many DOIs as possible.

    Prefers the cache. Stops cleanly if OpenAlex's shared daily budget is exhausted,
    keeping whatever was already retrieved rather than failing the whole run.
    """
    result: dict[str, dict] = {}
    if CACHE_JSON.exists() and not refresh:
        result = json.loads(CACHE_JSON.read_text(encoding="utf-8"))

    if offline:
        print(f"Offline mode: using {len(result)} cached record(s) only.")
        return result

    if not refresh and all(doi.lower() in result for doi in dois):
        print(f"Using cache ({len(result)} records). Pass --refresh to re-fetch.")
        return result

    pending = [doi for doi in dois if doi.lower() not in result]
    print(f"Fetching {len(pending)} record(s) from OpenAlex in batches of 25...")

    batch_size = 25
    for start in range(0, len(pending), batch_size):
        chunk = pending[start : start + batch_size]
        query = (
            f"{OPENALEX}?filter=doi:" + "|".join(chunk)
            + f"&per-page={batch_size}&select=doi,title,abstract_inverted_index,"
            "cited_by_count,publication_year,open_access,best_oa_location"
        )

        try:
            payload = request_json(query)
        except BudgetExhausted:
            print(
                "\n  [STOP] OpenAlex's free daily budget is exhausted.\n"
                "         It is shared by everyone on this network's IP address, so it\n"
                "         resets on OpenAlex's schedule, not on demand.\n"
                f"         Continuing with the {len(result)} record(s) already cached.\n"
                "         Re-run later, or tomorrow, to fill the gaps."
            )
            break

        if payload is None:
            # Fall back to one-at-a-time rather than losing the whole chunk.
            print(f"  batch at {start} failed; retrying individually")
            for doi in chunk:
                try:
                    single = request_json(
                        f"{OPENALEX}/doi:{doi}?select=doi,title,abstract_inverted_index,"
                        "cited_by_count,publication_year,open_access,best_oa_location"
                    )
                except BudgetExhausted:
                    print("\n  [STOP] OpenAlex budget exhausted during individual retries.")
                    payload = None
                    break
                if single:
                    result[doi.lower()] = summarise(single)
                time.sleep(0.4)
            else:
                payload = {"results": []}
            if payload is None:
                break
        else:
            for work in payload.get("results", []):
                doi = (work.get("doi") or "").replace("https://doi.org/", "").lower()
                if doi:
                    result[doi] = summarise(work)
            print(f"  {start + len(chunk):>3}/{len(pending)}  (returned {len(payload.get('results', []))})")
            time.sleep(1.0)

        CACHE_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")

    return result


def summarise(work: dict) -> dict:
    oa_location = work.get("best_oa_location") or {}
    return {
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
        "citations": work.get("cited_by_count", 0),
        "year": work.get("publication_year"),
        "oa_url": oa_location.get("pdf_url") or oa_location.get("landing_page_url") or "",
        "title": work.get("title") or "",
    }


def first_author(item: dict) -> str:
    authors = item.get("author") or []
    if not authors:
        return "Unknown"
    family = authors[0].get("family") or authors[0].get("name") or "Unknown"
    return f"{family} et al." if len(authors) > 1 else family


def year_of(item: dict) -> str:
    issued = (item.get("issued") or {}).get("date-parts") or [[None]]
    if issued and issued[0] and issued[0][0]:
        return str(issued[0][0])
    return "n.d."


def console_safe(value: str) -> str:
    """Downgrade typographic characters so a cp1252 console cannot raise."""
    for original, simple in {
        "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-",
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2026": "...",
        "\u00a0": " ", "\u03b2": "beta", "\u2265": ">=", "\u2264": "<=",
    }.items():
        value = value.replace(original, simple)
    return value.encode("ascii", errors="replace").decode("ascii")


def build(theme_data: dict[str, list[dict]], enriched: dict[str, dict]) -> tuple[list[dict], dict[str, list[dict]]]:
    """Merge Crossref metadata with the OpenAlex enrichment."""
    rows: list[dict] = []
    by_theme: dict[str, list[dict]] = {}

    for theme, items in theme_data.items():
        section, purpose = THEME_TO_SECTION.get(theme, ("?", "Unmapped theme."))
        collected: list[dict] = []

        for item in items:
            doi = (item.get("DOI") or "").strip()
            if not doi:
                continue
            extra = enriched.get(doi.lower(), {})
            collected.append(
                {
                    "theme": theme,
                    "section": section,
                    "purpose": purpose,
                    "title": (item.get("title") or [UNTITLED])[0].strip(),
                    "author": first_author(item),
                    "year": year_of(item),
                    "venue": (item.get("container-title") or [""])[0].strip(),
                    "doi": doi,
                    "citations": extra.get("citations", 0),
                    "abstract": extra.get("abstract", ""),
                    "oa_url": extra.get("oa_url", ""),
                }
            )

        # Most-cited first: a referee will expect the influential work to be engaged.
        collected.sort(key=lambda r: (-r["citations"], r["year"]))
        by_theme[theme] = collected
        rows.extend(collected)

    return rows, by_theme


def write_markdown(by_theme: dict[str, list[dict]], rows: list[dict]) -> None:
    with_abstract = sum(1 for r in rows if r["abstract"])
    lines = [
        "# Literature Reading List",
        "",
        f"**{len(rows)} candidate papers, {with_abstract} with a publisher abstract.**",
        "",
        "Generated by `python src/build_reading_list.py`. Grouped by the manuscript",
        "section each theme feeds, most-cited first within each group.",
        "",
        "---",
        "",
        "## Read this before using this list",
        "",
        "**I have not read these papers.** Nothing here is my summary or",
        "interpretation. Each abstract is quoted **verbatim** as the publisher",
        "deposited it, with the DOI, so you can verify it.",
        "",
        "An abstract is a claim by an author about their own work. It is not the",
        "work. For anything you cite as a finding:",
        "",
        "1. **Open the paper.** Abstracts routinely omit the limitations, the",
        "   sample, and the direction of an effect that does not flatter the",
        "   authors' framing.",
        "2. **Check the claim you are attaching it to.** A paper showing e-scooters",
        "   have *lower* severity in one city does not support a sentence saying",
        "   severity is high.",
        "3. **Do not cite a paper you have only read the abstract of**, and do not",
        "   let anyone else's summary stand in for the paper itself — including mine.",
        "",
        "A literature review that misrepresents three papers is worse than one that",
        "cites fifteen accurately.",
        "",
        "### A practical order of work",
        "",
        "1. Work theme by theme, in the order below. Each maps to one manuscript",
        "   section, so you finish a section's reading and can write it immediately.",
        "2. Start with **2.1** and **2.2**: they carry the most weight and set up your",
        "   three-way comparison.",
        "3. Read `docs/prior-work-scan.txt` and Zhao et al. (2026) early. Your novelty",
        "   claim depends on how you position against it.",
        "4. Track progress in `docs/reading-list.csv` (a `read` column is provided).",
        "5. Delete entries from `paper/references.bib` that you do not use. A tight 40",
        "   honest citations beats 99 loose ones.",
        "",
        "---",
        "",
        "## Contents",
        "",
    ]

    for theme, collected in by_theme.items():
        section, _ = THEME_TO_SECTION.get(theme, ("?", ""))
        lines.append(f"- **{section}** — {theme} ({len(collected)} papers)")

    for theme, collected in by_theme.items():
        section, purpose = THEME_TO_SECTION.get(theme, ("?", "Unmapped theme."))
        lines += [
            "",
            "---",
            "",
            f"## {section} — {theme}",
            "",
            f"*Why: {purpose}*",
            "",
        ]

        for index, paper in enumerate(collected, 1):
            venue = f" *{paper['venue']}*." if paper["venue"] else ""
            lines.append(
                f"### {section}.{index} {paper['title']}"
            )
            lines.append("")
            lines.append(
                f"**{paper['author']} ({paper['year']}).**{venue} "
                f"Cited {paper['citations']}x. "
                f"[doi.org/{paper['doi']}](https://doi.org/{paper['doi']})"
            )
            if paper["oa_url"]:
                lines.append(f" Open access: <{paper['oa_url']}>")
            lines.append("")
            if paper["abstract"]:
                quoted = paper["abstract"].replace("\n", " ").strip()
                lines.append("> *Publisher abstract, quoted verbatim:*")
                lines.append(">")
                for chunk in wrap(quoted, 100):
                    lines.append(f"> {chunk}")
            else:
                lines.append(
                    "> *No abstract available from OpenAlex. Open the DOI to read it.*"
                )
            lines.append("")

    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def wrap(text: str, width: int) -> list[str]:
    """Simple greedy wrap, to keep blockquotes readable in a text editor."""
    words, lines, current = text.split(), [], ""
    for word in words:
        if len(current) + len(word) + 1 > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines


def write_csv(rows: list[dict]) -> None:
    """A tracking sheet. The `read` column is blank for you to fill in."""
    fieldnames = [
        "section", "theme", "year", "author", "title", "venue",
        "citations", "has_abstract", "read", "notes", "doi",
    ]
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "section": row["section"],
                    "theme": row["theme"],
                    "year": row["year"],
                    "author": row["author"],
                    "title": row["title"],
                    "venue": row["venue"],
                    "citations": row["citations"],
                    "has_abstract": "yes" if row["abstract"] else "no",
                    "read": "",
                    "notes": "",
                    "doi": row["doi"],
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Ignore the cache and re-fetch")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use only the cache; never contact OpenAlex (useful when its shared budget is spent)",
    )
    args = parser.parse_args()

    theme_data = load_crossref()
    dois = list(
        dict.fromkeys(
            item["DOI"] for items in theme_data.values() for item in items if item.get("DOI")
        )
    )
    print(f"{len(theme_data)} theme(s), {len(dois)} unique DOI(s)")

    enriched = fetch_openalex(dois, args.refresh, offline=args.offline)
    print(f"OpenAlex data for {len(enriched)} of {len(dois)} DOI(s)")

    rows, by_theme = build(theme_data, enriched)
    write_markdown(by_theme, rows)
    write_csv(rows)

    with_abstract = sum(1 for r in rows if r["abstract"])
    unique_with_abstract = len({r["doi"] for r in rows if r["abstract"]})
    print(f"\nReading list written to {OUTPUT_MD}")
    print(f"Tracking sheet written to {OUTPUT_CSV}")
    print(
        f"  {len(rows)} entries across {len(dois)} unique papers; "
        f"{unique_with_abstract} unique papers have an abstract "
        f"({100 * unique_with_abstract / max(len(dois), 1):.0f}%)"
    )
    print("  (entries exceed papers because a paper can inform two sections)")
    print(f"  {len(dois) - unique_with_abstract} need the DOI opened manually")

    print("\n--- Papers per manuscript section ---")
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["section"]] = counts.get(row["section"], 0) + 1
    for section in sorted(counts):
        print(f"  {section:10s} {counts[section]:>3} paper(s)")

    print(
        "\nNext: open docs/reading-list.md and work through it theme by theme.\n"
        "Each theme maps to one manuscript section, so you can write as you read."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
