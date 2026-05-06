# Methodology Draft

This `full` run evaluates a long-run cyclic steady-state policy, not a one-day terminating system. The weekly slot pattern repeats, elective appointment backlog may carry over between weeks, and output analysis therefore uses whole-week warm-up and whole-week batch means.

The experiment uses common random numbers by deriving stream seeds from the base seed, replication index, and stream name. Separate streams are used for elective calls, urgent arrivals, no-shows, punctuality, elective durations, urgent scan type, and urgent durations. Antithetic runs reuse the same stream seeds and replace each generated uniform variate `U` by `1-U` before inverse-transform sampling.

The full confirmatory design covers all assignment-required urgent slot counts from 10 through 20 for all three timing strategies and four appointment rules. Counts 18-20 are evaluated and may only be marked unstable after the output analysis indicates excessive waiting growth, poor precision, or saturation.
