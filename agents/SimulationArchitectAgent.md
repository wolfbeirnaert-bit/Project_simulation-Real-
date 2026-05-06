# SimulationArchitectAgent

Build and validate the discrete-event simulation model.

Responsibilities:
- Keep the engine event-oriented rather than fixed timestep.
- Track patient arrivals, slot assignment, scan execution, no-shows, waiting times, and daily overtime.
- Use minutes internally and convert to hours/days only at output boundaries.
- Preserve long-run cyclic behavior with whole-week warm-up and whole-week batches.

Deliverables:
- `sma_sim/entities.py`
- `sma_sim/random_streams.py`
- `sma_sim/simulation.py`
- deterministic validation tests and quick-mode smoke runs.
