"""
Build the Zenodo deposit package and the metadata to paste into the web form.

WHY THIS EXISTS
---------------
Two things go wrong with manual Zenodo deposits: the archive accidentally contains
hundreds of megabytes of regenerable data, and the metadata is retyped by hand with
small inconsistencies. This script fixes both.

It produces, in outputs/deposit/:

  * a clean .zip of exactly the files worth archiving
  * a metadata sheet per record type, formatted field-by-field to paste into Zenodo
  * an integrity report (file count, size, and a SHA-256 of the archive itself)

Raw data and derived data are excluded by design: they are already published by the
Department for Transport and are regenerable from the included scripts. Excluding them
turns a ~380 MB deposit into a few megabytes.

Usage:
    python src/make_deposit.py
    python src/make_deposit.py --include-pdf paper/manuscript.pdf
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEPOSIT_DIR = PROJECT_ROOT / "outputs" / "deposit"

# Directories and files to include, relative to the project root. Anything not
# listed is omitted, so the deposit cannot silently grow to include data blobs.
INCLUDE_DIRS = ["src", "paper", "docs", "outputs/figures", "outputs/tables"]
INCLUDE_FILES = [
    "README.md",
    "plan.md",
    "progress.md",
    "requirements.txt",
    "requirements-lock.txt",
    "CITATION.cff",
    "LICENSE",
    "LICENSE-CC-BY-4.0.md",
]

# Never include these, wherever they appear.
EXCLUDE_NAMES = {".gitkeep", "crossref-results.json", "prior-work-results.json"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
EXCLUDE_DIR_PARTS = {"__pycache__", ".venv", ".git"}

ARCHIVE_NAME = "escooter-casualty-severity-gb-v1.0.0.zip"


def should_include(path: Path) -> bool:
    if any(part in EXCLUDE_DIR_PARTS for part in path.parts):
        return False
    if path.suffix in EXCLUDE_SUFFIXES:
        return False
    # The raw Crossref JSON is a working file, not a deposit artefact. The
    # bibliography it produced is included; the source metadata is large and
    # regenerable by the included script.
    if path.name in EXCLUDE_NAMES:
        return False
    return True


def collect(extra_files: list[Path]) -> list[Path]:
    """Return the full list of files to archive, sorted for reproducibility."""
    files: list[Path] = []

    for relative in INCLUDE_FILES:
        path = PROJECT_ROOT / relative
        if path.exists():
            files.append(path)

    for relative in INCLUDE_DIRS:
        directory = PROJECT_ROOT / relative
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_file() and should_include(path):
                files.append(path)

    for path in extra_files:
        if path.exists():
            files.append(path)
        else:
            print(f"  [warn] requested file not found, skipping: {path}")

    # De-duplicate while preserving order, then sort for a stable archive.
    unique = {path.resolve(): path for path in files}
    return sorted(unique.values(), key=lambda p: str(p.relative_to(PROJECT_ROOT)))


def build_archive(files: list[Path]) -> Path:
    DEPOSIT_DIR.mkdir(parents=True, exist_ok=True)
    archive = DEPOSIT_DIR / ARCHIVE_NAME
    if archive.exists():
        archive.unlink()

    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in files:
            arcname = Path("escooter-casualty-severity-gb") / path.relative_to(PROJECT_ROOT)
            bundle.write(path, arcname=str(arcname))

    return archive


def write_metadata_sheets() -> tuple[Path, Path]:
    """Write field-by-field metadata for the two Zenodo records.

    Zenodo's manual upload form is pasted into, not scripted, so the most useful
    deliverable is a plain sheet of exactly the values for each field, in the order
    the form presents them.
    """
    try:
        zenodo = json.loads((PROJECT_ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Could not read .zenodo.json: {exc}")

    creators = zenodo.get("creators", [{}])
    author = creators[0] if creators else {}
    related = zenodo.get("related_identifiers", [])
    github = next(
        (r["identifier"] for r in related if "github" in str(r.get("identifier", "")).lower()),
        "[your repository URL]",
    )

    header = (
        "ZENODO MANUAL UPLOAD - METADATA TO PASTE\n"
        + "=" * 74
        + "\n\nPaste each value into the matching field in the Zenodo upload form.\n"
        "Fill any remaining [bracket] before publishing.\n\n"
    )

    preprint_sheet = header + (
        "RECORD 1: THE PREPRINT\n"
        + "-" * 74
        + f"""
Field                    Value
--------------------------------------------------------------------------------
Resource type            Publication  ->  Preprint
Title                    {zenodo.get('title', '')}

