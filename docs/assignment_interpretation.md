# Assignment Interpretation Checklist

This file maps the 2025-2026 radiology assignment requirements to the new pipeline.

| Requirement | Pipeline coverage |
| --- | --- |
| Single-server outpatient radiology department | `sma_sim.simulation.SimulationEngine` uses one server per open day. |
| Weekly cyclic schedule | `sma_sim.schedule.WeeklySchedule` repeats the same six-day schedule over simulated weeks. |
| Monday-Saturday only, no Sunday | `WeeklySchedule.validate()` rejects Sunday slots. |
| Thursday and Saturday half days | Schedule generation creates only morning sessions for days 3 and 5. |
| Slot length 15 minutes | `config/project_config.yaml` and `ScheduleGenerator`. |
| Current schedule 146 elective / 14 urgent | Strategy 1 with `U=14` validates to this capacity. |
| Urgent slots 10-20 inclusive | Full design matrix includes every count 10 through 20. |
| Three timing strategies | `ScheduleGenerator.generate(strategy=1|2|3, ...)`. |
| Elective calls Monday-Friday 08:00-17:00 | `SimulationEngine._generate_elective_patients`. |
| Elective FCFS slot assignment | `SimulationEngine._assign_elective_slots`. |
| Appointment rules 1-4 | `ScheduleGenerator._apply_appointment_rule`. |
| Elective no-shows, punctuality, positive scan durations | Separate random streams in `RandomStreams`; positive durations use truncated normals. |
| Urgent arrivals only during opening hours | `SimulationEngine._generate_urgent_patients`. |
| Urgent same-day slot or overtime | `SimulationEngine._assign_urgent_slots`. |
| Lunch is not overtime | Overtime compares last scan end with session end only. |
| Primary objective in hours | `SimulationEngine._execute_days` computes hours, then weights by `1/168` and `1/9`. |
| Warm-up and batch means in whole weeks | `sma_sim.analysis.compute_batch_results`. |
| CRN and antithetic variables | `sma_sim.random_streams.RandomStreams`. |
| Pareto front | `sma_sim.analysis.pareto_front` and `pareto_front.png`. |

Known current-report issue:
- Existing report text and README still describe a 96-design experiment over urgent slots 10-17. These claims must be replaced from new 132-design outputs before submission.
