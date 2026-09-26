"""
Fetch and search the DfT STATS19 data guide.

WHY THIS EXISTS
---------------
The STATS19 open data is published as integer codes with no built-in labels. The
authoritative code definitions live in a separate XLSX "data guide" on GOV.UK.
Guessing code values (or asking an AI assistant to recall them) is how studies
end up analysing the wrong variable, so this script downloads the real guide and
searches it for you.

It answers the study's central design question: which code identifies a powered
personal transporter (e-scooter)?

Usage:
    python src/fetch_data_guide.py                    # download + search
    python src/fetch_data_guide.py --search "pedal"   # custom search term
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
GUIDE_DIR = DOCS_DIR / "data-guide"

GUIDE_URL = (
    "https://assets.publishing.service.gov.uk/media/"
    "6ab2a71d997a4b2950cced58/"
    "dft-road-casualty-statistics-road-safety-open-dataset-data-guide-2025.xlsx"
)
GUIDE_PATH = GUIDE_DIR / "dft-stats19-data-guide.xlsx"

# Search terms covering the naming variants DfT has used.
DEFAULT_TERMS = [
    "powered personal",
    "e-scooter",
    "escooter",
    "electric scooter",
    "scooter",
    "pedal cycle",
    "motorcycle",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (academic-research; reproducible-analysis)"}


def download_guide(force: bool = False) -> Path:
    GUIDE_DIR.mkdir(parents=True, exist_ok=True)
    if GUIDE_PATH.exists() and not force:
        print(f"Guide already present: {GUIDE_PATH}")
        return GUIDE_PATH

    print(f"Downloading data guide from:\n  {GUIDE_URL}\n")
    try:
        response = requests.get(GUIDE_URL, headers=HEADERS, timeout=120)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"FAILED to download the guide: {exc}", file=sys.stderr)
        print(
            "\nDownload it manually from the 'Guidance and documentation' section of:\n"
            "  https://www.gov.uk/government/statistical-data-sets/road-safety-open-data\n"
            f"and save it as:\n  {GUIDE_PATH}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    GUIDE_PATH.write_bytes(response.content)
    print(f"Saved {GUIDE_PATH.stat().st_size / 1e3:.0f} KB to {GUIDE_PATH}\n")
    return GUIDE_PATH


def load_sheets(path: Path) -> dict[str, pd.DataFrame]:
    """Load every sheet as a headerless string grid.

    The guide is formatted for humans, not machines: variable code tables are
    scattered across sheets with merged cells and blank separator rows. Reading
    everything as raw strings and searching the full grid is more reliable than
    trying to parse a schema that is not actually a schema.
    """
    sheets = pd.read_excel(path, sheet_name=None, header=None, dtype=str)
    print(f"Sheets found ({len(sheets)}): {', '.join(sheets)}\n")
    return sheets


def search_sheets(
    sheets: dict[str, pd.DataFrame], terms: list[str], context: int = 2
) -> dict[str, list[pd.DataFrame]]:
    """Find every cell containing a term, with surrounding rows for context.

    Written as a plain nested loop over the raw grid rather than a vectorised
    pandas expression. The guide is only ~85 KB across two sheets, so speed is
    irrelevant, and pandas 3.0's string dtype preserves NA through .str.lower(),
    which makes the vectorised version both fragile and harder to reason about.
    """
    hits: dict[str, list[pd.DataFrame]] = {term: [] for term in terms}

    for sheet_name, frame in sheets.items():
        values = frame.to_numpy(dtype=object)
        n_rows, n_cols = values.shape

        for row in range(n_rows):
            for col in range(n_cols):
                raw = values[row, col]
                if raw is None:
                    continue
                text = str(raw).strip().lower()
                if not text or text == "nan":
                    continue

                for term in terms:
                    if term not in text:
                        continue
                    window = frame.iloc[
                        max(0, row - context) : row + context + 1,
                        max(0, col - 3) : col + 8,
                    ].copy()
                    window["_sheet"] = sheet_name
                    window["_row"] = row
                    hits[term].append(window)

    return hits


def report(hits: dict[str, list[pd.DataFrame]], max_windows: int = 6) -> None:
    for term, windows in hits.items():
        print("=" * 78)
        print(f'SEARCH: "{term}"  ->  {len(windows)} matching cell(s)')
        print("=" * 78)
        if not windows:
            print("  (no matches)\n")
            continue
        for window in windows[:max_windows]:
            sheet = window["_sheet"].iloc[0]
            row = window["_row"].iloc[0]
            print(f"\n  sheet='{sheet}'  row={row}")
            display = window.drop(columns=["_sheet", "_row"]).fillna("")
            for _, record in display.iterrows():
                cells = [str(v).strip() for v in record if str(v).strip()]
                if cells:
                    print("    | " + " | ".join(cells))
        if len(windows) > max_windows:
            print(f"\n  ... and {len(windows) - max_windows} more match(es)")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search", nargs="+", default=None,
                        help="Custom search term(s) instead of the defaults")
    parser.add_argument("--force", action="store_true",
                        help="Re-download the guide even if it exists")
    args = parser.parse_args()

    terms = [t.lower() for t in (args.search or DEFAULT_TERMS)]

    path = download_guide(force=args.force)
    sheets = load_sheets(path)
    hits = search_sheets(sheets, terms)
    report(hits)

    print("=" * 78)
    print("NEXT STEP")
    print("=" * 78)
    print(
        "  From the output above, record the exact vehicle_type code for\n"
        "  'powered personal transporter / e-scooter' (and for pedal cycle and\n"
        "  motorcycle) in docs/data-notes.md.\n\n"
        "  Then fill in VEHICLE_CODES in src/analysis.py and the PPT constants in\n"
        "  src/prepare_data.py, and set PPT_UNKNOWN = False."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
