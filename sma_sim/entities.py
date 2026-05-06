from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd


ELECTIVE = "elective"
URGENT = "urgent"
REGULAR_URGENT = "regular_urgent"
OVERTIME_URGENT = "overtime_urgent"


@dataclass(frozen=True)
class Slot:
    day: int
    day_name: str
    session: str
    index_in_day: int
    index_in_session: int
    start_minute: int
    patient_type: str
    slot_type: str
    appointment_minute: float

    @property
    def is_urgent(self) -> bool:
        return self.patient_type == URGENT

    @property
    def is_elective(self) -> bool:
        return self.patient_type == ELECTIVE


@dataclass
class WeeklySchedule:
    strategy: int
    urgent_slots: int
    appointment_rule: int
    slots: List[Slot]
    day_names: List[str]

    def validate(self) -> None:
        if len(self.slots) != 160:
            raise ValueError(f"Expected 160 open regular slots/week, got {len(self.slots)}")
        if any(slot.day == 6 for slot in self.slots):
            raise ValueError("Sunday slots are not allowed")
        if self.count_patient_type(URGENT) != self.urgent_slots:
            raise ValueError("Urgent slot count does not equal requested target")
        if self.count_patient_type(ELECTIVE) + self.count_patient_type(URGENT) != 160:
            raise ValueError("Every open slot must be elective or urgent")
        for day in (3, 5):
            day_slots = [slot for slot in self.slots if slot.day == day]
            if len(day_slots) != 16 or any(slot.start_minute >= 720 for slot in day_slots):
                raise ValueError("Thursday and Saturday must be half-day sessions")

    def count_patient_type(self, patient_type: str) -> int:
        return sum(1 for slot in self.slots if slot.patient_type == patient_type)

    def slots_for_day(self, day: int) -> List[Slot]:
        return sorted([slot for slot in self.slots if slot.day == day], key=lambda s: s.start_minute)

    def urgent_slots_for_day(self, day: int) -> List[Slot]:
        return [slot for slot in self.slots_for_day(day) if slot.is_urgent]

    def elective_slots(self) -> List[Slot]:
        return sorted([slot for slot in self.slots if slot.is_elective], key=lambda s: (s.day, s.start_minute))

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([slot.__dict__ for slot in self.slots])


@dataclass
class Patient:
    patient_id: int
    patient_type: str
    call_week: int
    call_day: int
    call_minute_abs: float
    duration_minutes: float
    scan_type: str = ""
    punctuality_minutes: float = 0.0
    is_no_show: bool = False
    assigned_week: Optional[int] = None
    assigned_day: Optional[int] = None
    slot_start_abs: Optional[float] = None
    appointment_minute_abs: Optional[float] = None
    physical_arrival_abs: Optional[float] = None
    scan_start_abs: Optional[float] = None
    scan_end_abs: Optional[float] = None
    is_overtime: bool = False
    service_order_abs: Optional[float] = None

    def appointment_wait_hours(self) -> Optional[float]:
        if self.appointment_minute_abs is None:
            return None
        return max(0.0, (self.appointment_minute_abs - self.call_minute_abs) / 60.0)

    def appointment_wait_days(self) -> Optional[float]:
        value = self.appointment_wait_hours()
        return None if value is None else value / 24.0

    def scan_wait_hours(self) -> Optional[float]:
        if self.scan_start_abs is None:
            return None
        arrival = self.physical_arrival_abs if self.patient_type == ELECTIVE else self.call_minute_abs
        if arrival is None:
            return None
        return max(0.0, (self.scan_start_abs - arrival) / 60.0)

    def to_record(self) -> Dict[str, object]:
        return {
            "patient_id": self.patient_id,
            "patient_type": self.patient_type,
            "call_week": self.call_week,
            "call_day": self.call_day,
            "call_minute_abs": self.call_minute_abs,
            "duration_minutes": self.duration_minutes,
            "scan_type": self.scan_type,
            "punctuality_minutes": self.punctuality_minutes,
            "is_no_show": self.is_no_show,
            "assigned_week": self.assigned_week,
            "assigned_day": self.assigned_day,
            "slot_start_abs": self.slot_start_abs,
            "appointment_minute_abs": self.appointment_minute_abs,
            "physical_arrival_abs": self.physical_arrival_abs,
            "scan_start_abs": self.scan_start_abs,
            "scan_end_abs": self.scan_end_abs,
            "is_overtime": self.is_overtime,
            "appointment_wait_hours": self.appointment_wait_hours(),
            "appointment_wait_days": self.appointment_wait_days(),
            "scan_wait_hours": self.scan_wait_hours(),
        }


@dataclass
class SimulationResult:
    design_id: str
    strategy: int
    urgent_slots: int
    appointment_rule: int
    replication: int
    variant: str
    weekly: pd.DataFrame
    patients: pd.DataFrame = field(default_factory=pd.DataFrame)
    metadata: Dict[str, object] = field(default_factory=dict)

