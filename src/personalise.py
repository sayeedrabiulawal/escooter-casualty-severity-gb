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
    python src/personalise.py --given "Rabiul Awal" --family "Sayeed" \
        --affiliation "Department of Civil Engineering, Example University" \
        --orcid 0000-0002-1234-5678 --github https://github.com/me/repo
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

# Files whose remaining placeholder mentions are documentation rather than live
# metadata, and so must not be reported as outstanding work.
DOCUMENTATION_ONLY = {"docs/zenodo-release-checklist.md"}

# Placeholder forms found in this repository. Kept as explicit alternatives rather
# than a loose pattern, so ordinary bracketed prose is never rewritten by accident.
PLACEHOLDER_PATTERNS = [
    r"\[Full name\]",
    r"\[Family name\]",
    r"\[Given names\]",
    r"\[Affiliation\]",
    r"\[ORCID\]",
    r"\[username\]/\[repo\]",
    r"\[GitHub URL\]",
    r"0000-0000-0000-0000",
]


# Patterns used to DETECT remaining placeholders. Kept separate from the
# substitution list so reporting works even when no replacement values are given,
# and so an unreplaced placeholder can still be found afterwards.
#
# The legacy forms are listed too: this repository previously encoded the author as
# "Sayed [surname]", which wrongly treated Sayeed as a given name. Both spellings are
# checked so a stale placeholder cannot survive unnoticed.
DETECT_PATTERNS = [
    (r"\[Full name\]", "author name"),
    (r"Sayed \[surname[^\]]*\]", "author name (legacy form)"),
    (r"\[Family name\]", "family name"),
    (r"\[Surname\]", "family name (legacy form)"),
    (r"\[Given names\]", "given names"),
    (r"\[Affiliation\]", "affiliation"),
    (r"\[Your University\]", "affiliation (legacy form)"),
    (r"\[ORCID\]", "orcid"),
    (r"\[add before release\]", "orcid/affiliation (legacy form)"),
    (r"\[username\]/\[repo\]", "repository url"),
    (r"\[GitHub URL\]", "repository url"),
    (r"0000-0000-0000-0000", "orcid"),
    (r"\[TODO[^\]]*\]", "TODO"),
]


def build_replacements(
    given: str, family: str, orcid: str, affiliation: str, github: str
) -> list[tuple[str, str, str]]:
    """Return (pattern, replacement, label) triples in priority order.

    Given names and family name are substituted separately because the two are
    ordered and labelled differently in each format: "Sayeed, Rabiul Awal" in
    Zenodo, family-names/given-names in CFF, "Rabiul Awal Sayeed" in prose.

    Order matters: the full GitHub URL must be substituted before the bare
    `[username]/[repo]` fragments, or the fragments are consumed first and a
    malformed URL is left behind.
    """
    full = f"{given} {family}".strip()
    replacements: list[tuple[str, str, str]] = []

    if github:
        replacements.append(
            (r"https://github\.com/\[username\]/\[repo\]", github, "github url")
        )
        replacements.append((r"\[username\]/\[repo\]", github, "github url"))
        replacements.append((r"\[GitHub URL\]", github, "github url"))
    if family:
        replacements.append((r"\[Family name\]", family, "family name"))
        replacements.append((r"\[Surname\]", family, "family name"))
    if given:
        replacements.append((r"\[Given names\]", given, "given names"))
    if full:
        # Author lines previously rendered as "Sayed `[surname]`", so the backticks
        # must be consumed together with the placeholder. Replacing only the
        # bracketed part would leave the surrounding ticks behind.
        replacements.append((r"`\[surname[^\]]*\]`", full, "author name"))
        replacements.append((r"Sayed \[surname[^\]]*\]", full, "author name"))
        replacements.append((r"\[Full name\]", full, "author name"))
    if orcid:
        cleaned = orcid.replace("https://orcid.org/", "").strip()
        replacements.append((r"\[ORCID\]", cleaned, "orcid"))
        replacements.append((r"0000-0000-0000-0000", cleaned, "orcid"))
    if affiliation:
        replacements.append((r"\[Affiliation\]", affiliation, "affiliation"))
        replacements.append((r"\[Your University\]", affiliation, "affiliation"))

    return replacements


