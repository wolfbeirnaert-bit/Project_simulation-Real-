from __future__ import annotations

from itertools import product
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd
from scipy import stats


METRIC_COLUMNS = [
    "objective",
    "elective_appointment_wait_hours_mean",
    "elective_scan_wait_hours_mean",
    "urgent_scan_wait_hours_mean",
    "daily_overtime_hours_mean",
]


def build_design_matrix(strategies: Iterable[int], urgent_slots: Iterable[int], rules: Iterable[int]) -> pd.DataFrame:
    rows = []
    for strategy, urgent, rule in product(strategies, urgent_slots, rules):
        rows.append(
            {
                "design_id": f"S{strategy}-U{urgent}-R{rule}",
                "strategy": strategy,
                "urgent_slots": urgent,
                "appointment_rule": rule,
            }
        )
    return pd.DataFrame(rows)


def pair_antithetic_weekly(weekly: pd.DataFrame) -> pd.DataFrame:
    key_cols = ["design_id", "strategy", "urgent_slots", "appointment_rule", "replication", "week"]
    standard = weekly[weekly["variant"] == "standard"].copy()
    anti = weekly[weekly["variant"] == "antithetic"].copy()
    if standard.empty or anti.empty:
        return standard
    merged = standard.merge(anti, on=key_cols, suffixes=("_std", "_anti"))
    rows = merged[key_cols].copy()
    rows["variant"] = "paired_antithetic"
    for column in METRIC_COLUMNS + [
        "elective_appointment_wait_days_mean",
        "daily_overtime_hours_total",
        "elective_calls",
        "elective_scans",
        "urgent_scans",
    ]:
        rows[column] = (merged[f"{column}_std"] + merged[f"{column}_anti"]) / 2.0
    return rows[
        ["design_id", "strategy", "urgent_slots", "appointment_rule", "replication", "variant", "week"]
        + [
            "elective_appointment_wait_hours_mean",
            "elective_appointment_wait_days_mean",
            "elective_scan_wait_hours_mean",
            "urgent_scan_wait_hours_mean",
            "daily_overtime_hours_mean",
            "daily_overtime_hours_total",
            "elective_calls",
            "elective_scans",
            "urgent_scans",
            "objective",
        ]
    ]


