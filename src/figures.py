"""
Publication figures for the e-scooter casualty study.

Run AFTER analysis.py so the derived fields and outputs exist.

Produces, in outputs/figures/:
  fig1_trends.png          Casualty counts by mode and year (RQ1)
  fig2_kasi_proportion.png KASI proportion with 95% CI by mode and year (RQ1)
  fig3_age_sex.png         Age and sex distribution by mode
  fig4_urban_rural.png     Urban/rural split by mode (RQ2)
  fig5_odds_ratios.png     Forest plot of Model B odds ratios (RQ4)

Journal-ready defaults: 300 dpi, no chartjunk, greyscale-safe palette so the
figures survive being printed in black and white.

Usage:
    python src/figures.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: no display needed

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dataset import prepare_analysis_frame

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"
FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"

MODES = ["escooter", "pedal_cycle", "motorcycle"]
LABELS = {
    "escooter": "E-scooter",
    "pedal_cycle": "Pedal cycle",
    "motorcycle": "Motorcycle",
}
# Greyscale-safe: distinguishable when printed without colour.
STYLES = {
    "escooter": {"color": "#000000", "linestyle": "-", "marker": "o"},
    "pedal_cycle": {"color": "#555555", "linestyle": "--", "marker": "s"},
    "motorcycle": {"color": "#999999", "linestyle": ":", "marker": "^"},
}

plt.rcParams.update(
    {
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "font.size": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linewidth": 0.5,
        "legend.frameon": False,
    }
)


def save(fig: plt.Figure, name: str) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / name
    fig.savefig(path)
    plt.close(fig)
    print(f"  saved -> {path}")


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the classified dataset and the RQ1 trend table.

    Uses dataset.prepare_analysis_frame so figure groupings come from exactly the
    same mode definition as the tables. Reading analysis_dataset.csv directly would
    leave the frame without a 'mode' column, which is how this function first broke.
    """
    trends_path = TABLES_DIR / "rq1_trends.csv"
    if not trends_path.exists():
        raise SystemExit(
            "Missing inputs. Run in order:\n"
            "  python src/prepare_data.py\n"
            "  python src/analysis.py"
        )
    return prepare_analysis_frame(verbose=False), pd.read_csv(trends_path)


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------


def fig1_trends(trends: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(5.5, 3.4))
    for mode in MODES:
        subset = trends[trends["mode"] == mode].sort_values("year")
        if subset.empty:
            continue
        ax.plot(subset["year"], subset["casualties"], label=LABELS[mode], **STYLES[mode])
    ax.set_xlabel("Year")
    ax.set_ylabel("Casualties")
    ax.set_title("Reported casualties by mode")
    ax.legend()
    ax.set_xticks(sorted(trends["year"].unique()))
    save(fig, "fig1_trends.png")


def fig2_kasi_proportion(trends: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(5.5, 3.4))
    for mode in MODES:
        subset = trends[trends["mode"] == mode].sort_values("year")
        if subset.empty:
            continue
        style = STYLES[mode]
        ax.plot(subset["year"], subset["kasi_proportion"], label=LABELS[mode], **style)
        ax.fill_between(
            subset["year"],
            subset["kasi_ci_low"],
            subset["kasi_ci_high"],
            color=style["color"],
            alpha=0.12,
            linewidth=0,
        )
    ax.set_xlabel("Year")
    ax.set_ylabel("Proportion killed or seriously injured")
    ax.set_title("KASI proportion with 95% confidence intervals")
    ax.legend()
    ax.set_xticks(sorted(trends["year"].unique()))
    save(fig, "fig2_kasi_proportion.png")


