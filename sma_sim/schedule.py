from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from .config import ProjectConfig
from .entities import ELECTIVE, URGENT, Slot, WeeklySchedule


@dataclass(frozen=True)
class Session:
    day: int
    name: str
    start_minute: int
    slots: int = 16


class AppointmentRule:
    FCFS = 1
    BAILEY_WELCH = 2
    BLOCKING = 3
    BENCHMARK = 4

    @staticmethod
    def label(rule_id: int) -> str:
        labels = {
            1: "Plain FCFS",
            2: "Bailey-Welch K=2",
            3: "Blocking B=2",
            4: "Benchmark k_sigma=0.5",
        }
        return labels[rule_id]


class ScheduleGenerator:
    """Generate cyclic weekly schedules for the three assignment strategies."""

    def __init__(self, config: ProjectConfig):
        self.config = config
        self.slot_length = config.slot_length_minutes
        self.day_names = config.day_names
        self.sessions = self._build_sessions()

    def generate(self, strategy: int, urgent_slots: int, appointment_rule: int = 1) -> WeeklySchedule:
        if strategy not in (1, 2, 3):
            raise ValueError("strategy must be 1, 2, or 3")
        if urgent_slots < 10 or urgent_slots > 20:
            raise ValueError("urgent_slots must be in the assignment range 10..20")

        counts = self._urgent_counts_by_session(urgent_slots)
        slots: List[Slot] = []
        for session in self.sessions:
            urgent_positions = self._urgent_positions(strategy, counts[session_key(session)])
            for idx in range(session.slots):
                patient_type = URGENT if idx in urgent_positions else ELECTIVE
                start_minute = session.start_minute + idx * self.slot_length
                slots.append(
                    Slot(
                        day=session.day,
                        day_name=self.day_names[session.day],
                        session=session.name,
                        index_in_day=self._index_in_day(session, idx),
                        index_in_session=idx,
                        start_minute=start_minute,
                        patient_type=patient_type,
                        slot_type=patient_type,
                        appointment_minute=start_minute,
                    )
                )

        schedule = WeeklySchedule(
            strategy=strategy,
            urgent_slots=urgent_slots,
            appointment_rule=appointment_rule,
            slots=self._apply_appointment_rule(slots, appointment_rule),
            day_names=self.day_names,
        )
        schedule.validate()
        return schedule

    def _build_sessions(self) -> List[Session]:
        sessions: List[Session] = []
        for day in range(6):
            sessions.append(Session(day=day, name="morning", start_minute=480))
            if day in self.config.full_days:
                sessions.append(Session(day=day, name="afternoon", start_minute=780))
        return sessions

    def _urgent_counts_by_session(self, urgent_slots: int) -> Dict[Tuple[int, str], int]:
        base = urgent_slots // len(self.sessions)
        remainder = urgent_slots % len(self.sessions)
        counts = {session_key(session): base for session in self.sessions}

        # This priority reproduces the provided S1-U14 input structure:
        # one urgent at every session end plus the four extra slots at the
        # morning ends of the full operating days.
        priority = [
            (0, "morning"),
            (1, "morning"),
            (2, "morning"),
            (4, "morning"),
            (0, "afternoon"),
            (1, "afternoon"),
            (2, "afternoon"),
            (4, "afternoon"),
            (3, "morning"),
            (5, "morning"),
        ]
        for key in priority[:remainder]:
            counts[key] += 1
        return counts

    def _urgent_positions(self, strategy: int, count: int) -> List[int]:
        if count == 0:
            return []
        if count > 16:
            raise ValueError("A 16-slot session cannot contain more than 16 urgent slots")

        if strategy == 1:
            return list(range(16 - count, 16))
        if strategy == 2:
            return sorted({round((i + 1) * 16 / (count + 1)) for i in range(count)})

        positions: List[int] = []
        elective_since_urgent = 0
        for idx in range(16):
            if len(positions) >= count:
                break
            if elective_since_urgent == 6:
                positions.append(idx)
                elective_since_urgent = 0
            else:
                elective_since_urgent += 1
        while len(positions) < count:
            candidate = 15 - len(positions)
            if candidate not in positions:
                positions.append(candidate)
        return sorted(positions)

    def _apply_appointment_rule(self, slots: Iterable[Slot], appointment_rule: int) -> List[Slot]:
        if appointment_rule not in (1, 2, 3, 4):
            raise ValueError("appointment_rule must be 1, 2, 3, or 4")
        k = int(self.config.get("appointment_rules", "bailey_welch_k"))
        block_size = int(self.config.get("appointment_rules", "blocking_b"))
        k_sigma = float(self.config.get("appointment_rules", "benchmark_k_sigma"))
        elective_sd = float(self.config.get("elective", "duration", "sd_minutes"))
        elective_mean = float(self.config.get("elective", "duration", "mean_minutes"))

        grouped: Dict[Tuple[int, str], List[Slot]] = {}
        for slot in slots:
            grouped.setdefault((slot.day, slot.session), []).append(slot)

        updated: List[Slot] = []
        for (_day, _session), session_slots in grouped.items():
            session_slots = sorted(session_slots, key=lambda slot: slot.index_in_session)
            session_start = session_slots[0].start_minute
            elective_sequence = 0
            for slot in session_slots:
                appointment = float(slot.start_minute)
                if slot.is_elective:
                    if appointment_rule == AppointmentRule.FCFS:
                        appointment = float(slot.start_minute)
                    elif appointment_rule == AppointmentRule.BAILEY_WELCH:
                        appointment = float(session_start if elective_sequence < k else slot.start_minute - elective_mean)
                    elif appointment_rule == AppointmentRule.BLOCKING:
                        block_start_idx = (slot.index_in_session // block_size) * block_size
                        appointment = float(session_start + block_start_idx * self.slot_length)
                    elif appointment_rule == AppointmentRule.BENCHMARK:
                        appointment = float(slot.start_minute - k_sigma * elective_sd)
                    elective_sequence += 1
                updated.append(
                    Slot(
                        day=slot.day,
                        day_name=slot.day_name,
                        session=slot.session,
                        index_in_day=slot.index_in_day,
                        index_in_session=slot.index_in_session,
                        start_minute=slot.start_minute,
                        patient_type=slot.patient_type,
                        slot_type=slot.slot_type,
                        appointment_minute=appointment,
                    )
                )
        return sorted(updated, key=lambda slot: (slot.day, slot.start_minute))

    @staticmethod
    def _index_in_day(session: Session, index_in_session: int) -> int:
        offset = 0 if session.name == "morning" else 16
        return offset + index_in_session


def session_key(session: Session) -> Tuple[int, str]:
    return (session.day, session.name)

