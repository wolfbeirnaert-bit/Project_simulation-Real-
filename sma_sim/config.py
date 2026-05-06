from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Union

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - depends on the active environment.
    yaml = None


DEFAULT_CONFIG_PATH = Path("config/project_config.yaml")

DEFAULT_CONFIG_DATA: Dict[str, Any] = {
    "project": {
        "name": "Reorganisation of an outpatient radiology department",
        "course": "Simulation Modelling and Analysis (F000941)",
        "academic_year": "2025-2026",
    },
    "calendar": {
        "day_names": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
        "full_days": [0, 1, 2, 4],
        "half_days": [3, 5],
        "closed_days": [6],
        "day_minutes": 1440,
        "opening": {
            "full_day": {"start": 480, "lunch_start": 720, "lunch_end": 780, "end": 1020},
            "half_day": {"start": 480, "end": 720},
        },
        "slot_length_minutes": 15,
        "current_schedule": {"elective_slots": 146, "urgent_slots": 14},
        "urgent_slot_range": [10, 20],
    },
    "arrival_processes": {
        "elective_calls": {
            "days": [0, 1, 2, 3, 4],
            "start_minute": 480,
            "end_minute": 1020,
            "lambda_per_day": 28.345,
        },
        "urgent_arrivals": {"lambda_full_day": 2.5, "lambda_half_day": 1.25},
    },
    "elective": {
        "no_show_probability": 0.02,
        "punctuality": {"distribution": "normal", "mean_minutes": 0.0, "sd_minutes": 2.5},
        "duration": {"distribution": "truncated_normal_positive", "mean_minutes": 15.0, "sd_minutes": 3.0},
    },
    "urgent": {
        "scan_types": [
            {"name": "brain", "probability": 0.70, "mean_minutes": 15.0, "sd_minutes": 2.5},
            {"name": "spine_lumbar", "probability": 0.10, "mean_minutes": 17.5, "sd_minutes": 1.0},
            {"name": "spine_cervical", "probability": 0.10, "mean_minutes": 22.5, "sd_minutes": 2.5},
            {"name": "abdomen_mri", "probability": 0.05, "mean_minutes": 30.0, "sd_minutes": 1.0},
            {"name": "others", "probability": 0.05, "mean_minutes": 30.0, "sd_minutes": 4.5},
        ]
    },
    "appointment_rules": {"bailey_welch_k": 2, "blocking_b": 2, "benchmark_k_sigma": 0.5},
    "objective": {
        "elective_appointment_wait_weight": 1 / 168,
        "urgent_scan_wait_weight": 1 / 9,
    },
    "randomness": {
        "base_seed": 42,
        "streams": [
            "elective_calls",
            "urgent_arrivals",
            "no_shows",
            "punctuality",
            "elective_durations",
            "urgent_scan_type",
            "urgent_durations",
        ],
    },
    "run_modes": {
        "quick": {
            "warmup_weeks": 2,
            "batch_size_weeks": 2,
            "batches": 3,
            "antithetic": True,
            "patient_records": True,
            "urgent_slots": [10, 14, 20],
            "appointment_rules": [1, 4],
        },
        "full": {
            "warmup_weeks": 60,
            "batch_size_weeks": 80,
            "batches": 22,
            "antithetic": True,
            "patient_records": False,
            "urgent_slots": [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
            "appointment_rules": [1, 2, 3, 4],
        },
    },
}


@dataclass(frozen=True)
class ProjectConfig:
    """Thin typed wrapper around the YAML source of truth."""

    data: Dict[str, Any]
    path: Path

    def get(self, *keys: str, default: Any = None) -> Any:
        node: Any = self.data
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    @property
    def slot_length_minutes(self) -> int:
        return int(self.get("calendar", "slot_length_minutes"))

    @property
    def day_minutes(self) -> int:
        return int(self.get("calendar", "day_minutes"))

    @property
    def full_days(self) -> List[int]:
        return list(self.get("calendar", "full_days"))

    @property
    def half_days(self) -> List[int]:
        return list(self.get("calendar", "half_days"))

    @property
    def day_names(self) -> List[str]:
        return list(self.get("calendar", "day_names"))

    @property
    def objective_weights(self) -> Dict[str, float]:
        return {
            "elective": float(self.get("objective", "elective_appointment_wait_weight")),
            "urgent": float(self.get("objective", "urgent_scan_wait_weight")),
        }

    @property
    def urgent_slot_values(self) -> List[int]:
        lo, hi = self.get("calendar", "urgent_slot_range")
        return list(range(int(lo), int(hi) + 1))

    def mode_settings(self, mode: str) -> Dict[str, Any]:
        settings = self.get("run_modes", mode)
        if not settings:
            raise ValueError(f"Unknown run mode: {mode}")
        return dict(settings)

    def design_urgent_slots(self, mode: str) -> List[int]:
        values = self.mode_settings(mode).get("urgent_slots")
        return [int(v) for v in values] if values else self.urgent_slot_values

    def design_rules(self, mode: str) -> List[int]:
        values = self.mode_settings(mode).get("appointment_rules")
        return [int(v) for v in values] if values else [1, 2, 3, 4]

    def stream_names(self) -> Iterable[str]:
        return list(self.get("randomness", "streams"))


def load_config(path: Union[str, Path] = DEFAULT_CONFIG_PATH) -> ProjectConfig:
    config_path = Path(path)
    if yaml is None:
        data = DEFAULT_CONFIG_DATA
    else:
        with config_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    return ProjectConfig(data=data, path=config_path)


def dump_config(data: Dict[str, Any]) -> str:
    if yaml is not None:
        return yaml.safe_dump(data, sort_keys=False)
    return json.dumps(data, indent=2)
