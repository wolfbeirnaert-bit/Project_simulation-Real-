# Report Improvement Plan

## Introduction

- Replace 10-17 language with 10-20 inclusive.
- State hypotheses for strategy, urgent-slot count, appointment rule, and instability of high urgent counts.
- Make clear that the goal is methodological comparison, not unsupported exact optimality.

## System And Model

- Add a compact state descriptor: schedule, elective backlog, urgent same-day slots, server availability, patient records, random streams.
- Describe event logic: elective call, urgent arrival, appointment assignment, day execution, scan start/end, overtime.
- State that minutes are used internally and outputs are converted to hours/days.

## Experimental Design

- Present the full 132-design matrix.
- Explain quick mode is only a debugging mode.
- Explain CRN and antithetic variables by named random stream.

## Output Analysis

- Include Welch plot, autocorrelation plot, batch means parameters, and relative precision.
- Discuss high urgent counts 18-20 from actual generated evidence instead of excluding them upfront.

## Results

- Insert generated top-design table and factor effects.
- Use paired comparisons for the strongest claims.
- Say "not statistically distinguishable" when intervals or paired tests do not support ranking.

## Pareto And Conclusion

- Add the Pareto front as the methodological improvement inspired by Maenhout.
- Use secondary objectives only for interpretation and tie-breaking.
- Keep limitations explicit: simulation assumptions, distribution fitting limits, and no guarantee of global optimality.
