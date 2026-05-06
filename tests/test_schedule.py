import pytest

from sma_sim.config import load_config
from sma_sim.entities import ELECTIVE, URGENT
from sma_sim.analysis import build_design_matrix
from sma_sim.schedule import ScheduleGenerator


@pytest.fixture()
def generator():
    return ScheduleGenerator(load_config())


def test_weekly_capacity_equals_expected_total_slots(generator):
    schedule = generator.generate(1, 14, 1)
    assert len(schedule.slots) == 160
    assert schedule.count_patient_type(ELECTIVE) == 146
    assert schedule.count_patient_type(URGENT) == 14


@pytest.mark.parametrize("urgent_slots", range(10, 21))
@pytest.mark.parametrize("strategy", [1, 2, 3])
def test_urgent_slot_count_exactly_matches_requested_u(generator, strategy, urgent_slots):
    schedule = generator.generate(strategy, urgent_slots, 1)
    assert schedule.count_patient_type(URGENT) == urgent_slots


def test_no_sunday_slots(generator):
    schedule = generator.generate(2, 20, 1)
    assert all(slot.day != 6 for slot in schedule.slots)


def test_thursday_and_saturday_half_day_slots(generator):
    schedule = generator.generate(3, 20, 1)
    for day in (3, 5):
        day_slots = schedule.slots_for_day(day)
        assert len(day_slots) == 16
        assert all(slot.start_minute < 720 for slot in day_slots)


def test_strategy_1_u14_reproduces_current_capacity_and_extra_morning_pattern(generator):
    schedule = generator.generate(1, 14, 1)
    urgent_by_day = {
        day: [slot.index_in_day for slot in schedule.urgent_slots_for_day(day)]
        for day in range(6)
    }
    assert schedule.count_patient_type(ELECTIVE) == 146
    assert schedule.count_patient_type(URGENT) == 14
    assert urgent_by_day[0] == [14, 15, 31]
    assert urgent_by_day[1] == [14, 15, 31]
    assert urgent_by_day[2] == [14, 15, 31]
    assert urgent_by_day[3] == [15]
    assert urgent_by_day[4] == [14, 15, 31]
    assert urgent_by_day[5] == [15]


def test_invalid_urgent_slot_count_rejected(generator):
    with pytest.raises(ValueError):
        generator.generate(1, 9, 1)


def test_full_design_matrix_has_132_required_configurations():
    matrix = build_design_matrix([1, 2, 3], range(10, 21), [1, 2, 3, 4])
    assert len(matrix) == 132
    assert set(matrix["urgent_slots"]) == set(range(10, 21))
