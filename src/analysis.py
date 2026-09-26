"""
Descriptive statistics and severity models for the e-scooter casualty study.

Addresses:
  RQ1 - trends in counts and severity proportions by mode and year
  RQ2 - urban/rural and geographic distribution
  RQ3 - determinants of KASI within the e-scooter subset
  RQ4 - comparative severity odds across modes (adjusted)

PREREQUISITE: prepare_data.py must have run, and the e-scooter mode definition
in CLASSIFY below must be confirmed against the DfT data guide.

Usage:
    python src/analysis.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

# src/ is the script's own directory, so this sibling import resolves when the
# script is run as `python src/analysis.py`.
from codes import add_labelled_columns, describe_label_source, reference_level
from dataset import (
    MODE_ORDER,
    MODE_REFERENCE,
    VEHICLE_TYPE_PPT,
    prepare_analysis_frame,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "tables"

# Mode definition, the verified vehicle_type codes, and the derived date/age fields
# all live in dataset.py, shared with figures.py. Keeping one definition means the
# figures cannot silently disagree with the tables about what counts as an
# e-scooter casualty.

# Categorical predictors, rendered with the DfT data guide's labels rather than
# raw integer codes. See src/codes.py.
MODEL_FIELDS = [
    "sex_of_casualty",
    "speed_limit",
    "light_conditions",
    "road_type",
    "urban_or_rural_area",
    "junction_detail",
]

# STATS19 casualty_severity codes.
SEVERITY_FATAL = 1
SEVERITY_SERIOUS = 2
SEVERITY_SLIGHT = 3

# DfT severity-adjustment columns, used for the injury-based reporting sensitivity
# analysis. See add_adjusted_outcome for why both are needed.
COL_ADJ_SERIOUS = "casualty_adjusted_severity_serious"
COL_INJURY_BASED = "casualty_injury_based"


def add_adjusted_outcome(frame: pd.DataFrame) -> pd.DataFrame:
    """Add `kasi_adj`: the DfT severity-adjusted expected KASI probability.

    WHY THIS IS NOT JUST `casualty_adjusted_severity_serious`
    -------------------------------------------------------
    That column is the probability of being SERIOUS BUT NOT FATAL. It is 0 for
    slight casualties AND 0 for fatalities, and the two adjusted columns sum to 1
    for non-fatal casualties but to 0 for fatalities. Verified in the September 2026
    release: all 8,033 fatalities have adjusted_serious == 0.000000 exactly.

    Taking the column directly as the outcome would therefore score every single
    fatality as a non-KASI case. In this dataset that understates the adjusted KASI
    rate by 5.6% (0.2192 correct vs 0.2069 naive), which is more than large enough
    to change a conclusion.

    So fatalities are added back explicitly. The result is an expected value in
    [0, 1] rather than a 0/1 flag, which is why the models below use a fractional
    (quasi-likelihood) logit rather than a standard logistic regression.
    """
    if COL_ADJ_SERIOUS not in frame.columns:
        return frame

    frame = frame.copy()
    severity = pd.to_numeric(frame["casualty_severity"], errors="coerce")
    is_fatal = (severity == SEVERITY_FATAL).astype(int)
    adjusted = pd.to_numeric(frame[COL_ADJ_SERIOUS], errors="coerce")

    frame["kasi_adj"] = (is_fatal + adjusted).clip(0, 1)
    return frame


def build_formula(outcome: str, terms: list[str], interaction: tuple[str, str] | None = None) -> str:
    """Assemble an R-style formula from whichever terms are available."""
    parts = []
    if interaction:
        left, right = interaction
        if left in terms and right in terms:
            parts = [f"C({left}) * C({right})"]
            terms = [t for t in terms if t not in interaction]
    parts += [f"C({t})" for t in terms]
    return f"{outcome} ~ " + " + ".join(parts)


# ---------------------------------------------------------------------------
# RQ1 - trends
# ---------------------------------------------------------------------------


def rq1_trends(frame: pd.DataFrame) -> pd.DataFrame:
    print("=" * 70)
    print("RQ1 - Casualty counts and severity proportions by mode and year")
    print("=" * 70)

    subset = frame.dropna(subset=["mode", "year"])
    counts = (
        subset.groupby(["mode", "year"], observed=True)
        .size()
        .unstack(fill_value=0)
        .reindex(MODE_ORDER)
    )
    print("\nCasualty counts by mode and year:")
    print(counts.to_string())

    records = []
    for mode in MODE_ORDER:
        for year in sorted(subset["year"].unique()):
            group = subset[(subset["mode"] == mode) & (subset["year"] == year)]
            known = group.dropna(subset=["is_kasi_num"])
            n, k = len(group), int(known["is_kasi_num"].sum())
            proportion = k / len(known) if len(known) else np.nan
            low, high = wilson_interval(k, len(known)) if len(known) else (np.nan, np.nan)
            records.append(
                {
                    "mode": mode,
                    "year": year,
                    "casualties": n,
                    "kasi": k,
                    "kasi_proportion": proportion,
                    "kasi_ci_low": low,
                    "kasi_ci_high": high,
                    "unknown_severity": int(group["is_kasi_num"].isna().sum()),
                }
            )

    table = pd.DataFrame(records)
    print("\nKASI proportion with 95% Wilson CI:")
    print(
        table[["mode", "year", "casualties", "kasi_proportion", "kasi_ci_low", "kasi_ci_high"]]
        .round(4)
        .to_string(index=False)
    )
    return table


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval — correct for proportions, unlike the normal approximation."""
    if total == 0:
        return (np.nan, np.nan)
    p = successes / total
    denominator = 1 + z**2 / total
    centre = (p + z**2 / (2 * total)) / denominator
    margin = z * np.sqrt(p * (1 - p) / total + z**2 / (4 * total**2)) / denominator
    return (max(0.0, centre - margin), min(1.0, centre + margin))


