"""
Build a verified BibTeX bibliography from the Crossref REST API.

WHY THIS EXISTS
---------------
A literature review must cite real papers. Inventing plausible-looking references
is academic misconduct and would be far worse for an application than having no
publication at all.

This script queries Crossref - an authoritative DOI registry - for each theme the
paper needs, then writes only the metadata Crossref actually returns. Every entry
carries a real DOI that can be checked. Nothing here is written by hand, and
nothing is generated from memory.

It also searches specifically for papers that might ALREADY cover this study's
territory. Finding a scoop is a good outcome: it is far better to discover it now
than to claim novelty a reviewer can disprove.

Usage:
    python src/build_bibliography.py
    python src/build_bibliography.py --check-scoop
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAPER_DIR = PROJECT_ROOT / "paper"
BIB_PATH = PAPER_DIR / "references.bib"
SCAN_PATH = PROJECT_ROOT / "docs" / "prior-work-scan.txt"
RAW_PATH = PROJECT_ROOT / "docs" / "crossref-results.json"
SCAN_RAW_PATH = PROJECT_ROOT / "docs" / "prior-work-results.json"

API = "https://api.crossref.org/works"
HEADERS = {
    # Crossref asks for a contact address in the User-Agent for polite access.
    "User-Agent": "academic-literature-review/1.0 (mailto:researcher@example.org)",
}

# One entry per literature-review theme. These map onto paper/outline.md section 2.
SEARCHES: dict[str, dict] = {
    "escooter_epi": {
        "query.bibliographic": "electric scooter injury epidemiology emergency department",
        "rows": 12,
    },
    "escooter_severity": {
        "query.bibliographic": "e-scooter crash injury severity modelling",
        "rows": 12,
    },
    "micromobility_safety": {
        "query.bibliographic": "micromobility shared scooter road safety policy",
        "rows": 10,
    },
    "vru_severity": {
        "query.bibliographic": "vulnerable road user injury severity comparison cyclists motorcyclists",
        "rows": 12,
    },
    "severity_methods": {
        "query.bibliographic": "logistic regression killed seriously injured road casualty severity",
        "rows": 10,
    },
    "police_reported_bias": {
        "query.bibliographic": "under-reporting police road casualty data STATS19 validity",
        "rows": 10,
    },
    "speed_limit": {
        "query.bibliographic": "speed limit road environment injury severity outcome",
        "rows": 10,
    },
    "spatial_analysis": {
        "query.bibliographic": "spatial analysis road collision severity geographical",
        "rows": 8,
    },
    "cycling_severity": {
        "query.bibliographic": "bicycle cyclist injury severity determinants collision",
        "rows": 10,
    },
    "scooter_regulation": {
        "query.bibliographic": "electric scooter regulation law helmet rental scheme",
        "rows": 10,
    },
}

# Crossref keyword search is loose and returns unrelated work ("Lord chancellors of
# England", "EMPIAR dataset", motor-design papers). Each theme therefore declares
# the terms a candidate title must plausibly contain. This is a blunt instrument,
# but it removes obvious noise - and a human still has to read the survivors.
RELEVANCE_TERMS: dict[str, list[str]] = {
    "escooter_epi": ["scooter", "micromobility", "electric scooter"],
    "escooter_severity": ["scooter", "micromobility", "severity"],
    "micromobility_safety": ["micromob", "scooter", "shared", "micromobility"],
    "vru_severity": ["vulnerable", "cyclist", "motorcycl", "pedestrian", "severity"],
    "severity_methods": ["injury", "severity", "casualt", "crash", "collision"],
    "police_reported_bias": ["under-report", "underreport", "police", "casualt", "validity", "stats19"],
    "speed_limit": ["speed", "injury", "severity", "road"],
    "spatial_analysis": ["spatial", "geograph", "collision", "casualt", "crash"],
    "cycling_severity": ["cycl", "bicycle", "bike", "severity", "injury"],
    "scooter_regulation": ["scooter", "micromob", "regulat", "helmet", "law"],
    "GB e-scooter severity": ["scooter", "micromob", "casualt", "england", "britain", "road"],
    "e-scooter vs cyclist comparison": ["scooter", "cycl", "bicycle", "compar"],
    "e-scooter KSI trends": ["scooter", "casualt", "killed", "seriously injured", "trend"],
    "powered transporter casualties": ["scooter", "transporter", "casualt", "micromob"],
}


def is_relevant(item: dict, theme: str) -> bool:
    """True if the title plausibly belongs to the theme.

    Deliberately permissive: a false positive costs a few seconds of reading,
    while a false negative silently removes a real paper from the review.
    """
    terms = RELEVANCE_TERMS.get(theme)
    if not terms:
        return True
    title = clean_text((item.get("title") or [""])[0]).lower()
    return any(term in title for term in terms)


# Queries aimed at finding prior work that could pre-empt this study. Run with
# --check-scoop. Results go to a separate report file and never enter the
# bibliography, because a prior-work scan is a decision aid, not a citation list.
SCOOP_QUERIES: dict[str, str] = {
    "GB e-scooter severity": "England Great Britain e-scooter injury severity STATS19",
    "e-scooter vs cyclist comparison": "e-scooter versus bicycle casualty severity comparative",
    "e-scooter KSI trends": "e-scooter killed seriously injured trends national",
    "powered transporter casualties": "powered personal transporter casualty analysis",
}


def write_prior_work_report(results: dict[str, list[dict]]) -> Path:
    """Write the prior-work scan to a plain-text report."""
    lines = [
        "PRIOR-WORK SCAN",
        "=" * 74,
        "",
        "Papers that may already cover this study's territory. Read these BEFORE",
        "claiming novelty, and cite them. Generated by:",
        "    python src/build_bibliography.py --check-scoop",
        "",
    ]
    for name, items in results.items():
        lines.append("")
        lines.append(name)
        lines.append("-" * 74)
        for item in items:
            issued = (item.get("issued") or {}).get("date-parts") or [[None]]
            year = f" ({issued[0][0]})" if issued and issued[0] and issued[0][0] else ""
            title = console_safe(clean_text((item.get("title") or [""])[0]))
            venue = console_safe(clean_text((item.get("container-title") or [""])[0]))
            lines.append(f"  - {title}{year}")
            if venue:
                lines.append(f"      {venue}")
            lines.append(f"      https://doi.org/{item.get('DOI')}")
    SCAN_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return SCAN_PATH


def print_scan(results: dict[str, list[dict]]) -> None:
    """Print the scan to the console with ASCII-safe text."""
    print("\n" + "=" * 74)
    print("PRIOR-WORK SCAN - review by hand before claiming novelty")
    print("=" * 74)
    for name, items in results.items():
        print(f"\n{name}")
        for item in items[:6]:
            issued = (item.get("issued") or {}).get("date-parts") or [[None]]
            year = f" ({issued[0][0]})" if issued and issued[0] and issued[0][0] else ""
            title = console_safe(clean_text((item.get("title") or [""])[0]))
            print(f"  - {title[:96]}{year}")
            print(f"      https://doi.org/{item.get('DOI')}")
    print(
        "\nIf any of these covers GB e-scooter casualty severity, the novelty\n"
        "claim must be narrowed to what this study adds beyond it."
    )

SELECT = "DOI,title,author,issued,container-title,type,volume,issue,page,publisher,abstract,URL"


def fetch(params: dict, retries: int = 5) -> list[dict]:
    """Query Crossref, retrying on transient failures and rate limiting.

    Crossref throttles bursts. A 429 must be retried rather than treated as "no
    results", or a theme is silently dropped from the bibliography.
    """
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(API, params=params, headers=HEADERS, timeout=45)
            if response.status_code == 429:
                wait = min(2**attempt, 20)
                print(f"\n    rate limited, waiting {wait}s", end="", flush=True)
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()["message"]["items"]
        except requests.RequestException as exc:
            if attempt == retries:
                print(f"\n    FAILED after {retries} attempts: {exc}", file=sys.stderr)
                return []
            time.sleep(min(2**attempt, 20))
    print("\n    gave up after repeated rate limiting", file=sys.stderr)
    return []


def clean_text(value: str) -> str:
    """Strip JATS markup and collapse whitespace from Crossref abstracts."""
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def console_safe(value: str) -> str:
    """Make a string safe to print on a legacy Windows console.

    Crossref metadata is UTF-8 and contains typographic characters (non-breaking
    hyphens, en dashes, accented names). A cp1252 console raises
    UnicodeEncodeError on these, which would crash the scan partway through. The
    .bib file itself keeps the original characters; only the console is downgraded.
    """
    replacements = {
        "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-",
        "\u2014": "-", "\u2018": "'", "\u2019": "'", "\u201c": '"',
        "\u201d": '"', "\u2026": "...", "\u00a0": " ",
    }
    for original, substitute in replacements.items():
        value = value.replace(original, substitute)
    return value.encode("ascii", errors="replace").decode("ascii")


def author_to_bibtex(author: dict) -> str:
    family = (author.get("family") or "").strip()
    given = (author.get("given") or "").strip()
    if not family and not given:
        return ""
    if not given:
        return family
    return f"{family}, {given}"


def make_key(item: dict) -> str:
    """A stable citation key: first author surname + year + a title word."""
    authors = item.get("author") or []
    surname = ""
    if authors:
        surname = re.sub(r"[^A-Za-z]", "", (authors[0].get("family") or "anon"))
    year = "n.d."
    issued = (item.get("issued") or {}).get("date-parts") or [[None]]
    if issued and issued[0] and issued[0][0]:
        year = str(issued[0][0])
    title = (item.get("title") or [""])[0]
    word = ""
    for candidate in re.findall(r"[A-Za-z]{4,}", title):
        if candidate.lower() not in {"the", "and", "with", "from", "using", "study"}:
            word = candidate.lower()
            break
    return f"{surname.lower()}{year}{word}"


def to_bibtex(item: dict) -> tuple[str, str, bool]:
    """Return (key, bibtex_entry, has_doi)."""
    doi = (item.get("DOI") or "").strip()
    key = make_key(item)
    if not doi:
        return key, "", False

    title = clean_text((item.get("title") or [""])[0])
    journal = clean_text((item.get("container-title") or [""])[0])
    year = ""
    issued = (item.get("issued") or {}).get("date-parts") or [[None]]
    if issued and issued[0] and issued[0][0]:
        year = str(issued[0][0])

    authors = [author_to_bibtex(a) for a in (item.get("author") or [])]
    authors = [a for a in authors if a]
    author_field = " and ".join(authors[:20])

    # Prefer the DOI-resolvable URL for anything without a journal venue.
    entry_type = "article" if item.get("type") == "journal-article" else "misc"
    if item.get("type") == "proceedings-article":
        entry_type = "inproceedings"
    elif item.get("type") == "posted-content":
        entry_type = "misc"

    fields = [
        ("author", author_field),
        ("title", title),
        ("journal", journal if entry_type == "article" else ""),
        ("booktitle", journal if entry_type == "inproceedings" else ""),
        ("year", year),
        ("volume", str(item.get("volume") or "")),
        ("number", str(item.get("issue") or "")),
        ("pages", str(item.get("page") or "")),
        ("publisher", clean_text(str(item.get("publisher") or ""))),
        ("doi", doi),
        ("url", f"https://doi.org/{doi}"),
    ]
    body = ",\n".join(
        f"  {name} = {{{value}}}" for name, value in fields if value
    )
    entry = f"@{entry_type}{{{key},\n{body}\n}}"
    return key, entry, True


def run_search(name: str, params: dict) -> list[dict]:
    print(f"  {name:26s}", end="", flush=True)
    items = fetch({**params, "select": SELECT})
    kept = [item for item in items if is_relevant(item, name)]
    dropped = len(items) - len(kept)
    note = f" ({dropped} filtered as off-topic)" if dropped else ""
    print(f" -> {len(kept)} kept{note}")
    # Polite pacing: Crossref throttles bursts, and a throttled theme would be
    # dropped silently, leaving a hole in the literature review.
    time.sleep(1.5)
    return kept


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-scoop",
        action="store_true",
        help="Only run the searches for prior work that may pre-empt this study",
    )
    args = parser.parse_args()

    PAPER_DIR.mkdir(parents=True, exist_ok=True)
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)

    searches = SCOOP_QUERIES if args.check_scoop else SEARCHES
    label = "prior-work checks" if args.check_scoop else "literature themes"

    print(f"Querying Crossref for {len(searches)} {label}...\n")
    results: dict[str, list[dict]] = {}
    for name, params in searches.items():
        # SEARCHES holds full parameter dicts; SCOOP_QUERIES holds query strings.
        if isinstance(params, str):
            params = {"query.bibliographic": params, "rows": 10}
        results[name] = run_search(name, params)

    # The two runs must not share a JSON file. crossref-results.json is the
    # provenance record for references.bib, so overwriting it with scan results
    # would break the trail between the bibliography and its source metadata.
    raw_path = SCAN_RAW_PATH if args.check_scoop else RAW_PATH
    raw_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nRaw JSON written to {raw_path}")

    # A prior-work scan is a decision aid, not a citation list. Dumping its hits
    # into references.bib would pollute the bibliography with off-topic results
    # and destroy the curated theme search, so it writes a separate report.
    if args.check_scoop:
        report = write_prior_work_report(results)
        print(f"Prior-work report written to {report}")
        print_scan(results)
        return 0

    # De-duplicate across themes by DOI, keeping first-seen order.
    seen: dict[str, dict] = {}
    for items in results.values():
        for item in items:
            doi = (item.get("DOI") or "").strip().lower()
            if doi and doi not in seen:
                seen[doi] = item

    entries: dict[str, tuple[str, str]] = {}
    no_doi = 0
    for item in seen.values():
        key, entry, has_doi = to_bibtex(item)
        if not has_doi:
            no_doi += 1
            continue
        # Resolve collisions deterministically rather than overwriting.
        base_key, suffix = key, 1
        while key in entries:
            suffix += 1
            key = f"{base_key}{chr(ord('a') + suffix - 1)}"
        entries[key] = (key, entry)

    print(f"Unique records with a DOI: {len(entries)}")
    if no_doi:
        print(f"Skipped {no_doi} record(s) lacking a DOI (not citable enough to include).")

    missing = [name for name, items in results.items() if not items]
    if missing:
        print(
            "\n[WARN] These themes returned nothing and are NOT represented in the "
            f"bibliography: {', '.join(missing)}\n"
            "       Re-run to fill them in before writing the literature review.",
            file=sys.stderr,
        )

    header = (
        "% BibTeX bibliography generated from the Crossref REST API.\n"
        "%\n"
        "% Every entry below carries a real DOI returned by Crossref and can be\n"
        "% verified at https://doi.org/<doi>. Do NOT hand-edit entries to add claims\n"
        "% that Crossref did not return, and do not add a citation you have not read.\n"
        "%\n"
        "% Regenerate with: python src/build_bibliography.py\n"
        "% Check for prior work that may pre-empt this study:\n"
        "%   python src/build_bibliography.py --check-scoop\n"
        "%\n"
        "% BEFORE SUBMITTING: read each of these and remove any that do not actually\n"
        "% support the point you cite it for. Volume is not a virtue.\n\n"
    )
    BIB_PATH.write_text(
        header + "\n\n".join(entry for _, entry in entries.values()) + "\n",
        encoding="utf-8",
    )
    print(f"Bibliography written to {BIB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
