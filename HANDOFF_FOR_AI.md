# Handoff Document — Simulation Project (SMA F000941, 2025-2026)
> Written for: GPT / Codex or any AI assistant continuing this work  
> Project deadline: **13 May 2026**  
> GitHub repo: https://github.com/wolfbeirnaert-bit/Project_simulation-Real-  
> Language: Python (simulation) + LaTeX (report)

---

## 1. What this project is about

We are redesigning the cyclic appointment schedule of a **single-server outpatient radiology department** at a hospital. The simulation is already built and working (Python). Our job is to run the right statistical experiments on it and write a rigorous academic report.

The department serves two patient types:
- **Elective patients**: call ahead, get an appointment slot, may be unpunctual or no-show
- **Urgent patients**: arrive without appointment, must be served same day or in overtime

### The three design decisions we are investigating
| Factor | Levels |
|--------|--------|
| Timing Strategy (where urgent slots go) | 1 = end-of-block, 2 = evenly spread, 3 = after every 6 elective slots |
| Urgent Slot Capacity | 10, 11, 12, 13, 14, 15, 16, 17 per week |
| Appointment Rule | 1 = FCFS, 2 = Bailey-Welch (K=2), 3 = Blocking (B=2), 4 = Benchmarking (kσ=0.5) |

Full factorial: 3 × 8 × 4 = **96 configurations**. U=18,19,20 were excluded (systemically unstable — proven via antithetic variates blowing up).

### Primary objective function (MINIMIZE)
```
OV = (1/168) * avg_elective_appointment_WT + (1/9) * avg_urgent_scan_WT
```
- w_e = 1/168 (1 week normalized)
- w_u = 1/9 (9 hours normalized)
- **Elective scan WT and overtime are SECONDARY objectives** — only used for tiebreaking

---

## 2. Key files and what they do

### Simulation code
- `smaproject2026/python-code/simulation.py` — the main DES simulator
  - `setupScenario(strategy, num_urgent, rule)` — configure a design
  - `runOneSimulation()` — run it
  - `getWeeklyObjectiveValues()` — returns list of weekly OV values (post warm-up)
  - **BUG WAS FIXED**: previously `getWeeklyObjectiveValues()` wrongly added `movingAvgElectiveScanWT` to the OV. This was removed. The correct formula only uses `movingAvgElectiveAppWT` and `movingAvgUrgentScanWT`.
- `smaproject2026/python-code/helper.py` — random number generation
  - `USE_ANTITHETIC = False` flag — set to True to flip U → 1-U for antithetic variates
  - `get_uniform()` returns `1 - u` when antithetic mode is on

### Experiment scripts
| File | What it does |
|------|-------------|
| `run_full_sweep.py` | Runs all 96 designs with antithetic variates, saves to `full_sweep_antithetic.csv` |
| `update_representative_csvs.py` | Re-runs 11 representative designs → saves `BMM_Representative_Designs.csv` (standard) and `BMM_Antithetic_Designs.csv` |
| `batch_means_analysis.py` | Autocorrelation analysis to justify batch size M=80 |
| `robust_warmup_analysis.py` | Welch's method to justify warm-up W=60 |
| `run_antithetic_bmm.py` | Earlier antithetic BMM runner (superseded by update_representative_csvs.py) |

### Data files
| File | Contents |
|------|----------|
| `full_sweep_antithetic.csv` | All 96 designs, sorted by OV ascending, with CI metrics (sep=`;`, decimal=`,`) |
| `BMM_Representative_Designs.csv` | 11 representative designs, standard run (no antithetic) |
| `BMM_Antithetic_Designs.csv` | Same 11 designs, antithetic run |

### Report
- `report.tex` — **the main LaTeX report** (compile with pdfLaTeX in Overleaf)
- `Simulation_Project_Report.md` — older markdown version (less current than .tex)

---

## 3. Statistical methodology used

### Warm-up: Welch's method
- Applied to 11 representative designs
- Moving average of OV plotted per week
- Worst-case convergence ~63 weeks → conservative **W_warmup = 60 weeks**

### Batch Means Method (BMM)
- **M = 80 weeks** per batch (autocorrelation drops below 0.01 at lag 80)
- **L = 22 batches** (gives γ < 5% for stable designs)
- Total run: W_total = 60 + 22×80 = **1820 weeks**
- Confidence intervals: t-distribution with df = L-1 = 21, t_{0.025,21} ≈ 2.0796
- Seed = 42 for reproducibility

