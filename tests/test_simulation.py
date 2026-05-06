import pandas as pd

from sma_sim.config import load_config
from sma_sim.entities import Patient
from sma_sim.simulation import SimulationEngine


def test_overtime_zero_when_last_scan_finishes_before_session_end():
    engine = SimulationEngine(load_config())
    patient = Patient(
        patient_id=1,
        patient_type="urgent",
        call_week=0,
        call_day=0,
        call_minute_abs=500,
        duration_minutes=10,
        assigned_week=0,
        assigned_day=0,
        slot_start_abs=510,
        appointment_minute_abs=510,
        physical_arrival_abs=500,
        service_order_abs=510,
    )
    weekly = engine._execute_days([patient], total_weeks=1)
    assert weekly.loc[0, "daily_overtime_hours_total"] == 0


def test_urgent_patient_goes_to_overtime_when_no_urgent_slot_remains():
    cfg = load_config()
    engine = SimulationEngine(cfg)
    schedule = engine.generator.generate(1, 10, 1)
    last_urgent_start = max(slot.start_minute for slot in schedule.urgent_slots_for_day(0))
    patient = Patient(
        patient_id=1,
        patient_type="urgent",
        call_week=0,
        call_day=0,
        call_minute_abs=last_urgent_start + 1,
        duration_minutes=10,
    )
    engine._assign_urgent_slots([patient], schedule)
    assert patient.is_overtime is True
    assert patient.slot_start_abs == 1020


def test_reproducibility_same_seed_gives_same_result():
    engine = SimulationEngine(load_config())
    a = engine.run_design(1, 14, 1, total_weeks=3, replication=0, antithetic=False)
    b = engine.run_design(1, 14, 1, total_weeks=3, replication=0, antithetic=False)
    pd.testing.assert_frame_equal(a.weekly, b.weekly)


def test_different_replication_changes_result():
    engine = SimulationEngine(load_config())
    a = engine.run_design(1, 14, 1, total_weeks=3, replication=0, antithetic=False)
    b = engine.run_design(1, 14, 1, total_weeks=3, replication=1, antithetic=False)
    assert not a.weekly["objective"].equals(b.weekly["objective"])

