from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_report_assets(report_dir: Path, summary: pd.DataFrame, pareto: pd.DataFrame, mode: str) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    variant = "paired_antithetic" if "paired_antithetic" in set(summary["variant"]) else "standard"
    data = summary[summary["variant"] == variant].sort_values("objective_mean")

    (report_dir / "report_outline.md").write_text(REPORT_OUTLINE, encoding="utf-8")
    (report_dir / "methodology_draft.md").write_text(METHODOLOGY_DRAFT.format(mode=mode), encoding="utf-8")
    (report_dir / "figure_captions.md").write_text(FIGURE_CAPTIONS, encoding="utf-8")

    if data.empty:
        results_text = "No simulation results were generated yet.\n"
        latex_tables = "% No simulation results were generated yet.\n"
    else:
        best = data.iloc[0]
        unstable = data[data["unstable_flag"] == True]  # noqa: E712
        top_table = data.head(10)[
            [
                "design_id",
                "objective_mean",
                "objective_half_width",
                "elective_appointment_wait_hours_mean",
                "urgent_scan_wait_hours_mean",
                "daily_overtime_hours_mean",
                "unstable_flag",
            ]
        ]
        results_text = (
            "# Results Draft\n\n"
            f"Mode: `{mode}`. Numerical values are generated from the latest pipeline run.\n\n"
            f"The best point estimate in this run is `{best['design_id']}` with objective "
            f"{best['objective_mean']:.4f}. The 95% confidence interval half-width is "
            f"{best['objective_half_width']:.4f}. This should be interpreted with the paired "
            "confidence intervals and secondary objectives before claiming a final optimum.\n\n"
            f"Designs flagged as unstable or precision-problematic: {len(unstable)}.\n\n"
            "## Top Designs\n\n"
            + dataframe_to_markdown(top_table)
            + "\n\n## Pareto Designs\n\n"
            + (dataframe_to_markdown(pareto.head(20)) if not pareto.empty else "No Pareto rows available.")
            + "\n"
        )
        latex_tables = dataframe_to_latex(top_table)

    (report_dir / "results_draft.md").write_text(results_text, encoding="utf-8")
    (report_dir / "latex_tables.tex").write_text(latex_tables, encoding="utf-8")


REPORT_OUTLINE = """# Report Outline

1. Introduction and hypotheses
2. System description and input data
3. Factors, responses, and objective hierarchy
4. Simulation model: state descriptor, event logic, and time handling
5. Experimental design and variance reduction
6. Output analysis: warm-up, batch means, precision
7. Screening and statistical comparison
8. Pareto trade-off between elective and urgent waiting
9. Secondary objectives, limitations, and conclusion
"""

METHODOLOGY_DRAFT = """# Methodology Draft

This `{mode}` run evaluates a long-run cyclic steady-state policy, not a one-day terminating system. The weekly slot pattern repeats, elective appointment backlog may carry over between weeks, and output analysis therefore uses whole-week warm-up and whole-week batch means.

The experiment uses common random numbers by deriving stream seeds from the base seed, replication index, and stream name. Separate streams are used for elective calls, urgent arrivals, no-shows, punctuality, elective durations, urgent scan type, and urgent durations. Antithetic runs reuse the same stream seeds and replace each generated uniform variate `U` by `1-U` before inverse-transform sampling.

The full confirmatory design covers all assignment-required urgent slot counts from 10 through 20 for all three timing strategies and four appointment rules. Counts 18-20 are evaluated and may only be marked unstable after the output analysis indicates excessive waiting growth, poor precision, or saturation.
"""

FIGURE_CAPTIONS = """# Figure Captions

- `welch_plot.png`: Welch-style moving average of the weekly objective after applying the run's selected estimator.
- `autocorrelation_plot.png`: Autocorrelation of the weekly objective used to justify whole-week batch size.
- `objective_by_urgent.png`: Best objective value by urgent slot count and timing strategy.
- `pareto_front.png`: Non-dominated trade-off between elective appointment waiting time and urgent scan waiting time.
- `schedule_*.png`: Weekly schedule heatmaps; darker cells indicate urgent slots.
"""


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows available._"
    columns = list(frame.columns)
    lines = [
        "| " + " | ".join(str(column) for column in columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in frame.iterrows():
        values = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                values.append(f"{value:.6g}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def dataframe_to_latex(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "% No rows available.\n"
    columns = list(frame.columns)
    alignment = "l" * len(columns)
    lines = [
        "\\begin{tabular}{" + alignment + "}",
        "\\toprule",
        " & ".join(_latex_escape(str(column)) for column in columns) + r" \\",
        "\\midrule",
    ]
    for _, row in frame.iterrows():
        values = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                values.append(f"{value:.4f}")
            else:
                values.append(_latex_escape(str(value)))
        lines.append(" & ".join(values) + r" \\")
    lines.extend(["\\bottomrule", "\\end{tabular}", ""])
    return "\n".join(lines)


def _latex_escape(value: str) -> str:
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value
