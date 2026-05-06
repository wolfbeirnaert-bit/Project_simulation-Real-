# Fix List

Must fix before final submission:

1. Fill in group number, names, and student numbers on the report cover page.
2. Manually read the refreshed report for page-limit fit and narrative flow.
3. Inspect whether the full-run batch size and warm-up remain adequate for the unstable high urgent counts.
4. Decide whether to keep the Pareto front in the main text or move it to an appendix if the 15-page limit becomes tight.
5. Optionally run a longer confirmatory analysis on the final 13-14 urgent-slot candidate region.

Recently completed:

1. Ran `python -m sma_agents.run_pipeline --mode full` and generated `outputs/20260505_221519/`.
2. Replaced old report/README statements saying the experiment has 96 designs or urgent slots 10-17.
3. Reviewed full-run evidence for urgent slots 18-20 and documented that all 36 high-count designs were flagged.
4. Inserted the generated Pareto front into the LaTeX report.
5. Used `top_designs_comparison.csv` to frame the recommendation as a 13-14 urgent-slot region instead of overclaiming one exact optimum.

Should improve if time allows:

1. Add a short appendix describing the antithetic inverse-transform implementation.
2. Add a compact limitations paragraph about distributional assumptions and finite run length.
3. Consider rerunning top candidates with longer batches if relative precision is too high.
