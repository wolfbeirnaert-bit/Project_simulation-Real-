"""
Herberekent BMM_Representative_Designs.csv (standard) en
BMM_Antithetic_Designs.csv (antithetic) met de gecorrigeerde objectieffunctie.

- De 10 representative designs met U <= 17 zitten al in full_sweep_antithetic.csv.
  Voor de antithetische CSV worden die waarden direct overgenomen.
- S1-U18-R4 (niet in de sweep) wordt apart opnieuw gerund voor beide CSVs.
"""

import sys, os, random, math
import numpy as np
import pandas as pd
from scipy import stats

sys.path.append(os.path.join(os.getcwd(), "smaproject2026", "python-code"))
from simulation import Simulation
import helper

# ── Parameters ────────────────────────────────────────────────────────────────
WARMUP = 60
M      = 80
L      = 22
W_TOTAL = WARMUP + L * M   # 1820
SEED   = 42
ALPHA  = 0.05

def t_crit(df):
    return stats.t.ppf(1 - ALPHA / 2, df)

def bmm_stats(Dk):
    d_bar = float(np.mean(Dk))
    s2    = float(np.var(Dk, ddof=1))
    s     = math.sqrt(s2)
    eps   = t_crit(L - 1) * math.sqrt(s2 / L)
    return d_bar, s2, s, eps

def run_single(strategy, num_urgent, rule, antithetic):
    """Eén run, geeft L batch means terug."""
    helper.USE_ANTITHETIC = antithetic
    sim = Simulation("", W_TOTAL, 1, rule)
    sim.setupScenario(strategy, num_urgent, rule)
    random.seed(SEED)
    sim.runOneSimulation()
    data = np.array(sim.getWeeklyObjectiveValues()[WARMUP:])
    helper.USE_ANTITHETIC = False
    return np.array([np.mean(data[k*M:(k+1)*M]) for k in range(L)])

def run_antithetic_pair(strategy, num_urgent, rule):
    """Standaard + antithetische run, geeft gepaard gemiddelde terug."""
    Dk1 = run_single(strategy, num_urgent, rule, antithetic=False)
    Dk2 = run_single(strategy, num_urgent, rule, antithetic=True)
    return (Dk1 + Dk2) / 2.0

# ── 11 representative designs ─────────────────────────────────────────────────
representative = [
    (1, 14, 1),
    (1, 18, 4),   # niet in sweep → apart runnen
    (3, 17, 2),
    (1, 11, 3),
    (2, 17, 2),
    (3, 14, 3),
    (3, 17, 3),
    (3, 13, 3),
    (1, 14, 4),
    (2, 16, 1),
    (2, 13, 4),
]

# ── Laad full sweep voor snelle lookup (antithetisch) ─────────────────────────
sweep = pd.read_csv("full_sweep_antithetic.csv", sep=";", decimal=",")
sweep_idx = {
    (int(r.Strategy), int(r.Urgent_Slots), int(r.Rule)): r
    for _, r in sweep.iterrows()
}

# ─────────────────────────────────────────────────────────────────────────────
# 1.  BMM_Representative_Designs.csv  (standard, geen antithetisch)
# ─────────────────────────────────────────────────────────────────────────────
print("Herberekenen BMM_Representative_Designs.csv (standard)...")
std_rows = []
for s, u, r in representative:
    scenario = f"S{s}-U{u}-R{r}"
    print(f"  {scenario} ...")
    Dk = run_single(s, u, r, antithetic=False)
    d_bar, s2, sd, eps = bmm_stats(Dk)
    ci_lo, ci_hi = d_bar - eps, d_bar + eps
    std_rows.append({
        "Design":           scenario,
        "Avg_Obj (D_bar)":  round(d_bar, 4),
        "Var (S^2)":        round(s2,    4),
        "StdDev (S)":       round(sd,    4),
        "Half-Width (eps)": round(eps,   4),
        "95% CI":           f"[{ci_lo:.4f} ; {ci_hi:.4f}]".replace(".", ","),
        "Coeff of Var (CV)":round(sd / d_bar, 4),
        "Rel Precision (gamma)": round(eps / d_bar, 4),
    })

df_std = pd.DataFrame(std_rows)
df_std.to_csv("BMM_Representative_Designs.csv", index=False, sep=";", decimal=",")
print("  → BMM_Representative_Designs.csv opgeslagen\n")

# ─────────────────────────────────────────────────────────────────────────────
# 2.  BMM_Antithetic_Designs.csv
#     – voor U <= 17: direct uit full_sweep_antithetic.csv
#     – voor S1-U18-R4: apart runnen
# ─────────────────────────────────────────────────────────────────────────────
print("Herberekenen BMM_Antithetic_Designs.csv ...")
anti_rows = []
for s, u, r in representative:
    scenario = f"S{s}-U{u}-R{r}"
    key = (s, u, r)

    if key in sweep_idx:
        # Haal direct uit de full sweep (al correct berekend)
        row = sweep_idx[key]
        d_bar = float(row["Avg_OV"])
        s2    = float(row["Var"])
        sd    = float(row["StdDev"])
        eps   = float(row["Half_Width"])
        ci_lo = float(row["CI_Low"])
        ci_hi = float(row["CI_High"])
        cv    = float(row["CV"])
        gamma = float(row["Rel_Precision"])
        print(f"  {scenario} → overgenomen uit full sweep")
    else:
        # S1-U18-R4: apart runnen
        print(f"  {scenario} → apart runnen (niet in sweep)...")
        Dk = run_antithetic_pair(s, u, r)
        d_bar, s2, sd, eps = bmm_stats(Dk)
        ci_lo, ci_hi = d_bar - eps, d_bar + eps
        cv    = sd / d_bar
        gamma = eps / d_bar

    anti_rows.append({
        "Design":              scenario,
        "Avg_Obj (Y_bar)":     round(d_bar, 4),
        "Var (S^2_Y)":         round(s2,    4),
        "StdDev (S_Y)":        round(sd,    4),
        "Half-Width (eps)":    round(eps,   4),
        "95% CI":              f"[{ci_lo:.4f} ; {ci_hi:.4f}]".replace(".", ","),
        "Coeff of Var (CV)":   round(cv,    4),
        "Rel Precision (gamma)": round(gamma, 4),
    })

df_anti = pd.DataFrame(anti_rows)
df_anti.to_csv("BMM_Antithetic_Designs.csv", index=False, sep=";", decimal=",")
print("  → BMM_Antithetic_Designs.csv opgeslagen\n")

# ── Print resultaten ──────────────────────────────────────────────────────────
print("=" * 70)
print("BMM_Representative_Designs.csv (standard, gecorrigeerde OV):")
print(df_std.to_string(index=False))
print()
print("BMM_Antithetic_Designs.csv (antithetisch, gecorrigeerde OV):")
print(df_anti.to_string(index=False))