def analyse() -> dict[str, list[tuple[str, int]]]:
    """Count remaining placeholders per file without changing anything.

    Documentation files are skipped. The release checklist has to *show* the
    placeholder syntax in order to explain it, so reporting those mentions would
    send the reader hunting for a placeholder that does not exist. A miss here
    cannot hide a broken record, because verify_zenodo_json() checks the real
    metadata strictly.
    """
    report: dict[str, list[tuple[str, int]]] = {}
    for relative in TARGETS:
        if relative in DOCUMENTATION_ONLY:
            continue
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

# CITATION.cff ships with a commented-out ORCID line. Left in place it would still
# assert an ORCID is expected, which is not true and would mislead a reader of the
# archived record.
ABSENT_OPTIONAL_METADATA_RULES: list[tuple[str, str, str]] = [
    ("CITATION.cff", r"^\s*# orcid: [^\n]*\n", ""),
]


def _creator_name(given: str, family: str) -> str:
    """Zenodo wants "Family, Given"; the comma is dropped if a part is missing."""
    return f"{family}, {given}".strip().strip(",").strip()


def update_zenodo_json(
    given: str, family: str, orcid: str, affiliation: str, github: str, dry_run: bool
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

    if family or given:
        creator["name"] = _creator_name(given, family)
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
            json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    return notes


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
        for placeholder in (
            "0000-0000-0000",
            "[Full name]",
            "[Family name]",
            "[Given names]",
            "[Affiliation]",
            "[Surname]",
            "[Your University]",
            "[username]",
            "[TODO",
        )
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
            "Both --given and --family are required for a complete author name. "
            f"Affiliation defaults to '{DEFAULT_AFFILIATION}'. ORCID and --github are "
            "optional, and their placeholders are removed cleanly if not supplied."
        ),
    )
    parser.add_argument("--given", default="", help="Given names, e.g. 'Rabiul Awal'")
    parser.add_argument("--family", default="", help="Family name, e.g. 'Sayeed'")
    parser.add_argument("--orcid", default="", help="ORCID iD, e.g. 0000-0002-1234-5678 (optional)")
    parser.add_argument("--affiliation", default="", help="Institution and department (optional)")
    parser.add_argument("--github", default="", help="Public repository URL (optional)")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    if not any([args.given, args.family, args.orcid, args.affiliation, args.github]):
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
            "\nMinimum needed: --given and --family. Everything else is optional:\n"
            "  ORCID        free at https://orcid.org (about 2 minutes, recommended)\n"
            "  affiliation  defaults to 'Independent Researcher' if omitted\n"
            "  github       omit if the code is not public yet; the deposit still holds it"
        )
        return 0

    if not (args.given and args.family):
        print(
            "[warn] --given and --family are both needed, otherwise the author name\n"
            "       keeps a placeholder. An author placeholder in a permanent record\n"
            "       looks broken, so supply both.",
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
    print(f"  author : {args.given} {args.family}".rstrip())
    print(f"  affil  : {args.affiliation or DEFAULT_AFFILIATION}")

    # 1. Structured edit of the Zenodo metadata, via the json module.
    notes = update_zenodo_json(
        args.given, args.family, cleaned_orcid, args.affiliation, args.github, args.dry_run
    )
    print("\n  .zenodo.json handled with the json module (cannot become invalid)")
    for note in notes:
        print(f"    - {note}")

    # 2. Substitute any supplied values across the text files.
    patterns = build_replacements(
        args.given, args.family, cleaned_orcid, args.affiliation, args.github
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
