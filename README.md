# Reorganisation of an Outpatient Radiology Department

This repository contains the simulation models, data analysis scripts, and final report assets for the **Simulation Modelling and Analysis (2025-2026)** course project.

The goal of this study is to analyze and optimize the performance of an outpatient radiology department using discrete-event simulation. By redesigning the capacity distribution (urgent vs. elective slots) and the timing of urgent slots, we aim to minimize the weighted waiting times for both urgent and elective patients.

## 📂 Repository Structure

- `smaproject2026/`
  - `cpp-code/`: The core discrete-event simulation models written in C++ for maximum performance.
  - `python-code/`: Python implementations and helper scripts for the simulation logic.
- `*.py` (Root Directory): Data analysis scripts used for warm-up analysis, batch means processing, variance reduction (Antithetic Variables), and full screening sweeps.
  - `batch_means_analysis.py`
  - `robust_warmup_analysis.py`
  - `run_full_sweep.py`
  - `run_antithetic_bmm.py`
  - `generate_report_pdf.py`
- `report.tex`: The LaTeX source code for the final simulation report.
- `Simulation_Project_Report.md`: A markdown version of the final simulation report.
- `*.csv`: Output data files containing the results of the simulation sweeps and variance reduction analysis.
- `sma_sim/` and `sma_agents/`: The newer reproducible Python pipeline used for the 132-design screening.
- `outputs/20260505_221519/`: Latest full run output folder.

## 🚀 Key Findings & Recommendations

After evaluating all 132 required appointment schedule configurations across three timing strategies, eleven urgent slot counts (10-20), and four appointment rules, the main conclusions are:

1. **Best Timing Region:** Strategy 3 (placing an urgent slot after every 6 consecutive elective slots) gives the strongest overall region.
2. **Best Capacity Region:** 13-14 urgent slots is the best compromise region. The lowest point estimate is S3-U13-R4.
3. **High Urgent Counts:** Urgent slot counts 18-20 were tested, not silently excluded. All 36 corresponding designs were flagged as unstable or precision-problematic.
4. **Appointment Rules:** Rule 4 gives the lowest point estimate in the best region, but appointment-rule effects are smaller than the timing and urgent-capacity effects.
5. **Recommended Operating Region:** **Strategy 3 with 13-14 urgent slots**, with S3-U13-R4 as the lowest point estimate and S3-U14-R4 as a nearby trade-off option with lower urgent waiting.

For the new pipeline workflow and commands, see `README_AGENTIC_PIPELINE.md`.

## 📄 Generating the Report

To generate the PDF version of the report, you can:
1. Compile the LaTeX document locally using `pdflatex report.tex` (requires a full TeX Live / TinyTeX installation with `multirow`, `babel-english`, etc.).
2. Generate it from Markdown using the provided python script: `python3 generate_report_pdf.py` (requires `reportlab`).
3. Or view the pre-compiled `report.pdf` (if available) or read `Simulation_Project_Report.md` directly on GitHub.