### Variance reduction: Antithetic Variates
- For every standard run with sequence U, a paired run with 1-U is generated
- Paired average: Y_k = (X_k + X'_k) / 2
- For stable designs, variance is roughly halved (e.g. S1-U11-R3: Var 0.0003 → 0.0001)
- **Critical finding**: S1-U18-R4 standard mean = 0.914, antithetic mean = 2.374 (variance EXPLODES) → proves U≥18 is fundamentally unstable due to queue convexity

### CI overlap criterion
- Two designs are statistically significantly different if their 95% CIs do NOT overlap
- If CIs overlap → cannot distinguish → use secondary objectives to break tie

---

## 4. Key results already computed

### Top 5 designs (from full_sweep_antithetic.csv)
| Rank | Design | Strategy | Urgent | Rule | OV (Ȳ) | ε | 95% CI |
|------|--------|----------|--------|------|---------|---|--------|
| 1 | S3-U11-R4 | 3 | 11 | 4 | 0.4311 | 0.0040 | [0.4271 ; 0.4352] |
| 2 | S3-U11-R2 | 3 | 11 | 2 | 0.4321 | 0.0040 | [0.4280 ; 0.4361] |
| 3 | S3-U11-R1 | 3 | 11 | 1 | 0.4325 | 0.0040 | [0.4284 ; 0.4365] |
| 4 | S3-U11-R3 | 3 | 11 | 3 | 0.4344 | 0.0041 | [0.4304 ; 0.4385] |
| 5 | S3-U13-R4 | 3 | 13 | 4 | 0.4357 | 0.0069 | [0.4288 ; 0.4425] |

### Three main conclusions already drawn
1. **Strategy 3 dominates**: entire top 16 is Strategy 3. S3 CI lies entirely below S1 and S2 best designs → statistically significant.
2. **11 urgent slots is optimal**: within S3, U=11 is best. OV rises sharply for U≥15. U≥18 is unstable.
3. **Appointment rules have negligible impact**: top 4 all overlap in CI (spread of only 0.0033 across rules).

### Current schedule benchmark
S1-U14-R1: Ȳ ≈ 0.488 → **~11% worse** than the best design S3-U11-R4.

---

## 5. Current state of the LaTeX report (report.tex)

### Sections present
| Section | Status | Notes |
|---------|--------|-------|
| Cover page | ✅ Done | Names/group number are PLACEHOLDERS — must be filled in |
| 1. Introduction | ✅ Done | System description, hypotheses (H0/HA format), factor table, research overview |
| 2. Statistical Analysis & Warm-up | ✅ Done | Welch's method + BMM baseline table (Table 3) |
| 3. Variance Reduction | ✅ Done | Antithetic variates explanation + antithetic BMM table (Table 4) + exclusion of U≥18 |
| 4. Experimental Design (Screening) | ✅ Done | Objective function, top-20 table, 3 observations with supporting tables |
| 5. Comparative Analysis | ✅ Done | CI overlap comparison, strategy comparison, recommendation box |
| 6. Conclusion | ✅ Done | 4 main conclusions |
| References | ❌ MISSING | Required by assignment — must add |

### Known typo in report.tex
In the top-4 CI table (`tab:top4_ci`), S3-U11-R2 has `\epsilon = 0.4040` — this should be `0.0040`. Fix this before submission.

---

## 6. What still needs to be done (priority order)

### CRITICAL — must do before 13 May

**A. Fill in names and group number on cover page**
In `report.tex`, replace all `[Naam X]` and `[Studentnummer]` and `[GROEPSNUMMER]` placeholders.

**B. Add references section**
The assignment explicitly requires "a complete list of cited references organized by author". Minimum references needed:
- Bailey & Welch (1952) — Bailey-Welch appointment rule
- Welch (1983) — Welch's warm-up method
- Law (2015) — Simulation Modeling and Analysis (standard textbook for BMM)
- Dudewicz & Dalal (1975) — Ranking & Selection (if used)

**C. Fix typo in Tab. top4_ci**: `0.4040` → `0.0040` for S3-U11-R2 epsilon

**D. Secondary objectives tiebreaking**
The assignment says elective scan WT and overtime are secondary objectives for tiebreaking. The top 4 S3-U11 designs are statistically indistinguishable on primary OV. You MUST run a tiebreak:
- Collect avg_elective_scan_WT and avg_overtime for the 4 S3-U11 designs
- The simulation already tracks these — see `sim.avgElectiveScanWT` and `sim.avgOvertime`
- Add a tiebreaking table to Section 5 (Comparative Analysis)

**E. Add simulation model description section**
The assignment requires describing "the state descriptor, events, simulation time". Currently missing. Add a section (can go between Introduction and Statistical Analysis) covering:
- State variables: current time, patient queues, slot occupancy
- Events: elective arrival (phone call), elective physical arrival, urgent arrival, scan start, scan end
- Time advance: next-event approach
- Run length: 1820 weeks

### IMPORTANT — for a high grade

**F. Plots/figures** (assignment criterion 5 requires figures with captions)
Currently zero figures in report.tex. The PNG files already exist in the project folder:
- `robust_welch_comparison.png` → add to warm-up section to visually justify W=60
- `acf_batch_size.png` → add to BMM section to visually justify M=80
- `batch_means_plot.png` → can be added to BMM section

To include images in LaTeX: `\includegraphics[width=\linewidth]{robust_welch_comparison.png}` — you need to upload the PNGs to Overleaf alongside the .tex file.

**G. Dudewicz-Dalal Ranking & Selection** (optional but impressive)
The previous year's group (Group 3) did this. It formally selects the best design with a probability-of-correct-selection guarantee. A script for this already exists in:
`Project_previous_year/wetransfer_simulation_2026-04-28_1223/Extra_replications_Dudewicz_Dalal.py`
This needs adaptation to our simulation setup.

---

## 7. How to run the simulation

```python
import sys, os, random
sys.path.append("smaproject2026/python-code")
from simulation import Simulation
import helper

# Standard run
sim = Simulation("", 1820, 1, rule=1)
sim.setupScenario(strategy=3, num_urgent=11, rule=1)
random.seed(42)
sim.runOneSimulation()
weekly_ovs = sim.getWeeklyObjectiveValues()[60:]  # skip warm-up

# Antithetic run: set helper.USE_ANTITHETIC = True before running
helper.USE_ANTITHETIC = True
# ... run again with same seed ...
helper.USE_ANTITHETIC = False
```

BMM parameters: WARMUP=60, M=80, L=22, SEED=42
Batch mean k: mean of weekly_ovs[k*80 : (k+1)*80] for k in range(22)

---

## 8. Important decisions already made and why

| Decision | Reason |
|----------|--------|
| Exclude U=18,19,20 | Antithetic run of S1-U18-R4 blows up (Ȳ=2.374 vs 0.914 standard) — queue convexity causes total collapse |
| W_warmup = 60 weeks | Conservative choice based on worst-case Welch convergence at ~63 weeks |
| M = 80 weeks | Autocorrelation analysis shows lag-80 correlation < 0.01 |
| L = 22 batches | Gives γ < 5% for all stable designs |
| Full-factorial not fractional | Only 96 designs, computationally feasible; avoids aliasing of interaction effects |
| Antithetic variates chosen over CRN | Only one system configuration per run; CRN requires comparing two systems |
| Primary OV = appointment WT + urgent scan WT only | Assignment spec 2.2 explicitly: "elective scan WT and overtime are secondary objectives" |

---

## 9. File structure

```
Simulation_Project/
├── report.tex                          ← MAIN REPORT (LaTeX)
├── full_sweep_antithetic.csv           ← All 96 designs results
├── BMM_Representative_Designs.csv      ← 11 representative designs, standard BMM
├── BMM_Antithetic_Designs.csv          ← 11 representative designs, antithetic BMM
├── run_full_sweep.py                   ← Script that generated full_sweep_antithetic.csv
├── update_representative_csvs.py       ← Script that regenerated the two BMM CSVs
├── robust_welch_comparison.png         ← Welch plot (add to report)
├── acf_batch_size.png                  ← ACF plot (add to report)
├── batch_means_plot.png                ← Batch means plot (add to report)
├── smaproject2026/python-code/
│   ├── simulation.py                   ← DES simulator (bug fixed in getWeeklyObjectiveValues)
│   ├── helper.py                       ← RNG + USE_ANTITHETIC flag
│   ├── patient.py                      ← Patient class
│   └── slot.py                         ← Slot class
└── Project_previous_year/
    └── Group_3_Assignment_Report.pdf   ← Previous year reference report
```

---

## 10. CSV format note

Both CSV files use **semicolon separator** and **comma as decimal separator** (Dutch locale):
```python
pd.read_csv("full_sweep_antithetic.csv", sep=";", decimal=",")
```