def fig3_age_sex(frame: pd.DataFrame) -> None:
    if "age_band" not in frame.columns or "sex_of_casualty" not in frame.columns:
        print("  [skip] fig3: age_band or sex_of_casualty missing")
        return

    subset = frame[frame["mode"].isin(MODES)].copy()
    subset["sex_label"] = pd.to_numeric(subset["sex_of_casualty"], errors="coerce").map(
        {1: "Male", 2: "Female"}
    )
    subset = subset.dropna(subset=["age_band", "sex_label"])
    if subset.empty:
        print("  [skip] fig3: no plottable rows")
        return

    fig, axes = plt.subplots(1, 3, figsize=(9, 3.2), sharey=True)
    for ax, mode in zip(axes, MODES):
        group = subset[subset["mode"] == mode]
        if group.empty:
            ax.set_visible(False)
            continue
        counts = pd.crosstab(group["age_band"], group["sex_label"], normalize="columns")
        counts = counts.reindex(
            ["0-15", "16-24", "25-34", "35-44", "45-54", "55-64", "65+"]
        )
        counts.plot(kind="bar", ax=ax, color=["#777777", "#111111"], width=0.8)
        ax.set_title(LABELS[mode])
        ax.set_xlabel("Age band")
        ax.tick_params(axis="x", rotation=45)
        ax.legend(title="", fontsize=7)
    axes[0].set_ylabel("Proportion within sex")
    save(fig, "fig3_age_sex.png")


def fig4_urban_rural(frame: pd.DataFrame) -> None:
    if "urban_or_rural_area" not in frame.columns:
        print("  [skip] fig4: urban_or_rural_area missing")
        return

    subset = frame[frame["mode"].isin(MODES)].dropna(subset=["urban_or_rural_area"])
    if subset.empty:
        print("  [skip] fig4: no plottable rows")
        return

    table = pd.crosstab(subset["mode"], subset["urban_or_rural_area"], normalize="index")
    table = table.reindex(MODES)

    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    table.plot(kind="barh", stacked=True, ax=ax, color=["#111111", "#aaaaaa"])
    ax.set_yticklabels([LABELS.get(m, m) for m in table.index])
    ax.set_xlabel("Proportion of casualties")
    ax.set_ylabel("")
    ax.set_title("Urban / rural distribution by mode")
    ax.legend(title="", loc="lower right")
    save(fig, "fig4_urban_rural.png")


def fig5_odds_ratios() -> None:
    path = TABLES_DIR / "rq4_model_b_comparative.csv"
    if not path.exists():
        print("  [skip] fig5: rq4_model_b_comparative.csv not found")
        return

    table = pd.read_csv(path, index_col=0)
    table = table.dropna(subset=["odds_ratio", "ci_low", "ci_high"])
    # Exclude the intercept and drop very wide CIs that squash the plot.
    table = table[~table.index.str.contains("Intercept", case=False)]
    table = table[(table["ci_low"] > 0) & (table["ci_high"] < 100)]
    if table.empty:
        print("  [skip] fig5: nothing to plot after filtering")
        return

    table = table.sort_values("odds_ratio")
    y = np.arange(len(table))

    fig, ax = plt.subplots(figsize=(6.0, max(3.0, 0.28 * len(table))))
    ax.errorbar(
        table["odds_ratio"],
        y,
        xerr=[
            table["odds_ratio"] - table["ci_low"],
            table["ci_high"] - table["odds_ratio"],
        ],
        fmt="o",
        color="#111111",
        ecolor="#666666",
        capsize=2,
        markersize=4,
        linewidth=1,
    )
    ax.axvline(1.0, color="#999999", linestyle="--", linewidth=1)
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels([str(i) for i in table.index], fontsize=7)
    ax.set_xlabel("Odds ratio (log scale)")
    ax.set_title("Adjusted odds ratios for KASI\n(95% CI, model B)")
    ax.grid(axis="x", alpha=0.25)
    ax.grid(axis="y", visible=False)
    save(fig, "fig5_odds_ratios.png")


