# Reorganisation of an Outpatient Radiology Department

This repository contains the simulation models, data analysis scripts, and final report for the **Simulation Modelling and Analysis (2025-2026)** course project. 

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

## 🚀 Key Findings & Recommendations

After evaluating 96 appointment schedule configurations across three timing strategies, eight urgent slot counts (10–17), and four appointment rules, the main conclusions are:

1. **Optimal Timing Strategy:** Strategy 3 (placing an urgent slot after every 6 consecutive elective slots) consistently outperforms the alternatives.
2. **Optimal Capacity:** 11 urgent slots is the ideal capacity. Configurations with 16 or more urgent slots show severe systemic instability.
3. **Appointment Rules:** Have negligible impact on the primary objective.
4. **Recommended Configuration:** **Strategy 3 with 11 urgent slots (Rule 4 / Benchmarking)**, representing an 11% improvement over the current baseline schedule.

## 📄 Generating the Report

To generate the PDF version of the report, you can:
1. Compile the LaTeX document locally using `pdflatex report.tex` (requires a full TeX Live / TinyTeX installation with `multirow`, `babel-english`, etc.).
2. Generate it from Markdown using the provided python script: `python3 generate_report_pdf.py` (requires `reportlab`).
3. Or view the pre-compiled `report.pdf` (if available) or read `Simulation_Project_Report.md` directly on GitHub.
