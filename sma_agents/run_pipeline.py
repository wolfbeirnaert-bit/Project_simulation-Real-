from __future__ import annotations

import argparse
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

os.environ.setdefault("MPLCONFIGDIR", str(Path("outputs") / ".matplotlib"))

import pandas as pd

from sma_sim.analysis import (
    autocorrelation,
    build_design_matrix,
    compute_batch_results,
    factor_effects,
    pair_antithetic_weekly,
    pareto_front,
    summarize_batches,
    top_designs_comparison,
    variance_reduction_summary,
    welch_curve,
)
from sma_sim.config import ProjectConfig, dump_config, load_config
from sma_sim.plotting import (
    plot_autocorrelation,
    plot_objective_by_urgent,
    plot_pareto,
    plot_schedule_heatmap,
    plot_welch,
)
from sma_sim.reporting import write_report_assets
from sma_sim.schedule import ScheduleGenerator
from sma_sim.simulation import SimulationEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the agentic SMA radiology pipeline.")
    parser.add_argument("--mode", choices=["quick", "full"], default="quick")
    parser.add_argument("--config", default="config/project_config.yaml")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--output-root", default="outputs")
    args = parser.parse_args()

    config = load_config(args.config)
    output_dir = _make_output_dir(Path(args.output_root))
    (output_dir / "figures").mkdir(parents=True, exist_ok=True)
    (output_dir / "tables").mkdir(parents=True, exist_ok=True)
    (output_dir / "report_assets").mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(output_dir / ".matplotlib")

    log_lines: List[str] = []
    _log(log_lines, f"Started {args.mode} pipeline at {datetime.now().isoformat(timespec='seconds')}")
    _log(log_lines, f"Output directory: {output_dir}")

    (output_dir / "config_used.yaml").write_text(dump_config(config.data), encoding="utf-8")

    settings = config.mode_settings(args.mode)
    total_weeks = int(settings["warmup_weeks"]) + int(settings["batch_size_weeks"]) * int(settings["batches"])
    design_matrix = build_design_matrix(
        strategies=[1, 2, 3],
        urgent_slots=config.design_urgent_slots(args.mode),
        rules=config.design_rules(args.mode),
    )
    design_matrix.to_csv(output_dir / "design_matrix.csv", index=False)
    _log(log_lines, f"Design matrix rows: {len(design_matrix)}")

    generator = ScheduleGenerator(config)
    _validate_and_plot_schedules(generator, design_matrix, output_dir, log_lines)

    jobs = [
        {
            "config_data": config.data,
            "config_path": str(config.path),
            "strategy": int(row.strategy),
            "urgent_slots": int(row.urgent_slots),
            "appointment_rule": int(row.appointment_rule),
            "total_weeks": total_weeks,
            "patient_records": bool(settings.get("patient_records", False)),
            "antithetic_enabled": bool(settings.get("antithetic", True)),
        }
        for row in design_matrix.itertuples(index=False)
    ]
    _log(log_lines, f"Running {len(jobs)} designs for {total_weeks} weeks each")
    weekly_frames, patient_frames = _run_jobs(jobs, max(1, int(args.workers)))

    weekly_standard = pd.concat(weekly_frames, ignore_index=True)
    paired = pair_antithetic_weekly(weekly_standard)
    weekly_all = pd.concat([weekly_standard, paired], ignore_index=True)
    weekly_all.to_csv(output_dir / "weekly_results.csv", index=False)
    weekly_all.to_csv(output_dir / "raw_results.csv", index=False)
    if patient_frames:
        pd.concat(patient_frames, ignore_index=True).to_csv(output_dir / "patient_results.csv", index=False)
    else:
        pd.DataFrame().to_csv(output_dir / "patient_results.csv", index=False)

    batch_results = compute_batch_results(
        weekly_all,
        warmup_weeks=int(settings["warmup_weeks"]),
        batch_size_weeks=int(settings["batch_size_weeks"]),
        batches=int(settings["batches"]),
    )
    batch_results.to_csv(output_dir / "batch_results.csv", index=False)
    batch_results.to_csv(output_dir / "tables" / "batch_means_summary.csv", index=False)

    summary = summarize_batches(batch_results, weekly_all)
    summary.to_csv(output_dir / "summary_results.csv", index=False)
    summary.to_csv(output_dir / "tables" / "screening_results.csv", index=False)

    variance = variance_reduction_summary(batch_results)
    variance.to_csv(output_dir / "tables" / "variance_reduction_summary.csv", index=False)

    effects = factor_effects(summary)
    effects.to_csv(output_dir / "tables" / "factor_effects.csv", index=False)

    top_compare = top_designs_comparison(batch_results, summary)
    top_compare.to_csv(output_dir / "tables" / "top_designs_comparison.csv", index=False)

    pareto = pareto_front(summary)
    pareto.to_csv(output_dir / "tables" / "pareto_table.csv", index=False)

    _write_figures(weekly_all, summary, pareto, output_dir)
    write_report_assets(output_dir / "report_assets", summary, pareto, args.mode)
    _mirror_report_assets(output_dir / "report_assets", Path("report_assets"), log_lines)

    main_summary = summary[summary["variant"] == "paired_antithetic"]
    if main_summary.empty:
        main_summary = summary[summary["variant"] == "standard"]
    best = main_summary.sort_values("objective_mean").head(1)
    if not best.empty:
        _log(log_lines, f"Best point estimate: {best.iloc[0]['design_id']} objective={best.iloc[0]['objective_mean']:.4f}")
    _log(log_lines, f"Unstable/precision flags: {int(main_summary['unstable_flag'].sum())}")
    _log(log_lines, "Finished pipeline")
    (output_dir / "run_log.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print("\n".join(log_lines))


def _run_jobs(jobs: List[Dict[str, Any]], workers: int) -> Tuple[List[pd.DataFrame], List[pd.DataFrame]]:
    if workers <= 1:
        results = [_run_design_job(job) for job in jobs]
    else:
        try:
            with ProcessPoolExecutor(max_workers=workers) as executor:
                results = list(executor.map(_run_design_job, jobs))
        except PermissionError:
            # Some sandboxed environments block multiprocessing semaphore checks.
            # Threads keep the command runnable; local terminals should still use processes.
            with ThreadPoolExecutor(max_workers=workers) as executor:
                results = list(executor.map(_run_design_job, jobs))
    weekly_frames = [item[0] for item in results]
    patient_frames = [item[1] for item in results if not item[1].empty]
    return weekly_frames, patient_frames


def _run_design_job(job: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    config = ProjectConfig(data=job["config_data"], path=Path(job["config_path"]))
    engine = SimulationEngine(config)
    frames = []
    patient_frames = []
    standard = engine.run_design(
        strategy=job["strategy"],
        urgent_slots=job["urgent_slots"],
        appointment_rule=job["appointment_rule"],
        total_weeks=job["total_weeks"],
        replication=0,
        antithetic=False,
        patient_records=job["patient_records"],
    )
    frames.append(standard.weekly)
    if not standard.patients.empty:
        patient_frames.append(standard.patients)

    if job["antithetic_enabled"]:
        anti = engine.run_design(
            strategy=job["strategy"],
            urgent_slots=job["urgent_slots"],
            appointment_rule=job["appointment_rule"],
            total_weeks=job["total_weeks"],
            replication=0,
            antithetic=True,
            patient_records=job["patient_records"],
        )
        frames.append(anti.weekly)
        if not anti.patients.empty:
            patient_frames.append(anti.patients)

    return pd.concat(frames, ignore_index=True), pd.concat(patient_frames, ignore_index=True) if patient_frames else pd.DataFrame()


def _validate_and_plot_schedules(
    generator: ScheduleGenerator,
    design_matrix: pd.DataFrame,
    output_dir: Path,
    log_lines: List[str],
) -> None:
    for row in design_matrix.itertuples(index=False):
        generator.generate(int(row.strategy), int(row.urgent_slots), int(row.appointment_rule)).validate()
    for strategy in (1, 2, 3):
        schedule = generator.generate(strategy, 14, 1)
        plot_schedule_heatmap(schedule, output_dir / "figures" / f"schedule_S{strategy}_U14_R1.png")
    baseline = generator.generate(1, 14, 1)
    _log(
        log_lines,
        f"Baseline schedule check: elective={baseline.count_patient_type('elective')} urgent={baseline.count_patient_type('urgent')}",
    )


def _write_figures(weekly: pd.DataFrame, summary: pd.DataFrame, pareto: pd.DataFrame, output_dir: Path) -> None:
    figures = output_dir / "figures"
    curve = welch_curve(weekly, window=5)
    plot_welch(curve, figures / "welch_plot.png")
    baseline = weekly[(weekly["design_id"] == "S1-U14-R1") & (weekly["variant"] == "paired_antithetic")]
    if baseline.empty:
        baseline = weekly[weekly["variant"] == "paired_antithetic"]
    acf = autocorrelation(baseline.groupby("week")["objective"].mean(), max_lag=50)
    acf.to_csv(output_dir / "tables" / "autocorrelation_values.csv", index=False)
    plot_autocorrelation(acf, figures / "autocorrelation_plot.png")
    plot_objective_by_urgent(summary, figures / "objective_by_urgent.png")
    plot_pareto(summary, pareto, figures / "pareto_front.png")


def _mirror_report_assets(source: Path, target: Path, log_lines: List[str]) -> None:
    target.mkdir(exist_ok=True)
    for name in [
        "report_outline.md",
        "methodology_draft.md",
        "results_draft.md",
        "latex_tables.tex",
        "figure_captions.md",
    ]:
        (target / name).write_text((source / name).read_text(encoding="utf-8"), encoding="utf-8")
    _log(log_lines, f"Mirrored report assets to {target}")


def _make_output_dir(root: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = root / timestamp
    output_dir.mkdir(parents=True, exist_ok=False)
    return output_dir


def _log(log_lines: List[str], message: str) -> None:
    log_lines.append(message)


if __name__ == "__main__":
    main()
