# QA Report

## Critical Findings

1. The legacy report previously described a 96-design experiment over urgent slots 10-17. The full pipeline run now covers the required 132 designs over urgent slots 10-20, and the main README/report text has been refreshed with those results.
2. Existing legacy Python code uses global `random` and a broad scheduling pass. It does not provide separate random streams for CRN by source of randomness. The new package implements named streams and stable seed derivation.
3. Existing antithetic logic flips all calls to a global uniform generator, which is hard to audit by stream. The new `RandomStreams` class exposes explicit complements.
4. The current report claims appointment rules have minimal impact. This must be treated as a result-dependent conclusion, not an assumption, especially because the Maenhout paper reports appointment rules can matter.
5. Existing output files are not timestamped by run. The new pipeline writes every run to `outputs/YYYYMMDD_HHMMSS/`.

## Methodology Checks Added

- Whole-week warm-up and whole-week batch means.
- t-based confidence intervals for batch means.
- CRN-compatible paired batch comparisons.
- Pareto front between elective appointment waiting and urgent scan waiting.
- Instability flags for high urgent counts based on generated evidence.

## Manual Review Still Needed

- Inspect whether the full-run batch size and warm-up remain adequate for the unstable high urgent counts.
- Decide how much of the Pareto layer should remain in the main report versus appendix if the 15-page limit becomes tight.
- Confirm group names/student numbers on the cover page.
- Optionally run a longer confirmatory analysis on the final 13-14 urgent-slot candidate region.
