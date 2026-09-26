"""
Download UK STATS19 road safety open data from the Department for Transport.

Raw data is deliberately NOT committed to this repository: it is ~250 MB and is
already archived by DfT. This script re-creates it on demand, so the analysis is
reproducible without bloating the repo.

Licence: Open Government Licence v3.0, (c) Crown copyright.
Source:  https://www.gov.uk/government/statistical-data-sets/road-safety-open-data

Usage:
    python src/download_data.py
    python src/download_data.py --years 2021 2022 2023 2024 2025
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://data.dft.gov.uk/road-accidents-safety-data"

# The "last 5 years" bundle is the right size for this study. The complete
# 1979-present set contains a 1.5 GB collision file we do not need.
BUNDLES = {
    "collision": "dft-road-casualty-statistics-collision-last-5-years.csv",
    "vehicle": "dft-road-casualty-statistics-vehicle-last-5-years.csv",
    "casualty": "dft-road-casualty-statistics-casualty-last-5-years.csv",
}

# Per-year files, used when --years is given explicitly.
YEAR_TEMPLATE = "dft-road-casualty-statistics-{table}-{year}.csv"

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

HEADERS = {
    # DfT serves these fine to a normal browser UA; some proxies block bare requests.
    "User-Agent": "Mozilla/5.0 (academic-research; reproducible-analysis)",
}

CHUNK_SIZE = 1024 * 1024  # 1 MiB


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def sha256_of(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def existing_hash_matches(path: Path, expected: str | None) -> bool:
    """True if the file exists and, when an expected hash is given, matches it."""
    if not path.exists():
        return False
    if expected is None:
        return True
    return sha256_of(path) == expected


def download(url: str, destination: Path, *, force: bool = False) -> Path:
    """Stream a file to disk. Skips the download if it already exists."""
    if destination.exists() and not force:
        size_mb = destination.stat().st_size / 1e6
        print(f"  skip   {destination.name} (already present, {size_mb:.1f} MB)")
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_suffix(destination.suffix + ".part")

    print(f"  fetch  {destination.name}")
    try:
        with requests.get(url, headers=HEADERS, stream=True, timeout=120) as response:
            response.raise_for_status()
            total = int(response.headers.get("Content-Length", 0))
            written = 0

            with temp_path.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if not chunk:
                        continue
                    handle.write(chunk)
                    written += len(chunk)
                    if total:
                        pct = 100 * written / total
                        print(
                            f"\r         {written / 1e6:7.1f} / {total / 1e6:.1f} MB "
                            f"({pct:5.1f}%)",
                            end="",
                            flush=True,
                        )
            if total:
                print()
    except requests.RequestException as exc:
        temp_path.unlink(missing_ok=True)
        print(f"\n  FAILED {url}\n         {exc}", file=sys.stderr)
        raise

    temp_path.replace(destination)
    size_mb = destination.stat().st_size / 1e6
    print(f"         done, {size_mb:.1f} MB")
    return destination


def write_checksums(paths: list[Path]) -> Path:
    """Write a SHA-256 manifest so the exact data snapshot is auditable."""
    manifest = RAW_DIR / "checksums.sha256"
    lines = []
    for path in sorted(paths):
        if path.exists():
            lines.append(f"{sha256_of(path)}  {path.name}")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def check_urls(targets: dict[str, str]) -> int:
    """Probe each URL and report status and size without downloading the file.

    Uses a ranged GET (Range: bytes=0-0) rather than HEAD. The DfT file server
    answers HEAD with 405 Method Not Allowed, which looks like failure but is not;
    a one-byte ranged GET returns the real status along with Content-Range, from
    which the full size can be read.

    DfT occasionally renames these files between releases. Run this first so you
    find out in two seconds rather than after a 250 MB download.
    """
    print("Checking URLs via ranged GET (1 byte)...\n")
    bad = 0
    probe_headers = {**HEADERS, "Range": "bytes=0-0"}

    for name, url in targets.items():
        try:
            response = requests.get(
                url, headers=probe_headers, stream=True, timeout=30, allow_redirects=True
            )
            with response:
                size = 0
                content_range = response.headers.get("Content-Range", "")
                if "/" in content_range:  # e.g. "bytes 0-0/97700000"
                    try:
                        size = int(content_range.rsplit("/", 1)[1])
                    except ValueError:
                        size = 0
                if not size:
                    size = int(response.headers.get("Content-Length", 0))

                ok = response.status_code in (200, 206)
                size_text = f"{size / 1e6:.1f} MB" if size else "size unknown"
                if not ok:
                    bad += 1
                print(
                    f"  [{'OK  ' if ok else 'FAIL'}] {response.status_code}  "
                    f"{size_text:>14s}  {name}"
                )
        except requests.RequestException as exc:
            bad += 1
            print(f"  [FAIL] error        {name}: {exc}")

    print()
    if bad:
        print(
            f"{bad} URL(s) not reachable. Check the landing page for current filenames:\n"
            "  https://www.gov.uk/government/statistical-data-sets/road-safety-open-data",
            file=sys.stderr,
        )
        return 1
    print("All URLs reachable. Run without --check to download.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=None,
        help="Download per-year files instead of the 5-year bundle, e.g. --years 2021 2025",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if the files already exist",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only verify that the URLs are reachable; do not download",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    targets: dict[str, str] = {}
    if args.years:
        for year in sorted(args.years):
            for table in BUNDLES:
                name = YEAR_TEMPLATE.format(table=table, year=year)
                targets[name] = f"{BASE_URL}/{name}"
    else:
        for table, name in BUNDLES.items():
            targets[name] = f"{BASE_URL}/{name}"

    if args.check:
        return check_urls(targets)

    print(f"Downloading {len(targets)} file(s) into {RAW_DIR}\n")

    downloaded: list[Path] = []
    failures: list[str] = []

    for name, url in targets.items():
        try:
            downloaded.append(download(url, RAW_DIR / name, force=args.force))
        except requests.RequestException:
            failures.append(name)

    print()
    if downloaded:
        manifest = write_checksums(downloaded)
        print(f"Checksum manifest written to {manifest}")

    if failures:
        print(f"\n{len(failures)} file(s) failed:", file=sys.stderr)
        for name in failures:
            print(f"  - {name}", file=sys.stderr)
        print(
            "\nIf a URL has changed, check the landing page for the current filenames:\n"
            "  https://www.gov.uk/government/statistical-data-sets/road-safety-open-data",
            file=sys.stderr,
        )
        return 1

    print("\nAll files present. Next: python src/prepare_data.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
