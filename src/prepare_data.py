"""
Build the analysis-ready dataset from the raw STATS19 files.

Deliberately defensive: STATS19 columns and code values change between releases,
so this script VALIDATES before it transforms, and prints a schema report you are
expected to read. Do not trust the coding assumptions below without checking them
against the DfT data guide for the release you downloaded.

Reference (read this first):
  https://www.gov.uk/government/statistical-data-sets/road-safety-open-data
  -> "Open dataset data guide" (XLSX)

Usage:
    python src/prepare_data.py
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DOCS_DIR = PROJECT_ROOT / "docs"
GUIDE_XLSX = DOCS_DIR / "data-guide" / "dft-stats19-data-guide.xlsx"

# ---------------------------------------------------------------------------
# VERIFIED CODE VALUES
#
# Confirmed against the DfT data guide (docs/data-guide/) AND against the
# September 2026 release of the open data (docs/escooter-inspection.txt).
# Do not change these without re-verifying; see src/inspect_escooter.py.
#
#   vehicle_type 33 = "Personal powered transporter"  (e-scooter)
#   vehicle_type  1 = "Pedal cycle"
#   vehicle_type 22 = "Mobility scooter"  <- NOT an e-scooter, do not include
#   escooter_flag exists in BOTH the vehicle and casualty tables
#
# NOTE: the data guide states escooter_flag was introduced in 2023 (vehicle) and
# 2025 (casualty), but the September 2026 release has it populated for 2021-2025
# in both tables. It has therefore been back-filled. Flag this in the paper: an
# analysis using an older snapshot would not reproduce these results.
# ---------------------------------------------------------------------------

VEHICLE_TYPE_PPT = 33
VEHICLE_TYPE_PEDAL_CYCLE = 1
VEHICLE_TYPE_MOTORCYCLE = [2, 3, 4, 5, 23, 97]

# Candidate column names for the new categorisation, kept for the schema report.
CANDIDATE_MODE_COLUMNS = {
    "vehicle": ["vehicle_type", "escooter_flag"],
    "casualty": ["casualty_type", "escooter_flag"],
}

# Columns renamed before merging: both the casualty and vehicle tables now carry
# an 'escooter_flag'. The casualty-level flag is the one that identifies an
# injured e-scooter rider, so it must not be overwritten by the vehicle's.
RENAME_ON_MERGE = {
    "casualty": {"escooter_flag": "casualty_escooter_flag"},
    "vehicle": {"escooter_flag": "vehicle_escooter_flag"},
}

# Severity codes (standard across recent STATS19 releases — still verify).
SEVERITY_FATAL = 1
SEVERITY_SERIOUS = 2
SEVERITY_SLIGHT = 3

JOIN_KEY = "collision_index"

# A collision contains several vehicles, so collision_index alone does NOT
# identify a casualty's own vehicle. Joining on collision_index only and dropping
# duplicates silently attaches an ARBITRARY vehicle from the collision to every
# casualty, which corrupts any vehicle-level variable (vehicle_type above all).
# vehicle_reference exists in both the casualty and vehicle tables precisely to
# disambiguate this, and must form part of the join key.
VEHICLE_JOIN_KEYS = ["collision_index", "vehicle_reference"]

# STATS19 does NOT use blank cells for missing values. It uses integer sentinels,
# so a naive frame.isna() reports 0% missing on every field. The dominant sentinel
# is -1 = "Data missing or out of range".
#
# This matters far more than it looks: if -1 is left in place, `speed_limit` gains
# a real category called -1 and `urban_or_rural_area` gains -1. The models then
# fit and report a "-1 level" as though it meant something.
MISSING_SENTINEL = -1

# Coded fields used in the analysis. Sentinels are converted to NaN on these only.
ANALYSIS_CODE_FIELDS = [
    "casualty_severity",
    "casualty_type",
    "sex_of_casualty",
    "age_of_casualty",
    "casualty_escooter_flag",
    "vehicle_type",
    "vehicle_escooter_flag",
    "vehicle_manoeuvre",
    "sex_of_driver",
    "age_of_driver",
    "road_type",
    "speed_limit",
    "junction_detail",
    "light_conditions",
    "weather_conditions",
    "road_surface_conditions",
    "urban_or_rural_area",
    "police_force",
    "did_police_officer_attend_scene_of_accident",
]

# Field-specific "unknown" codes are NOT guessed. They are read from the DfT data
# guide, because a blanket check for 9/99 produces false positives: vehicle_type
# 9 is "Car" and 10 is "Minibus", both perfectly valid. Only codes whose guide
# label says unknown/missing/unallocated are treated as missing.
UNKNOWN_LABEL_KEYWORDS = (
    "missing",
    "unknown",
    "not known",
    "out of range",
    "unallocated",
    "not applicable",
)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def find_raw_file(table: str) -> Path:
    """Locate the raw CSV for a table, whether bundled or per-year."""
    exact = RAW_DIR / f"dft-road-casualty-statistics-{table}-last-5-years.csv"
    if exact.exists():
        return exact

    matches = sorted(RAW_DIR.glob(f"dft-road-casualty-statistics-{table}-*.csv"))
    matches = [m for m in matches if m.name != "checksums.sha256"]
    if matches:
        return matches[0]

    raise FileNotFoundError(
        f"No raw {table} file in {RAW_DIR}. Run: python src/download_data.py"
    )


def load(table: str) -> pd.DataFrame:
    path = find_raw_file(table)
    print(f"Loading {table:9s} <- {path.name}")
    # low_memory=False: STATS19 columns are mixed-type and chunked inference
    # produces spurious dtype warnings otherwise.
    return pd.read_csv(path, low_memory=False)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_join_key(collisions: pd.DataFrame, vehicles: pd.DataFrame) -> bool:
    """Validate both join keys before any merge happens."""
    if JOIN_KEY not in collisions.columns:
        print(f"  [FAIL] '{JOIN_KEY}' missing from the collision table.")
        return False

    duplicates = collisions[JOIN_KEY].duplicated().sum()
    if duplicates:
        print(f"  [FAIL] '{JOIN_KEY}' has {duplicates:,} duplicate values.")
        return False
    print(f"  [ OK ] '{JOIN_KEY}' is unique across {len(collisions):,} collisions.")

    # The vehicle link is a composite key. If it is not unique, a casualty could
    # match more than one vehicle row and the merge would fan out silently.
    missing_keys = [k for k in VEHICLE_JOIN_KEYS if k not in vehicles.columns]
    if missing_keys:
        print(f"  [FAIL] vehicle table missing join key(s): {missing_keys}")
        return False

    vehicle_combos = vehicles[VEHICLE_JOIN_KEYS].duplicated().sum()
    if vehicle_combos:
        print(
            f"  [FAIL] {'+'.join(VEHICLE_JOIN_KEYS)} has {vehicle_combos:,} "
            "duplicate combinations."
        )
        return False
    print(
        f"  [ OK ] {'+'.join(VEHICLE_JOIN_KEYS)} is unique across "
        f"{len(vehicles):,} vehicle records."
    )
    return True


def report_schema(name: str, frame: pd.DataFrame, max_columns: int = 200) -> None:
    print(f"\n{name} - {len(frame):,} rows x {frame.shape[1]} columns")
    for column in list(frame.columns)[:max_columns]:
        non_null = frame[column].notna().sum()
        pct = 100 * non_null / len(frame) if len(frame) else 0
        sample = frame[column].dropna().unique()[:4]
        preview = ", ".join(str(v) for v in sample)
        print(f"  {column:45s} {pct:6.1f}% populated   e.g. [{preview}]")
    if frame.shape[1] > max_columns:
        print(f"  ... and {frame.shape[1] - max_columns} more columns")


def locate_mode_columns(frames: dict[str, pd.DataFrame]) -> None:
    """Report which candidate mode columns exist, and confirm the verified codes."""
    print("\n--- Mode column candidates ---")
    for table, candidates in CANDIDATE_MODE_COLUMNS.items():
        if table not in frames:
            continue
        print(f"\n{table}:")
        for candidate in candidates:
            mark = "FOUND" if candidate in frames[table].columns else "absent"
            print(f"  [{mark:>6s}] {candidate}")

    # Confirm the e-scooter codes actually appear in this release, rather than
    # trusting the data guide. A release change would silently empty the cohort.
    print("\n--- Verified code check ---")
    vehicles = frames.get("vehicle")
    if vehicles is not None:
        vtype = pd.to_numeric(vehicles["vehicle_type"], errors="coerce")
        n_ppt = int((vtype == VEHICLE_TYPE_PPT).sum())
        n_cycle = int((vtype == VEHICLE_TYPE_PEDAL_CYCLE).sum())
        n_moto = int(vtype.isin(VEHICLE_TYPE_MOTORCYCLE).sum())
        n_mobility = int((vtype == 22).sum())
        print(f"  vehicle_type == {VEHICLE_TYPE_PPT}  (e-scooter)      {n_ppt:>7,} vehicles")
        print(f"  vehicle_type == {VEHICLE_TYPE_PEDAL_CYCLE}   (pedal cycle)    {n_cycle:>7,} vehicles")
        print(f"  motorcycle codes {VEHICLE_TYPE_MOTORCYCLE}  {n_moto:>7,} vehicles")
        print(f"  vehicle_type == 22  (mobility scooter, EXCLUDED) {n_mobility:>7,}")
        if n_ppt == 0:
            print("  [FAIL] No e-scooter vehicles found. Re-run src/inspect_escooter.py")
        else:
            print("  [ OK ] E-scooter code confirmed present in this release.")
    print()


# ---------------------------------------------------------------------------
# Transformation
# ---------------------------------------------------------------------------


def derive_severity(casualties: pd.DataFrame) -> pd.DataFrame:
    """Add is_kasi: 1 for killed or seriously injured, 0 for slight, NA if unknown.

    Uses the nullable Int64 dtype rather than a boolean with pd.NA values.
    A boolean column containing pd.NA becomes an object column, which survives a
    CSV round-trip as the strings 'True'/'False'/'<NA>' and then silently breaks
    every downstream model. 1/0/blank round-trips cleanly.
    """
    if "casualty_severity" not in casualties.columns:
        raise KeyError("casualty_severity not found in the casualty table")

    severity = pd.to_numeric(casualties["casualty_severity"], errors="coerce")
    unknown = severity.isna() | ~severity.isin(
        [SEVERITY_FATAL, SEVERITY_SERIOUS, SEVERITY_SLIGHT]
    )
    if unknown.any():
        print(f"  [warn] {unknown.sum():,} casualties with unknown severity")

    casualties = casualties.copy()
    is_kasi = ((severity == SEVERITY_FATAL) | (severity == SEVERITY_SERIOUS)).astype(
        "Int64"
    )
    is_kasi[unknown] = pd.NA
    casualties["is_kasi"] = is_kasi
    # Keep an explicit flag so the write-up can quantify what was excluded.
    casualties["severity_unknown"] = unknown.astype(int)
    return casualties


def build_analysis_dataset(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Left-join casualty -> vehicle -> collision on collision_index.

    Both the casualty and vehicle tables carry an 'escooter_flag' column, so they
    are renamed before merging. Without this the vehicle's flag would silently
    shadow the casualty's, and the e-scooter cohort would be defined by the wrong
    table (5,631 casualties vs 6,786 vehicles).
    """
    casualties = derive_severity(frames["casualty"])
    casualties = casualties.rename(columns=RENAME_ON_MERGE["casualty"])

    vehicles = frames["vehicle"].rename(columns=RENAME_ON_MERGE["vehicle"])
    collisions = frames["collision"]

    if VEHICLE_JOIN_KEYS[1] not in casualties.columns:
        raise KeyError(
            f"'{VEHICLE_JOIN_KEYS[1]}' not found on the casualty table, so casualties "
            "cannot be linked to their own vehicle. Check the release schema."
        )

    # Vehicle-level fields we want. The join keys are excluded because they are
    # already present on the casualty side, with identical values.
    vehicle_columns = VEHICLE_JOIN_KEYS + [
        c
        for c in (
            "vehicle_type",
            "vehicle_manoeuvre",
            "vehicle_escooter_flag",
            "sex_of_driver",
            "age_of_driver",
        )
        if c in vehicles.columns
    ]

    before = len(casualties)
    merged = casualties.merge(
        vehicles[vehicle_columns],
        on=VEHICLE_JOIN_KEYS,
        how="left",
        validate="many_to_one",
    )
    if len(merged) != before:
        raise AssertionError(
            f"Merge changed row count: {before:,} -> {len(merged):,}. "
            "The vehicle join key is not unique; investigate before continuing."
        )
    print(
        f"  Vehicle link: {merged['vehicle_type'].notna().sum():,} of {before:,} "
        f"casualties matched to their own vehicle "
        f"({100 * merged['vehicle_type'].notna().mean():.1f}%)"
    )

    collision_columns = [JOIN_KEY] + [
        c
        for c in (
            "date",
            "time",
            "police_force",
            "road_type",
            "speed_limit",
            "junction_detail",
            "light_conditions",
            "weather_conditions",
            "urban_or_rural_area",
            "longitude",
            "latitude",
        )
        if c in collisions.columns
    ]
    merged = merged.merge(
        collisions[collision_columns],
        on=JOIN_KEY,
        how="left",
        validate="many_to_one",
    )

    # Must happen after the merge and before export: this is what makes the
    # missingness report meaningful and keeps -1 out of the regression models.
    merged = apply_missing_sentinels(merged)
    return merged