def compute_batch_results(weekly: pd.DataFrame, warmup_weeks: int, batch_size_weeks: int, batches: int) -> pd.DataFrame:
    post = weekly[weekly["week"] >= warmup_weeks].copy()
    post["batch"] = ((post["week"] - warmup_weeks) // batch_size_weeks).astype(int)
    post = post[post["batch"] < batches]
    group_cols = ["design_id", "strategy", "urgent_slots", "appointment_rule", "replication", "variant", "batch"]
    return post.groupby(group_cols, as_index=False)[METRIC_COLUMNS].mean()


def summarize_batches(batch_results: pd.DataFrame, weekly: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    rows = []
    group_cols = ["design_id", "strategy", "urgent_slots", "appointment_rule", "variant"]
    for keys, group in batch_results.groupby(group_cols):
        design_id, strategy, urgent_slots, appointment_rule, variant = keys
        n = len(group)
        mean = float(group["objective"].mean())
        std = float(group["objective"].std(ddof=1)) if n > 1 else 0.0
        se = std / np.sqrt(n) if n else 0.0
        t_crit = float(stats.t.ppf(0.975, n - 1)) if n > 1 else 0.0
        half_width = t_crit * se
        rel_precision = half_width / mean if mean else np.nan
        row = {
            "design_id": design_id,
            "strategy": int(strategy),
            "urgent_slots": int(urgent_slots),
            "appointment_rule": int(appointment_rule),
            "variant": variant,
            "batches": n,
            "objective_mean": mean,
            "objective_std": std,
            "objective_se": se,
            "objective_half_width": half_width,
            "objective_ci_low": mean - half_width,
            "objective_ci_high": mean + half_width,
            "objective_cv": std / mean if mean else np.nan,
            "objective_rel_precision": rel_precision,
        }
        for metric in METRIC_COLUMNS:
            row[metric] = float(group[metric].mean())
        row["unstable_flag"] = _unstable_flag(row, weekly)
        rows.append(row)
    return pd.DataFrame(rows).sort_values("objective_mean").reset_index(drop=True)


def variance_reduction_summary(batch_results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for design_id, group in batch_results.groupby("design_id"):
        standard = group[group["variant"] == "standard"]["objective"]
        paired = group[group["variant"] == "paired_antithetic"]["objective"]
        if len(standard) < 2 or len(paired) < 2:
            continue
        var_standard = float(standard.var(ddof=1))
        var_paired = float(paired.var(ddof=1))
        rows.append(
            {
                "design_id": design_id,
                "standard_variance": var_standard,
                "paired_antithetic_variance": var_paired,
                "variance_ratio_paired_over_standard": var_paired / var_standard if var_standard else np.nan,
                "variance_reduction_pct": 100.0 * (1.0 - var_paired / var_standard) if var_standard else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values("design_id")


def factor_effects(summary: pd.DataFrame) -> pd.DataFrame:
    data = summary[summary["variant"].isin(["paired_antithetic", "standard"])].copy()
    if "paired_antithetic" in set(data["variant"]):
        data = data[data["variant"] == "paired_antithetic"]
    rows: List[Dict[str, object]] = []
    overall = float(data["objective_mean"].mean())
    for factor in ["strategy", "urgent_slots", "appointment_rule"]:
        for level, group in data.groupby(factor):
            rows.append(
                {
                    "factor": factor,
                    "level": level,
                    "n_designs": len(group),
                    "mean_objective": float(group["objective_mean"].mean()),
                    "effect_vs_grand_mean": float(group["objective_mean"].mean() - overall),
                }
            )
    effects = pd.DataFrame(rows)
    try:
        import statsmodels.formula.api as smf
        import statsmodels.api as sm

        model = smf.ols(
            "objective_mean ~ C(strategy) + urgent_slots + C(appointment_rule) + C(strategy):urgent_slots",
            data=data,
        ).fit()
        anova = sm.stats.anova_lm(model, typ=2).reset_index().rename(columns={"index": "term"})
        anova["factor"] = "ANOVA"
        anova["level"] = anova["term"]
        anova["n_designs"] = len(data)
        anova["mean_objective"] = np.nan
        anova["effect_vs_grand_mean"] = np.nan
        return pd.concat([effects, anova[effects.columns]], ignore_index=True)
    except Exception as exc:  # pragma: no cover - exercised only when statsmodels is absent/broken.
        effects["note"] = f"statsmodels ANOVA unavailable: {exc}"
        return effects


def top_designs_comparison(batch_results: pd.DataFrame, summary: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    variant = "paired_antithetic" if "paired_antithetic" in set(batch_results["variant"]) else "standard"
    summary_variant = summary[summary["variant"] == variant].sort_values("objective_mean")
    if summary_variant.empty:
        return pd.DataFrame()
    best = summary_variant.iloc[0]
    best_batches = _design_batch_series(batch_results, best["design_id"], variant)
    rows = []
    for _, candidate in summary_variant.head(top_n).iterrows():
        candidate_batches = _design_batch_series(batch_results, candidate["design_id"], variant)
        merged = best_batches.merge(candidate_batches, on="batch", suffixes=("_best", "_candidate"))
        if len(merged) > 1:
            diff = merged["objective_candidate"] - merged["objective_best"]
            t_stat, p_value = stats.ttest_1samp(diff, popmean=0.0)
            diff_mean = float(diff.mean())
            diff_half_width = float(stats.t.ppf(0.975, len(diff) - 1) * diff.std(ddof=1) / np.sqrt(len(diff)))
        else:
            p_value = np.nan
            diff_mean = np.nan
            diff_half_width = np.nan
        rows.append(
            {
                "best_design": best["design_id"],
                "candidate_design": candidate["design_id"],
                "candidate_objective_mean": candidate["objective_mean"],
                "paired_difference_vs_best": diff_mean,
                "difference_half_width": diff_half_width,
                "paired_t_p_value": p_value,
                "statistically_distinguishable_from_best": bool(
                    pd.notna(p_value) and p_value < 0.05 and diff_mean > 0
                ),
            }
        )
    return pd.DataFrame(rows)


def pareto_front(summary: pd.DataFrame) -> pd.DataFrame:
    variant = "paired_antithetic" if "paired_antithetic" in set(summary["variant"]) else "standard"
    data = summary[summary["variant"] == variant].copy()
    data = data.sort_values(["elective_appointment_wait_hours_mean", "urgent_scan_wait_hours_mean"])
    non_dominated = []
    for idx, row in data.iterrows():
        dominated = (
            (data["elective_appointment_wait_hours_mean"] <= row["elective_appointment_wait_hours_mean"])
            & (data["urgent_scan_wait_hours_mean"] <= row["urgent_scan_wait_hours_mean"])
            & (
                (data["elective_appointment_wait_hours_mean"] < row["elective_appointment_wait_hours_mean"])
                | (data["urgent_scan_wait_hours_mean"] < row["urgent_scan_wait_hours_mean"])
            )
        ).any()
        if not dominated:
            non_dominated.append(idx)
    front = data.loc[non_dominated].copy().sort_values("elective_appointment_wait_hours_mean")
    front["pareto_rank"] = range(1, len(front) + 1)
    return front


def welch_curve(weekly: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    variant = "paired_antithetic" if "paired_antithetic" in set(weekly["variant"]) else "standard"
    data = weekly[weekly["variant"] == variant].groupby("week", as_index=False)["objective"].mean()
    data["welch_moving_average"] = data["objective"].rolling(window=window, center=True, min_periods=1).mean()
    return data


def autocorrelation(values: Iterable[float], max_lag: int = 50) -> pd.DataFrame:
    x = np.asarray(list(values), dtype=float)
    if len(x) < 3:
        return pd.DataFrame({"lag": [], "autocorrelation": []})
    x = x - x.mean()
    denom = np.dot(x, x)
    rows = []
    for lag in range(1, min(max_lag, len(x) - 1) + 1):
        rows.append({"lag": lag, "autocorrelation": float(np.dot(x[:-lag], x[lag:]) / denom) if denom else 0.0})
    return pd.DataFrame(rows)


def _design_batch_series(batch_results: pd.DataFrame, design_id: str, variant: str) -> pd.DataFrame:
    return batch_results[
        (batch_results["design_id"] == design_id) & (batch_results["variant"] == variant)
    ][["batch", "objective"]].rename(columns={"objective": f"objective"})


def _unstable_flag(row: Dict[str, object], weekly: Optional[pd.DataFrame]) -> bool:
    rel_precision = row.get("objective_rel_precision", np.nan)
    urgent_slots = int(row.get("urgent_slots", 0))
    if urgent_slots >= 18 and pd.notna(rel_precision) and float(rel_precision) > 0.10:
        return True
    if weekly is None or weekly.empty:
        return False
    design_weekly = weekly[(weekly["design_id"] == row["design_id"]) & (weekly["variant"] == row["variant"])]
    if len(design_weekly) < 8:
        return False
    first = design_weekly.head(max(3, len(design_weekly) // 5))["elective_appointment_wait_hours_mean"].mean()
    last = design_weekly.tail(max(3, len(design_weekly) // 5))["elective_appointment_wait_hours_mean"].mean()
    return bool(urgent_slots >= 18 and first > 0 and last > 1.25 * first)

