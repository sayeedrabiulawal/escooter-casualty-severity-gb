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
import json
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
        # The author line renders as "Sayed `[surname]`", so the backticks must be
        # consumed together with the placeholder. Replacing only the bracketed part
        # leaves `Khan` visible in the output.
        replacements.append((r"`\[surname[^\]]*\]`", surname_full, "surname"))
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


# ---------------------------------------------------------------------------
# Absent-value handling
#
# None of ORCID, affiliation, or a public repository is required to deposit on
# Zenodo. What IS unacceptable is leaving a placeholder in the metadata, because the
# record is permanent and "0000-0000-0000-0000" looks broken. A missing value must
# therefore be REMOVED cleanly, not ignored.
# ---------------------------------------------------------------------------

DEFAULT_AFFILIATION = "Independent Researcher"

ABSENT_ORCID_RULES: list[tuple[str, str, str]] = [
    ("paper/manuscript.md", r"\*\*ORCID:\*\*[^\n]*\n", ""),
]

ABSENT_AFFILIATION_RULES: list[tuple[str, str, str]] = [
    ("paper/manuscript.md", r"\*\*Affiliation:\*\*[^\n]*\n", ""),
]

ABSENT_GITHUB_RULES: list[tuple[str, str, str]] = [
    (
        "paper/manuscript.md",
        # Replace only the placeholder fragment, not the whole sentence, or the
        # result repeats the word "pipeline" twice in a row.
        r"`\[GitHub URL\]`, tag `v1\.0\.0`",
        "Included in the archived deposit, tag `v1.0.0`",
    ),
    ("CITATION.cff", r"^repository-code: [^\n]*\n", ""),
    ("CITATION.cff", r"^url: [^\n]*\n", ""),
    ("README.md", r"\[username\]/\[repo\]", "the archived deposit"),
    ("plan.md", r"\[username\]/\[repo\]", "the archived deposit"),
    ("progress.md", r"\[username\]/\[repo\]", "the archived deposit"),
]

# CITATION.cff ships with a commented-out ORCID/affiliation block. Left in place it
# would still assert these are required, which is not true and would mislead a reader
# of the archived record.
ABSENT_OPTIONAL_METADATA_RULES: list[tuple[str, str, str]] = [
    (
        "CITATION.cff",
        r"^\s*# TODO: uncomment and complete before releasing[^\n]*\n(?:\s*#[^\n]*\n)*",
        "",
    ),
]


def apply_rules(rules: list[tuple[str, str, str]], dry_run: bool) -> int:
    """Apply (file, pattern, replacement) rules. Returns the number of edits made."""
    edits = 0
    for relative, pattern, replacement in rules:
        path = PROJECT_ROOT / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        new_text, count = re.subn(pattern, replacement, text, flags=re.M)
        if count:
            edits += count
            if not dry_run:
                path.write_text(new_text, encoding="utf-8")
    return edits


def update_zenodo_json(
    surname: str, orcid: str, affiliation: str, github: str, dry_run: bool
) -> list[str]:
    """Edit .zenodo.json with the json module so the file cannot become invalid.

    Regex surgery on JSON risks a trailing comma that breaks the deposit, and Zenodo
    rejects the entire upload if the metadata will not parse. Parsing, modifying, and
    re-serialising is the only safe way to do this.
    """
    path = PROJECT_ROOT / ".zenodo.json"
    if not path.exists():
        return ["[warn] .zenodo.json not found"]

    notes: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"[warn] .zenodo.json is not valid JSON, left unchanged: {exc}"]

    creators = data.get("creators") or [{}]
    creator = creators[0]

    if surname:
        creator["name"] = f"{surname}, Sayed"
    creator["affiliation"] = affiliation or DEFAULT_AFFILIATION
    if not affiliation:
        notes.append(f"affiliation defaulted to '{DEFAULT_AFFILIATION}'")

    if orcid:
        creator["orcid"] = orcid.replace("https://orcid.org/", "").strip()
    else:
        # Dropping the key is correct: Zenodo accepts creators without an ORCID.
        creator.pop("orcid", None)
        notes.append("no ORCID supplied, so the orcid field was removed")

    data["creators"] = creators

    related = data.get("related_identifiers") or []
    if github:
        for entry in related:
            if "github" in str(entry.get("identifier", "")).lower():
                entry["identifier"] = github
    else:
        # Remove only the placeholder repository link, keeping the dataset link.
        kept = [
            entry
            for entry in related
            if "github" not in str(entry.get("identifier", "")).lower()
        ]
        if len(kept) != len(related):
            notes.append("no repository URL supplied, so the GitHub link was removed")
        data["related_identifiers"] = kept

    if not dry_run:
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    return notes


