from sma_sim.config import load_config
from sma_sim.random_streams import RandomStreams, make_stream_seeds
from sma_sim.schedule import ScheduleGenerator


def first_elective_slots(schedule, day=0, session="morning", n=4):
    slots = [
        slot
        for slot in schedule.slots
        if slot.day == day and slot.session == session and slot.patient_type == "elective"
    ]
    return sorted(slots, key=lambda slot: slot.start_minute)[:n]


def test_appointment_rule_1_fcfs_times():
    schedule = ScheduleGenerator(load_config()).generate(1, 10, 1)
    slots = first_elective_slots(schedule)
    assert [slot.appointment_minute for slot in slots[:2]] == [480, 495]


def test_appointment_rule_2_bailey_welch_times():
    schedule = ScheduleGenerator(load_config()).generate(1, 10, 2)
    slots = first_elective_slots(schedule, n=3)
    assert [slot.appointment_minute for slot in slots] == [480, 480, 495]


def test_appointment_rule_3_blocking_times():
    schedule = ScheduleGenerator(load_config()).generate(1, 10, 3)
    slots = first_elective_slots(schedule)
    assert [slot.appointment_minute for slot in slots] == [480, 480, 510, 510]


def test_appointment_rule_4_benchmark_times():
    schedule = ScheduleGenerator(load_config()).generate(1, 10, 4)
    slots = first_elective_slots(schedule, n=2)
    assert slots[0].appointment_minute == 478.5
    assert slots[1].appointment_minute == 493.5


def test_objective_function_weights_are_correct():
    cfg = load_config()
    weights = cfg.objective_weights
    assert weights["elective"] == 1 / 168
    assert weights["urgent"] == 1 / 9


def test_no_negative_scan_durations():
    streams = RandomStreams(base_seed=42, replication=0)
    values = [streams.positive_normal("elective_durations", 15.0, 3.0) for _ in range(500)]
    assert min(values) > 0


def test_crn_same_replication_seed_reused_across_designs():
    seeds_a = make_stream_seeds(42, 7)
    seeds_b = make_stream_seeds(42, 7)
    seeds_c = make_stream_seeds(42, 8)
    assert seeds_a == seeds_b
    assert seeds_a != seeds_c


def test_antithetic_pairing_uses_complements():
    standard = RandomStreams(base_seed=42, replication=0, antithetic=False)
    anti = RandomStreams(base_seed=42, replication=0, antithetic=True)
    u = standard.uniform("elective_calls")
    v = anti.uniform("elective_calls")
    assert abs((u + v) - 1.0) < 1e-12