# ---------------------------------------------------------------------------
# RQ2 — spatial
# ---------------------------------------------------------------------------


def rq2_spatial(frame: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "=" * 70)
    print("RQ2 - Urban/rural distribution by mode")
    print("=" * 70)

    if "urban_or_rural_area" not in frame.columns:
        print("urban_or_rural_area not present — skipping.")
        return pd.DataFrame()

    subset = frame.dropna(subset=["mode", "urban_or_rural_area"])
    table = pd.crosstab(subset["mode"], subset["urban_or_rural_area"])
    table = table.reindex(MODE_ORDER)
    print("\nCounts:")
    print(table.to_string())

    proportions = table.div(table.sum(axis=1), axis=0)
    print("\nRow proportions:")
    print(proportions.round(4).to_string())

    if table.shape[1] == 2 and not table.empty:
        chi2, p_value, dof, _ = stats.chi2_contingency(table)
        print(f"\nChi-square test of independence: chi2={chi2:.2f}, dof={dof}, p={p_value:.3g}")
        print("Report: urban/rural mix differs by mode" if p_value < 0.05 else "Report: no evidence of a difference")
        print(
            "\nNOTE: with large n, chi-square is almost always significant. Report the\n"
            "proportions and an effect size, not just the p-value."
        )
    return table


def rq2_by_police_force(frame: pd.DataFrame) -> pd.DataFrame:
    print("\nE-scooter casualties by police force area (top 15):")
    if "police_force" not in frame.columns:
        print("police_force not present — skipping.")
        return pd.DataFrame()

    subset = frame[frame["mode"] == "escooter"]
    counts = subset["police_force"].value_counts().head(15)
    print(counts.to_string())
    return counts.to_frame("casualties")


# ---------------------------------------------------------------------------
# RQ3 / RQ4 — severity models
# ---------------------------------------------------------------------------


