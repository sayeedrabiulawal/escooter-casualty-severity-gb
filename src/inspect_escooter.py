"""
Verify the e-scooter identification against the actual downloaded STATS19 files.

WHY THIS EXISTS
---------------
The DfT data guide (docs/guide-search-report.txt) shows TWO different mechanisms
for identifying e-scooters, introduced in different years:

    vehicle.escooter_flag    1 = vehicle was an e-scooter    introduced 2023
    vehicle.vehicle_type     33 = "Personal powered transporter" (2024 spec)
    casualty.escooter_flag   1 = casualty was using an e-scooter  introduced 2025

They do not all cover the same years, so the study period depends on which one
you use. This script measures the actual coverage in the downloaded data before
any analysis decision is made.

Run this BEFORE src/analysis.py.

Usage:
    python src/inspect_escooter.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DOCS_DIR = PROJECT_ROOT / "docs"

GUIDE_XLSX = DOCS_DIR / "data-guide" / "dft-stats19-data-guide.xlsx"

VEHICLE_TYPE_PPT = 33  # "Personal powered transporter" - introduced 2024 spec
VEHICLE_TYPE_MOBILITY_SCOOTER = 22  # do NOT confuse with the above


def load_raw(table: str) -> pd.DataFrame:
    path = RAW_DIR / f"dft-road-casualty-statistics-{table}-last-5-years.csv"
    if not path.exists():
        raise SystemExit(f"Missing {path}. Run: python src/download_data.py")
    return pd.read_csv(path, low_memory=False)


def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def check_columns(name: str, frame: pd.DataFrame) -> None:
    section(f"{name}: e-scooter related columns present?")
    candidates = [c for c in frame.columns if "scooter" in c.lower()]
    print(f"  Columns matching 'scooter': {candidates or 'NONE'}")
    if "escooter_flag" in frame.columns:
        print("  [OK] escooter_flag present")
    else:
        print("  [!!] escooter_flag ABSENT from this table")


def coverage_by_year(name: str, frame: pd.DataFrame) -> pd.DataFrame | None:
    section(f"{name}: escooter_flag coverage by year")
    if "escooter_flag" not in frame.columns or "collision_year" not in frame.columns:
        print("  Cannot report - required columns missing.")
        return None

    flag = pd.to_numeric(frame["escooter_flag"], errors="coerce")
    year = pd.to_numeric(frame["collision_year"], errors="coerce")

    table = pd.crosstab(year, flag, dropna=False)
    print("\n  Counts of escooter_flag by collision_year:")
    print(table.to_string().replace("\n", "\n  "))

    print("\n  Records flagged as e-scooter (flag == 1) per year:")
    # .count() not .size(): .size() counts rows regardless of NaN, so masked
    # values would be counted as if they were flagged. .count() excludes them.
    per_year = flag.where(flag == 1).groupby(year).count().reindex(
        sorted(year.dropna().unique()), fill_value=0
    )
    for y, count in per_year.items():
        print(f"    {int(y)}: {int(count):>6,}")

    usable_years = sorted(int(y) for y, c in per_year.items() if c > 0)
    print(f"\n  >> Years with any e-scooter records: {usable_years}")
    return table


def compare_mechanisms(vehicles: pd.DataFrame) -> None:
    section("Do escooter_flag and vehicle_type==33 agree?")
    if "escooter_flag" not in vehicles.columns or "vehicle_type" not in vehicles.columns:
        print("  Both columns needed; cannot compare.")
        return

    flag = pd.to_numeric(vehicles["escooter_flag"], errors="coerce")
    vtype = pd.to_numeric(vehicles["vehicle_type"], errors="coerce")
    year = pd.to_numeric(vehicles["collision_year"], errors="coerce")

    for label, mask in (("escooter_flag == 1", flag == 1), ("vehicle_type == 33", vtype == VEHICLE_TYPE_PPT)):
        subset = vehicles[mask]
        years = sorted(pd.to_numeric(subset["collision_year"], errors="coerce").dropna().unique())
        years = [int(y) for y in years]
        print(f"\n  {label:24s} n={len(subset):>7,}   years={years}")

    both = (flag == 1) & (vtype == VEHICLE_TYPE_PPT)
    only_flag = (flag == 1) & (vtype != VEHICLE_TYPE_PPT)
    only_type = (flag != 1) & (vtype == VEHICLE_TYPE_PPT)
    print(f"\n  Agreement matrix:")
    print(f"    flag==1 AND type==33 : {both.sum():>7,}")
    print(f"    flag==1 AND type!=33 : {only_flag.sum():>7,}")
    print(f"    flag!=1 AND type==33 : {only_type.sum():>7,}")

    mismatched = vehicles[only_flag & (year >= 2024)]
    if len(mismatched):
        print("\n  vehicle_type values where flag==1 but type!=33 (2024+), top 10:")
        print(
            mismatched["vehicle_type"]
            .value_counts()
            .head(10)
            .to_string()
            .replace("\n", "\n    ")
        )


def vehicle_type_codes_for_escooters(vehicles: pd.DataFrame) -> None:
    section("vehicle_type codes used on e-scooter records")
    if "escooter_flag" not in vehicles.columns or "vehicle_type" not in vehicles.columns:
        return

    flag = pd.to_numeric(vehicles["escooter_flag"], errors="coerce")
    subset = vehicles[flag == 1]
    if subset.empty:
        print("  No e-scooter records found.")
        return

    counts = subset["vehicle_type"].value_counts().head(15)
    print(counts.to_string().replace("\n", "\n  "))


def dump_vehicle_type_codes() -> None:
    section("Full vehicle_type code list (from the DfT data guide)")
    if not GUIDE_XLSX.exists():
        print("  Guide not downloaded. Run: python src/fetch_data_guide.py")
        return

    sheet = pd.read_excel(GUIDE_XLSX, sheet_name="2024_code_list", header=None, dtype=str)
    values = sheet.to_numpy(dtype=object)

    # The guide is a flat grid: table | field | code | label | note
    rows = []
    for row in values:
        cells = [("" if c is None else str(c).strip()) for c in row]
        if len(cells) >= 4 and cells[0] == "vehicle" and cells[1] == "vehicle_type":
            rows.append((cells[2], cells[3]))

    if not rows:
        print("  Could not locate the vehicle_type table.")
        return

    for code, label in rows:
        marker = ""
        if code == str(VEHICLE_TYPE_PPT):
            marker = "   <== PERSONAL POWERED TRANSPORTER (e-scooter)"
        elif code == str(VEHICLE_TYPE_MOBILITY_SCOOTER):
            marker = "   <== mobility scooter, NOT an e-scooter"
        print(f"  {code:>4s}  {label}{marker}")


def main() -> int:
    vehicles = load_raw("vehicle")
    casualties = load_raw("casualty")
    collisions = load_raw("collision")

    print(f"vehicle   rows: {len(vehicles):,}")
    print(f"casualty  rows: {len(casualties):,}")
    print(f"collision rows: {len(collisions):,}")

    check_columns("vehicle", vehicles)
    check_columns("casualty", casualties)

    coverage_by_year("vehicle", vehicles)
    coverage_by_year("casualty", casualties)

    compare_mechanisms(vehicles)
    vehicle_type_codes_for_escooters(vehicles)
    dump_vehicle_type_codes()

    section("INTERPRETATION")
    print(
        "  Use whichever mechanism gives the longest defensible study period, and\n"
        "  state the choice explicitly in the paper's methods section.\n\n"
        "  Then record the decision in docs/data-notes.md and update the mode\n"
        "  definition in src/analysis.py."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
