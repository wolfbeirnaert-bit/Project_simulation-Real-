import sys
import os
import random
import math
import time
import numpy as np
import pandas as pd
from scipy import stats

sys.path.append(os.path.join(os.getcwd(), "smaproject2026", "python-code"))
from simulation import Simulation
import helper

# --- Parameters (zelfde als bestaande BMM scripts) ---
WARMUP = 60       # warm-up weken (bepaald via Welch)
M = 80            # batch grootte (weken per batch)
L = 22            # aantal batches
W_TOTAL = WARMUP + (L * M)   # = 1820 weken totaal
SEED = 42
ALPHA = 0.05
USE_ANTITHETIC = True   # False = sneller, True = kleinere variantie

# 11 eerder geanalyseerde designs (ter referentie in output)
REPRESENTATIVE = {
    (1, 14, 1), (1, 18, 4), (3, 17, 2), (1, 11, 3), (2, 17, 2),
    (3, 14, 3), (3, 17, 3), (3, 13, 3), (1, 14, 4), (2, 16, 1), (2, 13, 4)
}


def t_crit(df):
    return stats.t.ppf(1 - ALPHA / 2, df)


def run_design(strategy, num_urgent, rule):
    """
    Voer één design uit en geef de L batch means terug.
    Bij antithetische variaties worden twee runs gepaard en gemiddeld.
    """
    if USE_ANTITHETIC:
        helper.USE_ANTITHETIC = False
        sim1 = Simulation("", W_TOTAL, 1, rule)
        sim1.setupScenario(strategy, num_urgent, rule)
        random.seed(SEED)
        sim1.runOneSimulation()
        data1 = np.array(sim1.getWeeklyObjectiveValues()[WARMUP:])
        Dk1 = np.array([np.mean(data1[k * M:(k + 1) * M]) for k in range(L)])

        helper.USE_ANTITHETIC = True
        sim2 = Simulation("", W_TOTAL, 1, rule)
        sim2.setupScenario(strategy, num_urgent, rule)
        random.seed(SEED)   # zelfde seed als run 1 (vereist voor antithetisch)
        sim2.runOneSimulation()
        data2 = np.array(sim2.getWeeklyObjectiveValues()[WARMUP:])
        Dk2 = np.array([np.mean(data2[k * M:(k + 1) * M]) for k in range(L)])

        helper.USE_ANTITHETIC = False   # reset voor volgende run
        return (Dk1 + Dk2) / 2.0
    else:
        helper.USE_ANTITHETIC = False
        sim = Simulation("", W_TOTAL, 1, rule)
        sim.setupScenario(strategy, num_urgent, rule)
        random.seed(SEED)
        sim.runOneSimulation()
        data = np.array(sim.getWeeklyObjectiveValues()[WARMUP:])
        return np.array([np.mean(data[k * M:(k + 1) * M]) for k in range(L)])


# --- Sweep over alle designs: strategie 1-3, urgent slots 10-17, rules 1-4 ---
all_designs = [
    (s, u, r)
    for s in range(1, 4)
    for u in range(10, 18)   # 10 t/m 17 (18, 19, 20 uitgesloten)
    for r in range(1, 5)
]

results = []
total = len(all_designs)
start_time = time.time()

print(f"Full sweep: {total} designs  |  WARMUP={WARMUP}w  M={M}w  L={L}  antithetic={USE_ANTITHETIC}\n")

for i, (strategy, num_urgent, rule) in enumerate(all_designs, start=1):
    scenario = f"S{strategy}-U{num_urgent}-R{rule}"
    elapsed = time.time() - start_time
    eta = (elapsed / i) * (total - i) if i > 1 else 0
    print(f"[{i:3d}/{total}] {scenario}  |  elapsed {elapsed:5.0f}s  ETA {eta:5.0f}s")

    Dk = run_design(strategy, num_urgent, rule)

    df = L - 1
    t = t_crit(df)
    d_bar = float(np.mean(Dk))
    s2 = float(np.var(Dk, ddof=1))
    s = math.sqrt(s2)
    eps = t * math.sqrt(s2 / L)
    ci_low = d_bar - eps
    ci_high = d_bar + eps

    results.append({
        "Design": scenario,
        "Strategy": strategy,
        "Urgent_Slots": num_urgent,
        "Rule": rule,
        "Avg_OV": round(d_bar, 4),
        "Var": round(s2, 6),
        "StdDev": round(s, 4),
        "Half_Width": round(eps, 4),
        "CI_Low": round(ci_low, 4),
        "CI_High": round(ci_high, 4),
        "CV": round(s / d_bar, 4),
        "Rel_Precision": round(eps / d_bar, 4),
        "Was_Representative": (strategy, num_urgent, rule) in REPRESENTATIVE,
    })

total_time = time.time() - start_time
print(f"\nKlaar in {total_time:.1f}s")

# --- Resultaten opslaan ---
df_results = pd.DataFrame(results).sort_values("Avg_OV").reset_index(drop=True)
df_results.insert(0, "Rank", df_results.index + 1)

suffix = "antithetic" if USE_ANTITHETIC else "standard"
csv_path = f"full_sweep_{suffix}.csv"
df_results.to_csv(csv_path, index=False, sep=";", decimal=",")
print(f"Opgeslagen: {csv_path}")

# --- Top 15 printen ---
print(f"\nTop 15 designs (laagste OV)  [antithetic={USE_ANTITHETIC}]")
print(f"{'Rank':<5} {'Design':<16} {'Avg_OV':>8} {'Half_Width':>11} {'95% CI'}")
print("-" * 65)
for _, row in df_results.head(15).iterrows():
    ci = f"[{row['CI_Low']:.4f} ; {row['CI_High']:.4f}]"
    prev = " *" if row["Was_Representative"] else ""
    print(f"{int(row['Rank']):<5} {row['Design']:<16} {row['Avg_OV']:>8.4f} {row['Half_Width']:>11.4f}  {ci}{prev}")

print("\n* = was al in eerder geanalyseerde representative designs")

# --- Beste per strategie ---
print("\nBeste design per strategie:")
for s in range(1, 4):
    best = df_results[df_results["Strategy"] == s].iloc[0]
    print(f"  Strategie {s}: {best['Design']}  OV={best['Avg_OV']:.4f}")

# --- Beste per rule ---
print("\nBeste design per appointment rule:")
for r in range(1, 5):
    best = df_results[df_results["Rule"] == r].iloc[0]
    print(f"  Rule {r}: {best['Design']}  OV={best['Avg_OV']:.4f}")