Creators                 {author.get('name', '')}
                         ORCID: {author.get('orcid', '')}
                         Affiliation: {author.get('affiliation', '')}

Description              Copy the Abstract from paper/manuscript.md verbatim.
                         Paste as HTML: use <p> for paragraphs and <strong> for bold.

Keywords                 {', '.join(zenodo.get('keywords', []))}
Language                 English
Licence                  CC-BY-4.0
Access                   Open
DOI                      Leave blank - Zenodo mints it
Publication date         Today's date
Version                  v1.0.0

Related identifiers
  isSupplementedBy       {github}          (resource type: Software)
  isDerivedFrom          https://www.gov.uk/government/statistical-data-sets/road-safety-open-data    (dataset)

Notes                    {zenodo.get('notes', '')}

FILES TO UPLOAD
  - the manuscript PDF
  - optionally {ARCHIVE_NAME}

WARNING: a published Zenodo record cannot be deleted. Proofread the title, your
name, and the ORCID before clicking publish.
"""
    )

    software_sheet = header + (
        "RECORD 2: THE SOFTWARE / CODE\n"
        + "-" * 74
        + f"""
Field                    Value
--------------------------------------------------------------------------------
Resource type            Software
Title                    Analysis code: {zenodo.get('title', '')}

Creators                 {author.get('name', '')}
                         ORCID: {author.get('orcid', '')}
                         Affiliation: {author.get('affiliation', '')}

Description              Paste as HTML:
                         <p>Reproducible analysis pipeline for a comparative study
                         of e-scooter casualty severity in Great Britain using UK
                         STATS19 road safety open data. The pipeline fetches the
                         raw data, verifies the category codes against the
                         published data guide, and reproduces the derived analysis
                         dataset byte-identically (SHA-256
                         eb95fc2d5f27960a1a61ad7e64fe4125f73b08c069b677d48895acc1fe691634).</p>
                         <p>Raw STATS19 data is not redistributed; it is retrieved
                         by the included script from the Department for Transport
                         under the Open Government Licence v3.0.</p>

Keywords                 {', '.join(zenodo.get('keywords', []))}
Language                 English
Licence                  MIT
Access                   Open
Version                  v1.0.0
Programming language     Python

Related identifiers
  isSourceOf             {github}          (resource type: Software)
  isDerivedFrom          https://www.gov.uk/government/statistical-data-sets/road-safety-open-data    (dataset)

FILES TO UPLOAD
  - {ARCHIVE_NAME}

This record is complete and ready tonight. The preprint record needs the literature
review finished first.
"""
    )

    DEPOSIT_DIR.mkdir(parents=True, exist_ok=True)
    preprint_path = DEPOSIT_DIR / "zenodo-metadata-PREPRINT.txt"
    software_path = DEPOSIT_DIR / "zenodo-metadata-SOFTWARE.txt"
    preprint_path.write_text(preprint_sheet, encoding="utf-8")
    software_path.write_text(software_sheet, encoding="utf-8")
    return preprint_path, software_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-pdf",
        action="append",
        default=[],
        help="Extra file(s) to include, e.g. --include-pdf paper/manuscript.pdf",
    )
    args = parser.parse_args()

    extra = [Path(p) if Path(p).is_absolute() else PROJECT_ROOT / p for p in args.include_pdf]

    print("Collecting deposit files...")
    files = collect(extra)
    print(f"  {len(files)} file(s) selected")

    total_bytes = sum(f.stat().st_size for f in files)
    print(f"  {total_bytes / 1e6:.2f} MB uncompressed")

    archive = build_archive(files)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    print(f"\nArchive: {archive}")
    print(f"  size  : {archive.stat().st_size / 1e6:.2f} MB")
    print(f"  files : {len(files)}")
    print(f"  SHA256: {digest}")

    preprint_sheet, software_sheet = write_metadata_sheets()

    print("\nMetadata sheets written:")
    print(f"  {preprint_sheet.relative_to(PROJECT_ROOT)}")
    print(f"  {software_sheet.relative_to(PROJECT_ROOT)}")

    print("\n--- Contents by top-level folder ---")
    counts: dict[str, int] = {}
    for path in files:
        top = path.relative_to(PROJECT_ROOT).parts[0] if len(path.relative_to(PROJECT_ROOT).parts) > 1 else "(root)"
        counts[top] = counts.get(top, 0) + 1
    for name, count in sorted(counts.items()):
        print(f"  {name:20s} {count:>3} file(s)")

    print(
        "\nNext: open outputs/deposit/zenodo-metadata-SOFTWARE.txt and follow it.\n"
        "The software record needs no further work and can be deposited today."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