def load_unknown_codes_from_guide() -> dict[str, set[int]]:
    """Return {field: {codes}} where the guide labels a code unknown or missing.

    The guide is a flat grid of: table | field | code | label | note. Rather than
    hard-coding assumptions about which value means "unknown" for each field, this
    reads the authoritative labels.
    """
    if not GUIDE_XLSX.exists():
        print(
            "  [warn] Data guide not found, so field-specific unknown codes are "
            "not applied.\n         Run: python src/fetch_data_guide.py"
        )
        return {}

    sheet = pd.read_excel(GUIDE_XLSX, sheet_name="2024_code_list", header=None, dtype=str)
    values = sheet.to_numpy(dtype=object)

    result: dict[str, set[int]] = {}
    for row in values:
        cells = [("" if c is None else str(c).strip()) for c in row]
        if len(cells) < 4:
            continue
        field, code, label = cells[1], cells[2], cells[3].lower()
        if not field or not code or not label:
            continue
        if not any(keyword in label for keyword in UNKNOWN_LABEL_KEYWORDS):
            continue
        try:
            code_int = int(code)
        except ValueError:
            continue
        result.setdefault(field, set()).add(code_int)

    print(f"  Read unknown-code definitions for {len(result)} field(s) from the data guide.")
    return result


def apply_missing_sentinels(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert STATS19 missing sentinels to NaN and report what was converted.

    Two passes:
      1. -1, which is uniformly "Data missing or out of range".
      2. Field-specific codes the data guide labels unknown/missing.

    Without this, -1 survives into the models as a legitimate category. Reporting
    the counts keeps the conversion in the audit trail.
    """
    frame = frame.copy()
    print("\n--- Missing value conversion -> NaN ---")

    print("\n  Pass 1: sentinel -1")
    converted_any = False
    for field in ANALYSIS_CODE_FIELDS:
        if field not in frame.columns:
            continue
        column = pd.to_numeric(frame[field], errors="coerce")
        n_sentinel = int((column == MISSING_SENTINEL).sum())
        if n_sentinel:
            pct = 100 * n_sentinel / len(frame)
            print(f"    {field:42s} {n_sentinel:>8,} ({pct:5.2f}%)")
            converted_any = True
        frame[field] = column.mask(column == MISSING_SENTINEL)

    if not converted_any:
        print("    None found. Check the release has not changed its conventions.")

    print("\n  Pass 2: field-specific unknown codes (from the data guide)")
    unknown_codes = load_unknown_codes_from_guide()
    if unknown_codes:
        any_second = False
        for field in ANALYSIS_CODE_FIELDS:
            codes = unknown_codes.get(field)
            if not codes or field not in frame.columns:
                continue
            # -1 already handled; including it here would be redundant.
            codes = {c for c in codes if c != MISSING_SENTINEL}
            if not codes:
                continue
            n_unknown = int(frame[field].isin(codes).sum())
            if n_unknown:
                pct = 100 * n_unknown / len(frame)
                print(
                    f"    {field:42s} {n_unknown:>8,} ({pct:5.2f}%)  "
                    f"codes={sorted(codes)}"
                )
                any_second = True
            frame[field] = frame[field].mask(frame[field].isin(codes))
        if not any_second:
            print("    No additional unknown codes present in this dataset.")

    return frame


def report_missingness(frame: pd.DataFrame, minimum_pct: float = 0.0) -> None:
    print("\n--- Missingness on key analysis fields ---")
    key_fields = [
        "casualty_severity",
        "is_kasi",
        "severity_unknown",
        "casualty_escooter_flag",
        "vehicle_escooter_flag",
        "casualty_type",
        "vehicle_type",
        "sex_of_casualty",
        "age_of_casualty",
        "speed_limit",
        "light_conditions",
        "road_type",
        "urban_or_rural_area",
        "date",
    ]
    for field in key_fields:
        if field not in frame.columns:
            print(f"  {field:25s} NOT PRESENT")
            continue
        missing_pct = 100 * frame[field].isna().mean()
        flag = "  <-- investigate" if missing_pct > 10 else ""
        print(f"  {field:25s} {missing_pct:6.2f}% missing{flag}")
    print(
        "\nReport these in the paper. Do not silently drop unknown values -\n"
        "quantify them and run a sensitivity analysis."
    )


def write_dataset(frame: pd.DataFrame) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = PROCESSED_DIR / "analysis_dataset.csv"
    frame.to_csv(out, index=False)

    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"\nWrote {out} ({out.stat().st_size / 1e6:.1f} MB)")
    print(f"SHA-256: {digest}")
    print("Record this hash in docs/data-notes.md — it fixes the exact dataset used.")
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print("=== STATS19 preparation ===\n")

    try:
        frames = {table: load(table) for table in ("collision", "vehicle", "casualty")}
    except FileNotFoundError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1

    for name, frame in frames.items():
        report_schema(name.capitalize(), frame, max_columns=40)

    print("\n--- Join key validation ---")
    if not validate_join_key(frames["collision"], frames["vehicle"]):
        return 1

    locate_mode_columns(frames)

    print("--- Building analysis dataset ---")
    merged = build_analysis_dataset(frames)
    print(f"  {len(merged):,} casualty records, {merged.shape[1]} columns")

    report_missingness(merged)
    write_dataset(merged)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    print("\nNext steps:")
    print("  1. Check the verified code counts above are non-zero.")
    print("  2. Confirm the missingness report against docs/data-notes.md.")
    print("  3. Record the dataset SHA-256 in docs/data-notes.md.")
    print("  4. Then run: python src/analysis.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
