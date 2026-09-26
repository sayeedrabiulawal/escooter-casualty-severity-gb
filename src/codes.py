"""
Decode STATS19 integer codes into the human-readable labels from the DfT data guide.

WHY THIS EXISTS
---------------
STATS19 ships codes, not labels. A regression table reading
``C(light_conditions)[T.4.0]`` is unreadable and unpublishable. Mapping each code
to the guide's own label turns the same coefficient into
``light_conditions = Darkness - lights lit``, which is what belongs in a paper.

Labels come straight from the DfT guide so they are authoritative rather than
paraphrased. If the guide is unavailable, the functions degrade gracefully to the
raw codes instead of failing.

Usage:
    from codes import label_map, add_labelled_columns
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GUIDE_XLSX = PROJECT_ROOT / "docs" / "data-guide" / "dft-stats19-data-guide.xlsx"

# Matches codes the guide flags as not-real values. After sentinel conversion
# these should already be NaN, but some may survive for fields not listed in
# prepare_data.ANALYSIS_CODE_FIELDS.
_MISSING_LABEL_PATTERN = re.compile(
    r"missing|unknown|not known|out of range|unallocated|not applicable",
    re.IGNORECASE,
)

_cache: dict[str, dict[str, str]] | None = None

# Some fields are plain measured values rather than coded categories, so the guide
# has no code list for them. speed_limit is the important example: rendering it as
# "code 30" would be worse than useless in a regression table.
UNIT_SUFFIX: dict[str, str] = {
    "speed_limit": " mph",
}


def _load_all_labels() -> dict[str, dict[str, str]]:
    """Read {field: {code_string: label}} from the guide's 2024 code list sheet."""
    global _cache
    if _cache is not None:
        return _cache

    _cache = {}
    if not GUIDE_XLSX.exists():
        print(
            "[codes] Data guide not found; falling back to raw codes.\n"
            "        Run: python src/fetch_data_guide.py"
        )
        return _cache

    sheet = pd.read_excel(GUIDE_XLSX, sheet_name="2024_code_list", header=None, dtype=str)
    for row in sheet.to_numpy(dtype=object):
        cells = [("" if c is None else str(c).strip()) for c in row]
        if len(cells) < 4:
            continue
        field, code, label = cells[1], cells[2], cells[3]
        if not field or not code or not label:
            continue
        # The guide is a human-formatted sheet with merged and blank cells, so a
        # missing value can arrive as the literal string "nan". Treating that as a
        # real code makes the field look like it has a code list when it does not,
        # which then suppresses the unit-suffix fallback in add_labelled_columns.
        if code.lower() in ("nan", "none") or label.lower() in ("nan", "none"):
            continue
        # Skip discontinued categories so current labels are not shadowed by
        # legacy ones (e.g. three different meanings for motorcycle codes).
        note = cells[4].lower() if len(cells) > 4 else ""
        if "discontinued" in note:
            continue
        _cache.setdefault(field, {})[code] = label

    return _cache


def clean_label(label: str, max_length: int = 52) -> str:
    """Tidy a guide label for use as a coefficient name."""
    text = label.strip().rstrip(".")
    text = re.sub(r"\s+", " ", text)
    if len(text) > max_length:
        text = text[: max_length - 1].rstrip() + "\u2026"
    return text


def label_map(field: str, *, keep_missing: bool = False) -> dict[float, str]:
    """Return {numeric_code: label} for a STATS19 field.

    Args:
        field: STATS19 field name, e.g. "light_conditions".
        keep_missing: when False (default), codes the guide marks as
            missing/unknown are omitted, so they never appear as a level.
    """
    labels = _load_all_labels().get(field, {})
    result: dict[float, str] = {}

    for code, label in labels.items():
        if not keep_missing and _MISSING_LABEL_PATTERN.search(label):
            continue
        try:
            result[float(code)] = clean_label(label)
        except ValueError:
            continue

    return result


def add_labelled_columns(
    frame: pd.DataFrame,
    fields: list[str],
    suffix: str = "_label",
    *,
    max_levels: int = 40,
) -> tuple[pd.DataFrame, list[str]]:
    """Add a human-readable ``<field>_label`` column for each field in ``fields``.

    Returns the frame and the list of label columns actually created, so callers
    can build formulas from what exists rather than assuming.

    A field with more levels than ``max_levels`` is skipped: an unordered
    categorical with 40+ levels is not interpretable in a regression table anyway,
    and silently creating one is worse than leaving it out.
    """
    frame = frame.copy()
    created: list[str] = []

    for field in fields:
        if field not in frame.columns:
            continue
        numeric = pd.to_numeric(frame[field], errors="coerce")
        # Round to match the float keys produced by the code conversion.
        levels = sorted(numeric.dropna().round().unique())
        if len(levels) > max_levels:
            print(
                f"  [codes] '{field}' has {len(levels)} levels "
                f"(> {max_levels}); left as raw codes."
            )
            continue

        target = f"{field}{suffix}"
        mapping = label_map(field)
        unit = UNIT_SUFFIX.get(field, "")

        if mapping:
            # Codes seen in the data but absent from the guide stay visible as
            # "code <n>" rather than vanishing, so nothing disappears silently.
            labels = {code: mapping.get(code, f"code {int(code)}") for code in levels}
        else:
            # A measured value rather than a coded category.
            labels = {code: f"{int(code)}{unit}" for code in levels}

        frame[target] = numeric.round().map(labels)
        created.append(target)

    return frame, created


def reference_level(series: pd.Series) -> str:
    """The level a formula will treat as the baseline for this predictor.

    patsy uses the first level of a Categorical's own category order, but sorts
    the levels of a plain string column alphabetically. Those two rules give
    different answers, so the distinction has to be respected rather than assumed.
    """
    if isinstance(series.dtype, pd.CategoricalDtype) and series.cat.categories.size:
        return str(series.cat.categories[0])
    values = series.dropna().astype(str).unique()
    return str(sorted(values)[0]) if len(values) else ""


def describe_label_source() -> str:
    """One-line provenance note for the methods section."""
    if not GUIDE_XLSX.exists():
        return "STATS19 codes were used unlabelled (data guide unavailable)."
    return (
        "Variable categories use the labels given in the DfT "
        "'Road safety open dataset data guide'."
    )