def fig6_ibr_robustness() -> None:
    """Compare the headline e-scooter odds ratio across the IBR specifications.

    This is the paper's strongest single result: the estimate barely moves when the
    reporting-method change is corrected for, or when the analysis is restricted to
    uniformly-recording forces. Showing the three side by side in one panel makes
    that robustness visible rather than asking a reader to compare numbers across
    three separate tables.
    """
    sources = [
        ("rq4_model_b_comparative.csv", "Raw outcome"),
        ("sensitivity_ibr_adjusted_outcome.csv", "Severity-adjusted outcome"),
        ("sensitivity_ibr_forces_only.csv", "Injury-based-reporting forces only"),
    ]

    records = []
    for filename, label in sources:
        path = TABLES_DIR / filename
        if not path.exists():
            print(f"  [skip] fig6: {filename} not found")
            return
        table = pd.read_csv(path, index_col=0)
        for mode in ("escooter", "motorcycle"):
            match = table.index[table.index.str.contains(fr"T\.{mode}\]", regex=True, na=False)]
            if len(match) == 0:
                continue
            row = table.loc[match[0]]
            records.append(
                {
                    "specification": label,
                    "mode": mode,
                    "odds_ratio": float(row["odds_ratio"]),
                    "ci_low": float(row["ci_low"]),
                    "ci_high": float(row["ci_high"]),
                }
            )

    if not records:
        print("  [skip] fig6: no mode terms found in the saved tables")
        return

    data = pd.DataFrame(records)
    # Must collect the LABELS, not the filenames: `data["specification"]` holds
    # labels, so comparing it against `s` (a filename) selects nothing and yields
    # an empty axis with no error. Guard against that explicitly below.
    present = set(data["specification"])
    specs = [label for _, label in sources if label in present]
    if not specs:
        print(
            "  [skip] fig6: specification labels did not match the saved tables "
            f"(found {sorted(present)})"
        )
        return
    modes = ["escooter", "motorcycle"]

    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    offsets = {"escooter": 0.16, "motorcycle": -0.16}
    styles = {
        "escooter": {"color": "#000000", "marker": "o", "label": "E-scooter"},
        "motorcycle": {"color": "#888888", "marker": "s", "label": "Motorcycle"},
    }

    for mode in modes:
        group = data[data["mode"] == mode].set_index("specification")
        ys, xs, lows, highs = [], [], [], []
        for index, spec in enumerate(specs):
            if spec not in group.index:
                continue
            row = group.loc[spec]
            ys.append(index + offsets[mode])
            xs.append(row["odds_ratio"])
            lows.append(row["odds_ratio"] - row["ci_low"])
            highs.append(row["ci_high"] - row["odds_ratio"])
        if not xs:
            continue
        style = styles[mode]
        ax.errorbar(
            xs, ys, xerr=[lows, highs], fmt=style["marker"],
            color=style["color"], ecolor=style["color"], capsize=2,
            markersize=5, linewidth=1, label=style["label"],
        )

    ax.axvline(1.0, color="#999999", linestyle="--", linewidth=1)
    ax.set_yticks(range(len(specs)))
    ax.set_yticklabels([s.replace(" only", "\nonly") for s in specs], fontsize=8)
    ax.set_xlabel("Odds ratio for KASI vs pedal cycling (95% CI)")
    ax.set_title("Robustness of the mode effect to section-recording changes")
    # Lower-left is the only region with no data points at this x-range.
    ax.legend(title="", loc="lower left", ncols=2)
    ax.grid(axis="x", alpha=0.25)
    ax.grid(axis="y", visible=False)
    # Headroom so the top-most CI does not collide with the plot border.
    lower, upper = ax.get_xlim()
    ax.set_xlim(lower, upper + 0.06 * (upper - lower))
    save(fig, "fig6_ibr_robustness.png")


def main() -> int:
    print("=== Figures ===\n")
    frame, trends = load_data()

    fig1_trends(trends)
    fig2_kasi_proportion(trends)
    fig3_age_sex(frame)
    fig4_urban_rural(frame)
    fig5_odds_ratios()
    fig6_ibr_robustness()

    print("\nDone. Figures are 300 dpi and greyscale-safe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
