# ScheduleGeneratorAgent

Generate valid cyclic weekly schedules for Strategy 1, Strategy 2, and Strategy 3.

Responsibilities:
- Support urgent slot counts 10-20 inclusive.
- Enforce no Sunday scheduling and Thursday/Saturday half-day logic.
- Ensure all 160 weekly open slots are elective or urgent.
- Reproduce the current S1-U14 146 elective / 14 urgent structure as closely as specified.
- Generate heatmaps for selected schedules.

Deliverables:
- `sma_sim/schedule.py`
- schedule validation tests
- `outputs/<timestamp>/figures/schedule_*.png`