def prepare_model_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Coerce model inputs, add labelled categories, and drop unusable rows."""
    # Must happen before the dropna below, so kasi_adj survives on rows where the
    # raw severity is usable. Fatalities are added back inside this call.
    frame = add_adjusted_outcome(frame)

    model_frame = frame.dropna(subset=["mode", "is_kasi_num"]).copy()
    model_frame["kasi"] = model_frame["is_kasi_num"].astype(int)

    for column in MODEL_FIELDS + ["month"]:
        if column in model_frame.columns:
            model_frame[column] = pd.to_numeric(model_frame[column], errors="coerce")

    # Replace integer codes with the guide's own labels for the regression table.
    print("Adding readable category labels from the DfT data guide:")
    model_frame, label_columns = add_labelled_columns(model_frame, MODEL_FIELDS)
    for column in label_columns:
        print(f"  {column}")

    # Put the reference category first so patsy uses it as the baseline without
    # needing an explicit Treatment() in every formula.
    categories = [MODE_REFERENCE] + [m for m in MODE_ORDER if m != MODE_REFERENCE]
    model_frame["mode"] = pd.Categorical(model_frame["mode"], categories=categories)
    print(f"Model reference category: mode='{MODE_REFERENCE}'")
    return model_frame, label_columns


def check_available_terms(frame: pd.DataFrame, formula: str) -> str:
    """Drop terms whose columns are missing, so the script still runs."""
    import re

    terms = re.findall(r"C\((\w+)\)", formula)
    missing = [t for t in terms if t not in frame.columns]
    if missing:
        print(f"  [warn] dropping missing terms: {missing}")
        for term in missing:
            formula = formula.replace(f"C({term})", "")
            formula = formula.replace(f"C({term}) * ", "").replace(f" * C({term})", "")
        formula = re.sub(r"\s*\+\s*\+", " + ", formula)
        formula = re.sub(r"~\s*\+", "~ ", formula)
        formula = formula.rstrip(" +~")
    return formula


def report_reference_categories(frame: pd.DataFrame, formula: str) -> dict[str, str]:
    """Print which level each categorical predictor is compared against.

    A coefficient is uninterpretable without its baseline, and the baseline is
    chosen by patsy's ordering rules rather than by the analyst. Surfacing it here
    means the write-up cannot accidentally state the wrong reference category.
    """
    references: dict[str, str] = {}
    for column in re.findall(r"C\((\w+)\)", formula):
        if column not in frame.columns:
            continue
        if frame[column].dropna().nunique() < 2:
            continue
        references[column] = reference_level(frame[column])

    print("\nReference categories:")
    for column, level in references.items():
        print(f"  {column:34s} = {level}")
    return references


def fit_logit(frame: pd.DataFrame, formula: str, label: str, fractional: bool = False):
    """Fit and report a logistic or fractional-logit model.

    Args:
        fractional: when True the outcome is an expected probability in [0, 1]
            rather than a 0/1 flag, and a quasi-likelihood GLM with a Binomial
            family is used (the Papke-Wooldridge fractional logit). Coefficients
            are still log-odds and exp() is still a valid odds ratio.
    """
    print("\n" + "-" * 70)
    print(f"{label}" + ("  [fractional logit]" if fractional else ""))
    print(f"Formula: {formula}")
    print("-" * 70)

    formula = check_available_terms(frame, formula)
    report_reference_categories(frame, formula)

    try:
        if fractional:
            result = smf.glm(
                formula, data=frame, family=sm.families.Binomial()
            ).fit()
        else:
            result = smf.logit(formula, data=frame).fit(disp=False)
    except Exception as exc:  # noqa: BLE001 - surface any statsmodels/convergence issue
        print(f"  [error] could not fit: {exc}")
        return None, None

    # Odds ratios with 95% CI: report these, not raw coefficients.
    params = result.params
    confidence = result.conf_int()
    table = pd.DataFrame(
        {
            "odds_ratio": np.exp(params),
            "ci_low": np.exp(confidence[0]),
            "ci_high": np.exp(confidence[1]),
            "p_value": result.pvalues,
        }
    )
    table.index.name = "term"
    print(f"\nN = {int(result.nobs):,}")
    fit_stat = extract_pseudo_rsquared(result)
    if fit_stat is not None:
        stat_name = "Pseudo R-squared" if not fractional else "Pseudo R-squared (GLM)"
        print(f"{stat_name} = {fit_stat:.4f}")
    print(f"AIC = {result.aic:.1f}")
    print("\nOdds ratios (95% CI):")
    with pd.option_context("display.max_colwidth", 60):
        print(table.round(4).to_string())
    return result, table


def extract_pseudo_rsquared(result) -> float | None:
    """Pull a pseudo-R-squared out of a statsmodels result, whatever its shape.

    This is fiddly because the attribute differs by model class AND by kind:
    Logit exposes `prsquared` as a property, while GLM exposes `prsquared` as a
    METHOD and `pseudo_rsquared` as the property. Returning a bound method to a
    caller that formats it as a float raises
    `TypeError: unsupported format string passed to method.__format__`.
    So both names are tried, callables are invoked, and anything that is not a
    real number is rejected.
    """
    for attribute in ("prsquared", "pseudo_rsquared"):
        candidate = getattr(result, attribute, None)
        if candidate is None:
            continue
        if callable(candidate):
            try:
                candidate = candidate()
            except TypeError:
                continue
        if isinstance(candidate, (int, float)) and not isinstance(candidate, bool):
            return float(candidate)
    return None


def rq3_within_escooter(frame: pd.DataFrame, label_columns: list[str]):
    print("\n" + "=" * 70)
    print("RQ3 - Determinants of KASI among e-scooter casualties")
    print("=" * 70)
    subset = frame[frame["mode"] == "escooter"]
    if subset.empty:
        print("No e-scooter records - check the cohort definition.")
        return None, None
    if len(subset) < 100:
        print(f"WARNING: only {len(subset)} e-scooter records. Estimates will be unstable.")
    formula = build_formula("kasi", ["age_band"] + label_columns)
    return fit_logit(subset, formula, "Model A - within e-scooter")


def rq4_comparative(frame: pd.DataFrame, label_columns: list[str]):
    print("\n" + "=" * 70)
    print("RQ4 - Comparative severity across modes")
    print("=" * 70)
    # Speed limit is the most policy-relevant moderator, so the interaction tests
    # whether its effect on severity differs by mode.
    speed_term = next((c for c in label_columns if c.startswith("speed_limit")), None)

    formula_b = build_formula("kasi", ["mode", "age_band"] + label_columns)
    result_b, table_b = fit_logit(frame, formula_b, "Model B - pooled, mode as predictor")

    if speed_term:
        formula_c = build_formula(
            "kasi",
            ["mode", "age_band"] + label_columns,
            interaction=("mode", speed_term),
        )
        result_c, table_c = fit_logit(frame, formula_c, "Model C - mode x speed limit interaction")
    else:
        print("\n  [skip] Model C: no speed_limit label column available.")
        result_c, table_c = None, None

    return (result_b, table_b), (result_c, table_c)


def sensitivity_excluding_unknowns(frame: pd.DataFrame, label_columns: list[str]):
    print("\n" + "=" * 70)
    print("Sensitivity - e-scooter model excluding unknown-severity records")
    print("=" * 70)
    subset = frame[(frame["mode"] == "escooter") & (frame["is_kasi_num"].notna())]
    formula = build_formula("kasi", ["age_band"] + label_columns)
    return fit_logit(subset, formula, "Model A (known severity only)")


def sensitivity_alternative_definition(frame: pd.DataFrame, label_columns: list[str]) -> None:
    """Compare the casualty flag against the vehicle_type code as cohort definition.

    The two definitions agree on every flagged record but vehicle_type == 33
    additionally captures 115 vehicles the flag does not. This quantifies whether
    that difference matters for the findings.
    """
    print("\n" + "=" * 70)
    print("Sensitivity - alternative cohort definition (vehicle_type == 33)")
    print("=" * 70)

    flag = pd.to_numeric(frame.get("casualty_escooter_flag"), errors="coerce")
    vehicle_type = pd.to_numeric(frame["vehicle_type"], errors="coerce")

    by_flag = int((flag == 1).sum())
    by_type = int((vehicle_type == VEHICLE_TYPE_PPT).sum())
    print(f"  Casualties on an e-scooter by casualty flag : {by_flag:>7,}")
    print(f"  Casualties on vehicle_type == {VEHICLE_TYPE_PPT}   : {by_type:>7,}")
    print(f"  Difference                                : {by_type - by_flag:>7,}")
    print(
        "\n  If the difference is small relative to the cohort, report that the\n"
        "  choice of definition does not materially affect the results."
    )

    alternative = frame.copy()
    alternative.loc[vehicle_type == VEHICLE_TYPE_PPT, "mode"] = "escooter"
    alternative = alternative.dropna(subset=["is_kasi_num"])
    alternative["kasi"] = alternative["is_kasi_num"].astype(int)
    subset = alternative[alternative["mode"] == "escooter"]
    formula = build_formula("kasi", ["age_band"] + label_columns)
    fit_logit(subset, formula, "Model A (cohort = vehicle_type 33)")


# ---------------------------------------------------------------------------
# Injury-based reporting (IBR) sensitivity analysis
#
# Some police forces moved from the traditional severity judgement to
# injury-based reporting, which changed how severity is recorded. Adoption grew
# from 51.7% of casualties in 2021 to 86.4% in 2025, so the composition of the
# data shifts markedly across the study period. A rising severity trend could
# therefore be partly an artefact of who was recording it.
#
# The DfT publishes its own severity adjustment for this. These three analyses
# test whether the central findings survive it, and the disclosure of a
# regulatory change in the data is exactly what a reviewer will ask about.
# ---------------------------------------------------------------------------


def ibr_adoption_by_year(frame: pd.DataFrame) -> pd.DataFrame:
    """Report the IBR share per year, and adjusted vs raw KASI by mode and year."""
    print("\n" + "=" * 70)
    print("IBR - Adoption of injury-based reporting over the study period")
    print("=" * 70)

    if COL_INJURY_BASED not in frame.columns:
        print(f"  '{COL_INJURY_BASED}' not present - cannot run the IBR analysis.")
        return pd.DataFrame()

    working = frame.dropna(subset=["mode", "year"]).copy()
    working["is_fatal"] = (
        pd.to_numeric(working["casualty_severity"], errors="coerce") == SEVERITY_FATAL
    ).astype(int)
    working["is_kasi_num"] = pd.to_numeric(working["is_kasi"], errors="coerce")

    by_year = working.groupby("year").agg(
        casualties=("mode", "size"),
        ibr_pct=(COL_INJURY_BASED, lambda s: 100 * pd.to_numeric(s, errors="coerce").mean()),
    )
    print("\nShare of casualties from IBR forces, by year:")
    print(by_year.round(1).to_string())
    print(
        "\n  A near-monotonic rise means raw year-on-year severity comparisons are\n"
        "  confounded by the recording method. That must be stated in the paper."
    )

    records = []
    for mode in MODE_ORDER:
        for year in sorted(working["year"].unique()):
            group = working[(working["mode"] == mode) & (working["year"] == year)]
            if group.empty:
                continue
            known = group.dropna(subset=["is_kasi_num"])
            adjusted = group["kasi_adj"].dropna() if "kasi_adj" in group else pd.Series(dtype=float)
            records.append(
                {
                    "mode": mode,
                    "year": year,
                    "casualties": len(group),
                    "kasi_raw": known["is_kasi_num"].mean() if len(known) else np.nan,
                    "kasi_adjusted": adjusted.mean() if len(adjusted) else np.nan,
                    "ibr_pct": 100 * pd.to_numeric(group[COL_INJURY_BASED], errors="coerce").mean(),
                }
            )

    comparison = pd.DataFrame(records)
    comparison["difference"] = comparison["kasi_adjusted"] - comparison["kasi_raw"]
    print("\nRaw vs DfT severity-adjusted KASI proportion by mode and year:")
    print(comparison.round(4).to_string(index=False))
    return comparison


def ibr_adjusted_model(frame: pd.DataFrame, label_columns: list[str]):
    """Refit the comparative model using the severity-adjusted fractional outcome.

    This is the key test: if the e-scooter odds ratio holds under the DfT's own
    severity adjustment, the finding is not an artefact of reporting method.
    """
    print("\n" + "=" * 70)
    print("IBR - Comparative model refitted on the severity-adjusted outcome")
    print("=" * 70)

    if "kasi_adj" not in frame.columns:
        print("  'kasi_adj' not available - run add_adjusted_outcome first.")
        return None, None

    subset = frame.dropna(subset=["kasi_adj", "mode"]).copy()
    formula = build_formula("kasi_adj", ["mode", "age_band"] + label_columns)
    return fit_logit(
        subset, formula, "Model B (DfT severity-adjusted outcome)", fractional=True
    )


def ibr_restricted_to_ibr_forces(frame: pd.DataFrame, label_columns: list[str]):
    """Refit the comparative model using only injury-based-reporting forces.

    A cleaner but smaller subsample: within IBR forces the recording method is
    consistent, so any remaining difference between modes is not attributable to
    the method. The trade-off is reduced power and a changing set of forces over
    time, both of which belong in the limitations.
    """
    print("\n" + "=" * 70)
    print("IBR - Comparative model restricted to injury-based-reporting forces")
    print("=" * 70)

    if COL_INJURY_BASED not in frame.columns:
        print(f"  '{COL_INJURY_BASED}' not present - skipping.")
        return None, None

    injury_based = pd.to_numeric(frame[COL_INJURY_BASED], errors="coerce")
    subset = frame[(injury_based == 1) & frame["is_kasi_num"].notna()].copy()
    print(f"  Records from IBR forces: {len(subset):,} of {len(frame):,}")

    modes = subset["mode"].value_counts()
    print("  Cohort sizes by mode:")
    for mode in MODE_ORDER:
        print(f"    {mode:12s} {int(modes.get(mode, 0)):>8,}")
    if subset[subset["mode"] == "escooter"].shape[0] < 500:
        print("  [warn] small e-scooter subset; expect wide confidence intervals.")

    subset["kasi"] = subset["is_kasi_num"].astype(int)
    formula = build_formula("kasi", ["mode", "age_band"] + label_columns)
    return fit_logit(subset, formula, "Model B (IBR forces only)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def save_table(table: pd.DataFrame, name: str) -> None:
    if table is None or table.empty:
        return
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{name}.csv"
    table.to_csv(path)
    print(f"  saved -> {path}")


def table1_descriptives(frame: pd.DataFrame) -> pd.DataFrame:
    """Table 1: characteristics of casualties by mode.

    Every empirical paper needs a Table 1, and its purpose is to let a reader
    judge whether the groups are comparable before trusting any model. Report
    counts, proportions and medians rather than means where distributions are
    skewed, and include the unknowns so nothing is hidden.
    """
    print("\n" + "=" * 70)
    print("Table 1 - Characteristics of casualties by mode")
    print("=" * 70)

    subset = frame[frame["mode"].isin(MODE_ORDER)]
    rows = []
    for mode in MODE_ORDER:
        group = subset[subset["mode"] == mode]
        if group.empty:
            continue
        age = pd.to_numeric(group["age"], errors="coerce")
        severity = pd.to_numeric(group["casualty_severity"], errors="coerce")
        known = pd.to_numeric(group["is_kasi_num"], errors="coerce").dropna()
        sex = pd.to_numeric(group["sex_of_casualty"], errors="coerce")
        urban = pd.to_numeric(group["urban_or_rural_area"], errors="coerce")

        rows.append(
            {
                "mode": mode,
                "n": len(group),
                "age_median": age.median(),
                "age_iqr_low": age.quantile(0.25),
                "age_iqr_high": age.quantile(0.75),
                "age_unknown_pct": 100 * age.isna().mean(),
                "male_pct": 100 * (sex == 1).mean(),
                "female_pct": 100 * (sex == 2).mean(),
                "sex_unknown_pct": 100 * sex.isna().mean(),
                "urban_pct": 100 * (urban == 1).mean(),
                "kasi_pct": 100 * known.mean() if len(known) else np.nan,
                "kasi_unknown_pct": 100 * pd.to_numeric(
                    group["is_kasi_num"], errors="coerce"
                ).isna().mean(),
                "fatal_pct": 100 * (severity == SEVERITY_FATAL).mean(),
                "serious_pct": 100 * (severity == SEVERITY_SERIOUS).mean(),
                "slight_pct": 100 * (severity == SEVERITY_SLIGHT).mean(),
            }
        )

    table = pd.DataFrame(rows).set_index("mode")
    print("\n" + table.round(2).to_string())
    print(
        "\n  Report this as Table 1. The 'unknown' columns matter: they show the\n"
        "  reader exactly how much of each variable is missing, per mode."
    )
    return table


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    frame = prepare_analysis_frame()
    frame = add_adjusted_outcome(frame)

    stats_table = table1_descriptives(frame)
    save_table(stats_table, "table1_descriptives")

    trends = rq1_trends(frame)
    save_table(trends, "rq1_trends")

    urban = rq2_spatial(frame)
    save_table(urban, "rq2_urban_rural")
    rq2_by_police_force(frame)

    model_frame, label_columns = prepare_model_frame(frame)
    print(f"\nModellable records: {len(model_frame):,}")
    print(describe_label_source())

    _, table_a = rq3_within_escooter(model_frame, label_columns)
    save_table(table_a, "rq3_model_a_within_escooter")

    comparative = rq4_comparative(model_frame, label_columns)
    if comparative[0][1] is not None:
        save_table(comparative[0][1], "rq4_model_b_comparative")
    if comparative[1][1] is not None:
        save_table(comparative[1][1], "rq4_model_c_interaction")

    _, table_s = sensitivity_excluding_unknowns(model_frame, label_columns)
    save_table(table_s, "sensitivity_known_severity")

    sensitivity_alternative_definition(frame, label_columns)

    # Injury-based reporting: the confound a reviewer will ask about, and the one
    # most likely to undermine the rising-severity finding.
    ibr_table = ibr_adoption_by_year(frame)
    save_table(ibr_table, "sensitivity_ibr_adoption")

    _, table_adj = ibr_adjusted_model(model_frame, label_columns)
    save_table(table_adj, "sensitivity_ibr_adjusted_outcome")

    _, table_ibr = ibr_restricted_to_ibr_forces(model_frame, label_columns)
    save_table(table_ibr, "sensitivity_ibr_forces_only")

    print("\n" + "=" * 70)
    print("Reminder for the write-up:")
    print("  - Report odds ratios with 95% CI, never p-values alone.")
    print("  - State the reference category for every categorical predictor.")
    print(f"  - Mode reference category is '{MODE_REFERENCE}'.")
    print("  - Report the proportion of unknown values dropped by each model.")
    print("  - Model fit here is pseudo-R-squared and AIC; do not claim causality.")
    print("  - Report the three sensitivity analyses explicitly, including the IBR one.")
    print("  - State whether the e-scooter odds ratio survives IBR adjustment. ")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
