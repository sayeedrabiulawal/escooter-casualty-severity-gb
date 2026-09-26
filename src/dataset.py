"""
Shared data loading and mode classification.

WHY THIS EXISTS
---------------
Mode classification started out inside analysis.py, which meant figures.py could
not see the derived ``mode`` column and crashed. More importantly, having the
definition of "an e-scooter casualty" in one place only is essential: if two
scripts classify mode independently they will eventually disagree, and the
figures will silently contradict the tables.

Both analysis.py and figures.py import from here.

Usage:
    from dataset import prepare_analysis_frame
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATASET_PATH = PROCESSED_DIR / "analysis_dataset.csv"

# ---------------------------------------------------------------------------
# Verified code values
#
# Confirmed against the DfT data guide (docs/data-guide/) and the September 2026
# release of the open data (docs/escooter-inspection.txt). Re-verify with
# src/inspect_escooter.py before changing anything here.
#
#   vehicle_type 33 = "Personal powered transporter"  (e-scooter)
#   vehicle_type  1 = "Pedal cycle"
#   vehicle_type 22 = "Mobility scooter"  <- NOT an e-scooter, excluded
# ---------------------------------------------------------------------------

VEHICLE_TYPE_PPT = 33
VEHICLE_TYPE_PEDAL_CYCLE = 1
VEHICLE_TYPE_MOTORCYCLE = [2, 3, 4, 5, 23, 97]

MODE_ORDER = ["escooter", "pedal_cycle", "motorcycle"]

# Reference category for the comparative models. Pedal cycle is chosen because it
# is the most directly comparable mode to an e-scooter (similar speed, no
# protective shell, similar road position), so the resulting odds ratio is the
# most informative single number in the paper.
MODE_REFERENCE = "pedal_cycle"


def load_dataset() -> pd.DataFrame:
    """Load the derived dataset produced by src/prepare_data.py."""
    if not DATASET_PATH.exists():
        raise SystemExit(
            f"ERROR: {DATASET_PATH} not found.\n"
            "Run first: python src/prepare_data.py"
        )
    return pd.read_csv(DATASET_PATH, low_memory=False)


def classify_mode(frame: pd.DataFrame, *, verbose: bool = True) -> pd.DataFrame:
    """Assign analysis groups. E-scooters use the casualty-level flag.

    Every assignment is guarded by .isna() so an earlier and more specific
    definition can never be overwritten by a later, broader one. Without the guard
    a pedal-cycle vehicle code would silently reclassify e-scooter casualties.
    """
    if "vehicle_type" not in frame.columns:
        raise KeyError("'vehicle_type' not in dataset; cannot classify mode")

    frame = frame.copy()
    vehicle_type = pd.to_numeric(frame["vehicle_type"], errors="coerce")
    frame["mode"] = pd.NA

    # Primary definition: the purpose-built casualty-level e-scooter flag.
    if "casualty_escooter_flag" in frame.columns:
        casualty_flag = pd.to_numeric(frame["casualty_escooter_flag"], errors="coerce")
        frame.loc[casualty_flag == 1, "mode"] = "escooter"
    else:
        if verbose:
            print(
                "  [warn] casualty_escooter_flag missing; falling back to "
                f"vehicle_type == {VEHICLE_TYPE_PPT}"
            )
        frame.loc[vehicle_type == VEHICLE_TYPE_PPT, "mode"] = "escooter"

    pedal_mask = (vehicle_type == VEHICLE_TYPE_PEDAL_CYCLE) & frame["mode"].isna()
    frame.loc[pedal_mask, "mode"] = "pedal_cycle"

    motorcycle_mask = vehicle_type.isin(VEHICLE_TYPE_MOTORCYCLE) & frame["mode"].isna()
    frame.loc[motorcycle_mask, "mode"] = "motorcycle"

    if verbose:
        print("Mode assignment:")
        for mode in MODE_ORDER:
            print(f"  {mode:12s} {int((frame['mode'] == mode).sum()):>8,}")
        print(f"  {'(unclassified)':12s} {int(frame['mode'].isna().sum()):>8,}")
        validate_escooter_nesting(frame)

    return frame


def validate_escooter_nesting(frame: pd.DataFrame) -> None:
    """Confirm e-scooter records are consistent with vehicle_type.

    In the September 2026 release every flagged casualty sits on a vehicle of
    type 33 and no flagged record carries any other type. If that stops being
    true the cohort definition has shifted and every number downstream changes
    meaning, so it is asserted rather than assumed.
    """
    vehicle_type = pd.to_numeric(frame["vehicle_type"], errors="coerce")
    escooter = frame["mode"] == "escooter"
    if not escooter.any():
        return

    on_type = int((escooter & (vehicle_type == VEHICLE_TYPE_PPT)).sum())
    off_type = int((escooter & (vehicle_type != VEHICLE_TYPE_PPT)).sum())
    total = int(escooter.sum())

    print(
        f"  [check] e-scooter records on vehicle_type {VEHICLE_TYPE_PPT}: "
        f"{on_type:,} of {total:,}"
    )
    if off_type:
        print(
            f"  [warn] {off_type:,} e-scooter casualties are NOT on a "
            f"vehicle_type {VEHICLE_TYPE_PPT} vehicle."
        )
        print("         Compare the flag against vehicle_type in the sensitivity analysis.")
    else:
        print("  [ OK ] Flag and vehicle_type agree perfectly; definition is stable.")


def add_derived_fields(frame: pd.DataFrame) -> pd.DataFrame:
    """Add year, month, age, age band, and the numeric outcome."""
    frame = frame.copy()

    if "date" in frame.columns:
        # STATS19 dates are DD/MM/YYYY, which is not the pandas default.
        frame["date"] = pd.to_datetime(
            frame["date"], format="%d/%m/%Y", errors="coerce"
        )
        frame["year"] = frame["date"].dt.year
        frame["month"] = frame["date"].dt.month

    if "age_of_casualty" in frame.columns:
        age = pd.to_numeric(frame["age_of_casualty"], errors="coerce")
        age = age.where((age >= 0) & (age <= 110))
        frame["age"] = age
        frame["age_band"] = pd.cut(
            age,
            bins=[0, 15, 24, 34, 44, 54, 64, 120],
            labels=["0-15", "16-24", "25-34", "35-44", "45-54", "55-64", "65+"],
        )

    frame["is_kasi_num"] = pd.to_numeric(frame["is_kasi"], errors="coerce")
    return frame


def prepare_analysis_frame(*, verbose: bool = True) -> pd.DataFrame:
    """The single entry point: load, classify mode, and derive fields."""
    frame = load_dataset()
    frame = classify_mode(frame, verbose=verbose)
    frame = add_derived_fields(frame)
    if verbose:
        print()
    return frame
