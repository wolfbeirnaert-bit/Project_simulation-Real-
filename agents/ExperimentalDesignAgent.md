# ExperimentalDesignAgent

Define and execute the experimental design.

Responsibilities:
- Build the full factorial matrix: 3 strategies x 11 urgent counts x 4 appointment rules.
- Keep quick mode small and clearly labelled as non-confirmatory.
- Use common random numbers by replication and stream name.
- Keep urgent counts 18-20 in the design and mark instability only after evidence exists.

Deliverables:
- `outputs/<timestamp>/design_matrix.csv`
- `sma_agents/run_pipeline.py`
- design summary tables.
