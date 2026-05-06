from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

from .config import ProjectConfig
from .entities import ELECTIVE, URGENT, Patient, SimulationResult, WeeklySchedule
from .random_streams import RandomStreams
from .schedule import ScheduleGenerator


@dataclass(frozen=True)
class Design:
    strategy: int
    urgent_slots: int
    appointment_rule: int

    @property
    def design_id(self) -> str:
        return f"S{self.strategy}-U{self.urgent_slots}-R{self.appointment_rule}"


class SimulationEngine:
    """Event-oriented evaluator for a repeated cyclic weekly schedule."""

    def __init__(self, config: ProjectConfig):
        self.config = config
        self.generator = ScheduleGenerator(config)
        self.day_minutes = config.day_minutes
        self.slot_length = config.slot_length_minutes
        self.weights = config.objective_weights

    def run_design(
        self,
        strategy: int,
        urgent_slots: int,
        appointment_rule: int,
        total_weeks: int,
        replication: int = 0,
        antithetic: bool = False,
        patient_records: bool = False,
    ) -> SimulationResult:
        design = Design(strategy, urgent_slots, appointment_rule)
        schedule = self.generator.generate(strategy, urgent_slots, appointment_rule)
        streams = RandomStreams(
            base_seed=int(self.config.get("randomness", "base_seed")),
            replication=replication,
            antithetic=antithetic,
            stream_names=self.config.stream_names(),
        )

        patients = self._generate_patients(total_weeks, streams)
        self._assign_elective_slots(patients, schedule, total_weeks)
        self._assign_urgent_slots(patients, schedule)
        weekly = self._execute_days(patients, total_weeks)
        weekly.insert(0, "variant", "antithetic" if antithetic else "standard")
        weekly.insert(0, "replication", replication)
        weekly.insert(0, "appointment_rule", appointment_rule)
        weekly.insert(0, "urgent_slots", urgent_slots)
        weekly.insert(0, "strategy", strategy)
        weekly.insert(0, "design_id", design.design_id)

        patient_frame = pd.DataFrame()
        if patient_records:
            patient_frame = pd.DataFrame([patient.to_record() for patient in patients])
            patient_frame.insert(0, "variant", "antithetic" if antithetic else "standard")
            patient_frame.insert(0, "replication", replication)
            patient_frame.insert(0, "design_id", design.design_id)

        return SimulationResult(
            design_id=design.design_id,
            strategy=strategy,
            urgent_slots=urgent_slots,
            appointment_rule=appointment_rule,
            replication=replication,
            variant="antithetic" if antithetic else "standard",
            weekly=weekly,
            patients=patient_frame,
            metadata={
                "stream_seeds": dict(streams.seeds),
                "total_weeks": total_weeks,
                "patient_count": len(patients),
            },
        )

    def _generate_patients(self, total_weeks: int, streams: RandomStreams) -> List[Patient]:
        patients: List[Patient] = []
        next_id = 0
        next_id = self._generate_elective_patients(total_weeks, streams, patients, next_id)
        self._generate_urgent_patients(total_weeks, streams, patients, next_id)
        return sorted(patients, key=lambda p: (p.call_minute_abs, 0 if p.patient_type == URGENT else 1))

    def _generate_elective_patients(
        self,
        total_weeks: int,
        streams: RandomStreams,
        patients: List[Patient],
        next_id: int,
    ) -> int:
        process = self.config.get("arrival_processes", "elective_calls")
        start = float(process["start_minute"])
        end = float(process["end_minute"])
        horizon = end - start
        lam = float(process["lambda_per_day"])
        no_show_probability = float(self.config.get("elective", "no_show_probability"))
        punctuality = self.config.get("elective", "punctuality")
        duration = self.config.get("elective", "duration")

        for week in range(total_weeks):
            for day in process["days"]:
                minute = start
                while True:
                    minute += streams.exponential_minutes("elective_calls", lam, horizon)
                    if minute >= end:
                        break
                    call_abs = self._absolute_minute(week, day, minute)
                    patients.append(
                        Patient(
                            patient_id=next_id,
                            patient_type=ELECTIVE,
                            call_week=week,
                            call_day=day,
                            call_minute_abs=call_abs,
                            punctuality_minutes=streams.normal(
                                "punctuality",
                                float(punctuality["mean_minutes"]),
                                float(punctuality["sd_minutes"]),
                            ),
                            is_no_show=streams.bernoulli("no_shows", no_show_probability),
                            duration_minutes=streams.positive_normal(
                                "elective_durations",
                                float(duration["mean_minutes"]),
                                float(duration["sd_minutes"]),
                            ),
                        )
                    )
                    next_id += 1
        return next_id

    def _generate_urgent_patients(
        self,
        total_weeks: int,
        streams: RandomStreams,
        patients: List[Patient],
        next_id: int,
    ) -> None:
        urgent_cfg = self.config.get("arrival_processes", "urgent_arrivals")
        scan_types = self.config.get("urgent", "scan_types")
        probabilities = [float(item["probability"]) for item in scan_types]

        for week in range(total_weeks):
            for day in range(6):
                start, end = self._opening_bounds(day)
                lam = (
                    float(urgent_cfg["lambda_half_day"])
                    if day in self.config.half_days
                    else float(urgent_cfg["lambda_full_day"])
                )
                minute = float(start)
                horizon = float(end - start)
                while True:
                    minute += streams.exponential_minutes("urgent_arrivals", lam, horizon)
                    if minute >= end:
                        break
                    scan_idx = streams.categorical("urgent_scan_type", probabilities)
                    scan_cfg = scan_types[scan_idx]
                    patients.append(
                        Patient(
                            patient_id=next_id,
                            patient_type=URGENT,
                            scan_type=str(scan_cfg["name"]),
                            call_week=week,
                            call_day=day,
                            call_minute_abs=self._absolute_minute(week, day, minute),
                            duration_minutes=streams.positive_normal(
                                "urgent_durations",
                                float(scan_cfg["mean_minutes"]),
                                float(scan_cfg["sd_minutes"]),
                            ),
                        )
                    )
                    next_id += 1

    def _assign_elective_slots(
        self,
        patients: Iterable[Patient],
        schedule: WeeklySchedule,
        total_weeks: int,
    ) -> None:
        elective_patients = [patient for patient in patients if patient.patient_type == ELECTIVE]
        elective_patients.sort(key=lambda patient: patient.call_minute_abs)
        # Tail buffer prevents artificial end-of-horizon loss for overloaded high-U designs.
        horizon_weeks = total_weeks + max(52, int(np.ceil(total_weeks * 0.2)))
        slot_sequence = self._slot_sequence(schedule, ELECTIVE, horizon_weeks)
        pointer = 0

        for patient in elective_patients:
            while pointer < len(slot_sequence) and slot_sequence[pointer][2] <= patient.call_minute_abs:
                pointer += 1
            if pointer >= len(slot_sequence):
                raise RuntimeError("Elective scheduling horizon exhausted; increase tail buffer")
            week, slot, appointment_abs, start_abs = slot_sequence[pointer]
            pointer += 1
            patient.assigned_week = week
            patient.assigned_day = slot.day
            patient.slot_start_abs = start_abs
            patient.appointment_minute_abs = appointment_abs
            patient.physical_arrival_abs = appointment_abs + patient.punctuality_minutes
            patient.service_order_abs = start_abs

    def _assign_urgent_slots(self, patients: Iterable[Patient], schedule: WeeklySchedule) -> None:
        urgent_patients = [patient for patient in patients if patient.patient_type == URGENT]
        by_day: DefaultDict[Tuple[int, int], List[Patient]] = defaultdict(list)
        for patient in urgent_patients:
            by_day[(patient.call_week, patient.call_day)].append(patient)

        for (week, day), day_patients in by_day.items():
            day_patients.sort(key=lambda patient: patient.call_minute_abs)
            urgent_slots = schedule.urgent_slots_for_day(day)
            used = set()
            overtime_counter = 0
            planned_end = self._absolute_minute(week, day, self._planned_end(day))
            for patient in day_patients:
                assigned = False
                for idx, slot in enumerate(urgent_slots):
                    start_abs = self._absolute_minute(week, day, slot.start_minute)
                    if idx not in used and start_abs >= patient.call_minute_abs:
                        used.add(idx)
                        patient.assigned_week = week
                        patient.assigned_day = day
                        patient.slot_start_abs = start_abs
                        patient.appointment_minute_abs = start_abs
                        patient.physical_arrival_abs = patient.call_minute_abs
                        patient.service_order_abs = start_abs
                        assigned = True
                        break
                if not assigned:
                    patient.assigned_week = week
                    patient.assigned_day = day
                    patient.slot_start_abs = planned_end
                    patient.appointment_minute_abs = planned_end
                    patient.physical_arrival_abs = patient.call_minute_abs
                    patient.is_overtime = True
                    patient.service_order_abs = planned_end + overtime_counter * 1e-3
                    overtime_counter += 1

    def _execute_days(self, patients: Iterable[Patient], total_weeks: int) -> pd.DataFrame:
        patients_by_day: DefaultDict[Tuple[int, int], List[Patient]] = defaultdict(list)
        elective_app_waits: DefaultDict[int, List[float]] = defaultdict(list)
        elective_scan_waits: DefaultDict[int, List[float]] = defaultdict(list)
        urgent_scan_waits: DefaultDict[int, List[float]] = defaultdict(list)
        overtime_by_week: DefaultDict[int, List[float]] = defaultdict(list)

        for patient in patients:
            if patient.patient_type == ELECTIVE:
                wait = patient.appointment_wait_hours()
                if wait is not None and 0 <= patient.call_week < total_weeks:
                    elective_app_waits[patient.call_week].append(wait)
            if patient.assigned_week is not None and 0 <= patient.assigned_week < total_weeks:
                patients_by_day[(patient.assigned_week, patient.assigned_day or 0)].append(patient)

        for week in range(total_weeks):
            for day in range(6):
                day_patients = patients_by_day.get((week, day), [])
                day_patients.sort(
                    key=lambda patient: (
                        patient.service_order_abs if patient.service_order_abs is not None else float("inf"),
                        0 if patient.patient_type == URGENT else 1,
                        patient.patient_id,
                    )
                )
                server_available = self._absolute_minute(week, day, self._opening_bounds(day)[0])
                last_scan_end = server_available
                for patient in day_patients:
                    if patient.patient_type == ELECTIVE and patient.is_no_show:
                        continue
                    arrival = patient.physical_arrival_abs if patient.patient_type == ELECTIVE else patient.call_minute_abs
                    slot_start = patient.slot_start_abs if patient.slot_start_abs is not None else arrival
                    scan_start = max(server_available, arrival or server_available, slot_start)
                    scan_start = self._respect_lunch_start(day, scan_start)
                    scan_end = scan_start + patient.duration_minutes
                    patient.scan_start_abs = scan_start
                    patient.scan_end_abs = scan_end
                    server_available = scan_end
                    last_scan_end = max(last_scan_end, scan_end)

                    wait = patient.scan_wait_hours()
                    if wait is not None:
                        if patient.patient_type == ELECTIVE:
                            elective_scan_waits[week].append(wait)
                        else:
                            urgent_scan_waits[week].append(wait)

                overtime_hours = max(0.0, (last_scan_end - self._absolute_minute(week, day, self._planned_end(day))) / 60.0)
                overtime_by_week[week].append(overtime_hours)

        rows = []
        for week in range(total_weeks):
            elective_app = mean_or_zero(elective_app_waits[week])
            urgent_scan = mean_or_zero(urgent_scan_waits[week])
            objective = self.weights["elective"] * elective_app + self.weights["urgent"] * urgent_scan
            rows.append(
                {
                    "week": week,
                    "elective_appointment_wait_hours_mean": elective_app,
                    "elective_appointment_wait_days_mean": elective_app / 24.0,
                    "elective_scan_wait_hours_mean": mean_or_zero(elective_scan_waits[week]),
                    "urgent_scan_wait_hours_mean": urgent_scan,
                    "daily_overtime_hours_mean": mean_or_zero(overtime_by_week[week]),
                    "daily_overtime_hours_total": sum(overtime_by_week[week]),
                    "elective_calls": len(elective_app_waits[week]),
                    "elective_scans": len(elective_scan_waits[week]),
                    "urgent_scans": len(urgent_scan_waits[week]),
                    "objective": objective,
                }
            )
        return pd.DataFrame(rows)

    def _slot_sequence(
        self,
        schedule: WeeklySchedule,
        patient_type: str,
        horizon_weeks: int,
    ) -> List[Tuple[int, object, float, float]]:
        base_slots = [slot for slot in schedule.slots if slot.patient_type == patient_type]
        base_slots.sort(key=lambda slot: (slot.day, slot.appointment_minute, slot.start_minute))
        sequence = []
        for week in range(horizon_weeks):
            for slot in base_slots:
                appointment_abs = self._absolute_minute(week, slot.day, slot.appointment_minute)
                start_abs = self._absolute_minute(week, slot.day, slot.start_minute)
                sequence.append((week, slot, appointment_abs, start_abs))
        return sequence

    def _absolute_minute(self, week: int, day: int, minute_of_day: float) -> float:
        return week * 7 * self.day_minutes + day * self.day_minutes + minute_of_day

    def _opening_bounds(self, day: int) -> Tuple[int, int]:
        if day in self.config.half_days:
            bounds = self.config.get("calendar", "opening", "half_day")
            return int(bounds["start"]), int(bounds["end"])
        bounds = self.config.get("calendar", "opening", "full_day")
        return int(bounds["start"]), int(bounds["end"])

    def _planned_end(self, day: int) -> int:
        return self._opening_bounds(day)[1]

    def _respect_lunch_start(self, day: int, absolute_minute: float) -> float:
        if day not in self.config.full_days:
            return absolute_minute
        minute_of_day = absolute_minute % self.day_minutes
        lunch = self.config.get("calendar", "opening", "full_day")
        if int(lunch["lunch_start"]) <= minute_of_day < int(lunch["lunch_end"]):
            return absolute_minute + (int(lunch["lunch_end"]) - minute_of_day)
        return absolute_minute


def mean_or_zero(values: Iterable[float]) -> float:
    values = list(values)
    return float(np.mean(values)) if values else 0.0