def verify_zenodo_json() -> bool:
    """Confirm .zenodo.json parses and has no leftover placeholders."""
    path = PROJECT_ROOT / ".zenodo.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  [FAIL] .zenodo.json does not parse: {exc}")
        return False

    blob = json.dumps(data)
    problems = [
        placeholder
        for placeholder in ("0000-0000-0000", "[Surname]", "[Your University]", "[username]", "[TODO")
        if placeholder in blob
    ]
    if problems:
        print(f"  [FAIL] .zenodo.json still contains: {', '.join(problems)}")
        return False

    print("  [ OK ] .zenodo.json parses and contains no placeholders")
    return True


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
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Only --surname is required. Affiliation defaults to "
            f"'{DEFAULT_AFFILIATION}'. ORCID and --github are optional, and their "
            "placeholders are removed cleanly if not supplied."
        ),
    )
    parser.add_argument("--surname", default="", help="Your family name (the one value worth supplying)")
    parser.add_argument("--orcid", default="", help="ORCID iD, e.g. 0000-0002-1234-5678 (optional)")
    parser.add_argument("--affiliation", default="", help="Institution (optional)")
    parser.add_argument("--github", default="", help="Public repository URL (optional)")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    if not any([args.surname, args.orcid, args.affiliation, args.github]):
        print("No details supplied. Showing what is still missing.\n")
        report = analyse()
        if not report:
            print("No placeholders found. Nothing to do.")
            return 0
        for relative, found in report.items():
            print(f"  {relative}")
            for label, count in found:
                print(f"    {count:>2} x {label}")
        print(
            "\nMinimum needed: --surname. Everything else is optional:\n"
            "  ORCID        free at https://orcid.org (about 2 minutes, recommended)\n"
            "  affiliation  defaults to 'Independent Researcher' if omitted\n"
            "  github       omit if the code is not public yet; the deposit still holds it"
        )
        return 0

    if not args.surname:
        print(
            "[warn] --surname not supplied, so the author name keeps its placeholder.\n"
            "       An author placeholder in a permanent record looks broken, so\n"
            "       supply at least this one value.",
            file=sys.stderr,
        )

    cleaned_orcid = args.orcid.replace("https://orcid.org/", "").strip()
    if cleaned_orcid and not re.fullmatch(r"\d{4}-\d{4}-\d{4}-[\dX]{4}", cleaned_orcid):
        print(
            f"[warn] '{args.orcid}' does not look like an ORCID iD "
            "(expected 0000-0000-0000-0000). Publishing a malformed ORCID is\n"
            "       permanent, so verify it before continuing.",
            file=sys.stderr,
        )
    if args.github and not args.github.startswith("http"):
        print(f"[warn] --github '{args.github}' does not look like a URL.", file=sys.stderr)

    suffix = " (DRY RUN - nothing written)" if args.dry_run else ""
    print(f"Personalising metadata{suffix}\n")

    # 1. Structured edit of the Zenodo metadata, via the json module.
    notes = update_zenodo_json(
        args.surname, cleaned_orcid, args.affiliation, args.github, args.dry_run
    )
    print("  .zenodo.json handled with the json module (cannot become invalid)")
    for note in notes:
        print(f"    - {note}")

    # 2. Substitute any supplied values across the text files.
    patterns = build_replacements(
        args.surname, cleaned_orcid, args.affiliation, args.github
    )
    counts = apply_all(patterns, dry_run=args.dry_run)
    for relative, count in counts.items():
        print(f"    {relative} ({count} substitution(s))")

    # 3. Remove placeholders for values that were NOT supplied. Leaving them would
    #    put a broken-looking field into a record that cannot be deleted.
    removal_edits = 0
    if not cleaned_orcid:
        removal_edits += apply_rules(ABSENT_ORCID_RULES, args.dry_run)
    if not args.affiliation:
        removal_edits += apply_rules(ABSENT_AFFILIATION_RULES, args.dry_run)
    if not args.github:
        removal_edits += apply_rules(ABSENT_GITHUB_RULES, args.dry_run)
    if not (cleaned_orcid and args.affiliation):
        removal_edits += apply_rules(ABSENT_OPTIONAL_METADATA_RULES, args.dry_run)
    print(f"    {removal_edits} placeholder(s) removed for unsupplied values")

    print("\n--- Verification ---")
    if args.dry_run:
        print("  (skipped in dry run)")
    else:
        verify_zenodo_json()

    report = analyse()
    if not report:
        print("  [ OK ] No placeholders remain in any file.")
        if args.dry_run:
            print("\nDry run complete. Re-run without --dry-run to apply.")
        else:
            print("\nMetadata is fully personalised. Next:")
            print("  python src/make_deposit.py --include-pdf paper/manuscript.pdf")
        return 0

    print("\n  Remaining:")
    for relative, found in report.items():
        print(f"\n    {relative}")
        for label, count in found:
            marker = "  <-- must fix before publishing" if label == "TODO" else ""
            print(f"      {count:>2} x {label}{marker}")
    if args.dry_run:
        print("\nDry run complete. Re-run without --dry-run to apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
