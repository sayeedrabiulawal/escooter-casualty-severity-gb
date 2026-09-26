"""
Fill your personal details into every file that needs them.

WHY THIS EXISTS
---------------
Zenodo metadata is permanent. Getting a name wrong, or forgetting an ORCID, means
either publishing something you cannot correct or publishing a second version with a
different DOI. This script sets every placeholder from one source of truth so the
name, ORCID, and affiliation cannot drift apart between files.

It edits in place and prints a diff summary. Run with --dry-run first.

Usage:
    python src/personalise.py --dry-run
    python src/personalise.py --surname Khan --orcid 0000-0002-1234-5678 \
        --affiliation "University of Example" --github https://github.com/me/repo
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Files containing placeholders, with the substitutions each needs.
TARGETS = [
    "CITATION.cff",
    "LICENSE",
    ".zenodo.json",
    "README.md",
    "plan.md",
    "progress.md",
    "paper/manuscript.md",
    "docs/zenodo-release-checklist.md",
]

# Placeholder forms found in this repository. Kept as explicit alternatives rather
# than a loose pattern, so ordinary bracketed prose is never rewritten by accident.
PLACEHOLDER_PATTERNS = [
    r"\[surname[^\]]*\]",
    r"\[Surname\]",
    r"\[Your University\]",
    r"\[username\]/\[repo\]",
    r"\[GitHub URL\]",
    r"\[add before release\]",
    r"0000-0000-0000-0000",
]


# Patterns used to DETECT remaining placeholders. Kept separate from the
# substitution list so reporting works even when no replacement values are given,
# and so an unreplaced placeholder can still be found afterwards.
DETECT_PATTERNS = [
    (r"\[Surname\]", "surname"),
    (r"Sayed \[surname[^\]]*\]", "author name"),
    (r"\[Your University\]", "affiliation"),
    (r"\[username\]/\[repo\]", "github url"),
    (r"\[GitHub URL\]", "github url"),
    (r"\[add before release\]", "orcid"),
    (r"0000-0000-0000-0000", "orcid"),
    (r"\[TODO[^\]]*\]", "TODO"),
]


def build_replacements(
    surname: str, orcid: str, affiliation: str, github: str
) -> list[tuple[str, str, str]]:
    """Return (pattern, replacement, label) triples in priority order.

    Order matters: the full GitHub URL must be substituted before the bare
    `[username]/[repo]` fragments, or the fragments are consumed first and a
    malformed URL is left behind.
    """
    surname_full = surname
    replacements: list[tuple[str, str, str]] = []

    if github:
        replacements.append(
            (r"https://github\.com/\[username\]/\[repo\]", github, "github url")
        )
        replacements.append((r"\[username\]/\[repo\]", github, "github url"))
        replacements.append((r"\[GitHub URL\]", github, "github url"))
    if surname:
        replacements.append((r"\[Surname\]", surname_full, "surname"))
        replacements.append((r"Sayed \[surname[^\]]*\]", f"Sayed {surname_full}", "author name"))
        replacements.append((r"\[surname[^\]]*\]", surname_full, "surname"))
    if orcid:
        cleaned = orcid.replace("https://orcid.org/", "").strip()
        replacements.append((r"0000-0000-0000-0000", cleaned, "orcid"))
        replacements.append((r"\[add before release\]", cleaned, "orcid"))
    if affiliation:
        replacements.append((r"\[Your University\]", affiliation, "affiliation"))

    return replacements


def analyse() -> dict[str, list[tuple[str, int]]]:
    """Count remaining placeholders per file without changing anything."""
    report: dict[str, list[tuple[str, int]]] = {}
    for relative in TARGETS:
        path = PROJECT_ROOT / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        found: list[tuple[str, int]] = []
        seen: set[str] = set()
        for pattern, label in DETECT_PATTERNS:
            if label in seen:
                continue
            count = len(re.findall(pattern, text))
            if count:
                found.append((label, count))
                seen.add(label)
        if found:
            report[relative] = found
    return report


def apply_all(patterns: list[tuple[str, str, str]], dry_run: bool) -> dict[str, int]:
    """Apply substitutions. Returns substitution counts per file."""
    counts: dict[str, int] = {}
    for relative in TARGETS:
        path = PROJECT_ROOT / relative
        if not path.exists():
            continue
        original = path.read_text(encoding="utf-8")
        text = original
        for pattern, replacement, _ in patterns:
            text = re.sub(pattern, replacement, text)
        if text != original:
            counts[relative] = sum(
                len(re.findall(pattern, original)) for pattern, _, _ in patterns
            )
            if not dry_run:
                path.write_text(text, encoding="utf-8")
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--surname", default="", help="Your family name, e.g. Khan")
    parser.add_argument("--orcid", default="", help="ORCID iD, e.g. 0000-0002-1234-5678")
    parser.add_argument("--affiliation", default="", help="Institution, e.g. University of Example")
    parser.add_argument("--github", default="", help="Repository URL")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    if not any([args.surname, args.orcid, args.affiliation, args.github]):
        print("No details supplied, so nothing can be changed. Showing current state.\n")
        report = analyse()
        if not report:
            print("No placeholders found. Nothing to do.")
            return 0
        print("Placeholders still present:")
        for relative, found in report.items():
            print(f"\n  {relative}")
            for label, count in found:
                print(f"    {count:>2} x {label}")
        print(
            "\nSupply --surname, --orcid, --affiliation and --github to fill these.\n"
            "ORCID: get one free at https://orcid.org (takes about two minutes)."
        )
        return 0

    if args.orcid and not re.fullmatch(r"\d{4}-\d{4}-\d{4}-[\dX]{4}", args.orcid.replace("https://orcid.org/", "")):
        print(
            f"[warn] '{args.orcid}' does not look like an ORCID iD "
            "(expected 0000-0000-0000-0000). Publishing a malformed ORCID to Zenodo "
            "is permanent, so check it before continuing.",
            file=sys.stderr,
        )
    if args.github and not args.github.startswith("http"):
        print(f"[warn] --github '{args.github}' does not look like a URL.", file=sys.stderr)

    patterns = build_replacements(args.surname, args.orcid, args.affiliation, args.github)

    if args.dry_run:
        print("DRY RUN - nothing will be written.\n")
        counts = apply_all(patterns, dry_run=True)
        for relative, count in counts.items():
            print(f"  would change {relative} ({count} substitution(s))")
        print(f"\n{len(counts)} file(s) would change. Re-run without --dry-run to apply.")
        return 0

    counts = apply_all(patterns, dry_run=False)
    print("Applied:")
    for relative, count in counts.items():
        print(f"  {relative} ({count} substitution(s))")

    print("\n--- Remaining placeholders ---")
    report = analyse()
    if not report:
        print("  None. Metadata is fully personalised.")
        return 0
    for relative, found in report.items():
        print(f"\n  {relative}")
        for label, count in found:
            print(f"    {count:>2} x {label}")
    print(
        "\nReview the above before publishing. Anything listed as 'unresolved' is a\n"
        "TODO you must fill in by hand."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
