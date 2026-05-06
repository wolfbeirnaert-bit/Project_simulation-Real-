from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .entities import URGENT, WeeklySchedule


def plot_schedule_heatmap(schedule: WeeklySchedule, path: Path) -> None:
    frame = schedule.to_frame()
    matrix = np.full((32, 6), np.nan)
    for _, row in frame.iterrows():
        matrix[int(row["index_in_day"]), int(row["day"])] = 1 if row["patient_type"] == URGENT else 0

    plt.figure(figsize=(8, 8))
    plt.imshow(matrix, aspect="auto", cmap="Blues", vmin=0, vmax=1)
    plt.xticks(range(6), schedule.day_names, rotation=35, ha="right")
    plt.yticks(range(32), [f"{idx + 1}" for idx in range(32)])
    plt.xlabel("Day")
    plt.ylabel("Slot number")
    plt.title(f"Weekly schedule heatmap S{schedule.strategy}-U{schedule.urgent_slots}-R{schedule.appointment_rule}")
    plt.colorbar(label="Urgent slot")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_welch(curve: pd.DataFrame, path: Path) -> None:
    plt.figure(figsize=(9, 4))
    plt.plot(curve["week"], curve["objective"], alpha=0.35, label="Weekly objective")
    plt.plot(curve["week"], curve["welch_moving_average"], linewidth=2, label="Welch moving average")
    plt.xlabel("Week")
    plt.ylabel("Objective")
    plt.title("Welch-style moving average")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_autocorrelation(acf: pd.DataFrame, path: Path) -> None:
    plt.figure(figsize=(8, 4))
    if not acf.empty:
        plt.stem(acf["lag"], acf["autocorrelation"])
    plt.axhline(0.01, linestyle="--", color="red", linewidth=1)
    plt.axhline(-0.01, linestyle="--", color="red", linewidth=1)
    plt.xlabel("Lag (weeks)")
    plt.ylabel("Autocorrelation")
    plt.title("Autocorrelation of weekly objective")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_objective_by_urgent(summary: pd.DataFrame, path: Path) -> None:
    variant = "paired_antithetic" if "paired_antithetic" in set(summary["variant"]) else "standard"
    data = summary[summary["variant"] == variant]
    plt.figure(figsize=(9, 5))
    for strategy, group in data.groupby("strategy"):
        grouped = group.groupby("urgent_slots", as_index=False)["objective_mean"].min()
        plt.plot(grouped["urgent_slots"], grouped["objective_mean"], marker="o", label=f"Strategy {strategy}")
    plt.xlabel("Urgent slots per week")
    plt.ylabel("Best objective")
    plt.title("Objective versus urgent-slot capacity")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_pareto(summary: pd.DataFrame, pareto: pd.DataFrame, path: Path) -> None:
    variant = "paired_antithetic" if "paired_antithetic" in set(summary["variant"]) else "standard"
    data = summary[summary["variant"] == variant]
    plt.figure(figsize=(7, 5))
    plt.scatter(
        data["elective_appointment_wait_hours_mean"],
        data["urgent_scan_wait_hours_mean"],
        alpha=0.45,
        label="Tested designs",
    )
    if not pareto.empty:
        plt.plot(
            pareto["elective_appointment_wait_hours_mean"],
            pareto["urgent_scan_wait_hours_mean"],
            marker="o",
            color="red",
            label="Pareto front",
        )
    plt.xlabel("Elective appointment wait (hours)")
    plt.ylabel("Urgent scan wait (hours)")
    plt.title("Elective-urgent waiting time trade-off")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()

