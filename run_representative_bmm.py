import sys
import os
import random
import math
import numpy as np
import pandas as pd
from scipy import stats

sys.path.append(os.path.join(os.getcwd(), "smaproject2026", "python-code"))
from simulation import Simulation

WARMUP = 60
M = 80
L = 22
W_TOTAL = WARMUP + (L * M)
SEED = 42
ALPHA = 0.05

designs = [
    (1, 14, 1), # Base
    (1, 18, 4),
    (3, 17, 2),
    (1, 11, 3),
    (2, 17, 2),
    (3, 14, 3),
    (3, 17, 3),
    (3, 13, 3),
    (1, 14, 4),
    (2, 16, 1),
    (2, 13, 4)
]

def t_crit(df):
    return stats.t.ppf(1 - ALPHA / 2, df)

results = []

print("Running BMM on representative designs...")
for strategy, num_urgent, rule in designs:
    scenario = f"S{strategy}-U{num_urgent}-R{rule}"
    print(f"Running {scenario}...")
    
    sim = Simulation("", W_TOTAL, 1, rule)
    sim.setupScenario(strategy, num_urgent, rule)
    random.seed(SEED)
    sim.runOneSimulation()
    
    data = np.array(sim.getWeeklyObjectiveValues()[WARMUP:])
    
    # Calculate batch means
    Dk = [np.mean(data[k * M:(k + 1) * M]) for k in range(L)]
    Dk = np.array(Dk)
    
    df = L - 1
    t = t_crit(df)
    
    d_bar = np.mean(Dk)
    s2 = np.var(Dk, ddof=1)
    s = math.sqrt(s2)
    var_dbar = s2 / L
    eps = t * math.sqrt(var_dbar)
    
    ci_low = d_bar - eps
    ci_high = d_bar + eps
    
    cv = s / d_bar
    rel_prec = eps / d_bar
    
    results.append({
        "Design": scenario,
        "Avg_Obj (D_bar)": round(d_bar, 4),
        "Var (S^2)": round(s2, 4),
        "StdDev (S)": round(s, 4),
        "Half-Width (eps)": round(eps, 4),
        "95% CI": f"[{ci_low:.4f} ; {ci_high:.4f}]".replace('.', ','),
        "Coeff of Var (CV)": round(cv, 4),
        "Rel Precision (gamma)": round(rel_prec, 4)
    })

df_results = pd.DataFrame(results)

# Save to CSV
csv_path = "BMM_Representative_Designs.csv"
df_results.to_csv(csv_path, index=False, sep=';', decimal=',')
print(f"Saved CSV to {csv_path}")

# Save to Markdown
md_path = "BMM_Representative_Designs.md"
with open(md_path, "w") as f:
    f.write("# BMM Results on 11 Representative Designs\n\n")
    f.write(f"Parameters: L = {L} batches, M = {M} weeks, Warm-up = {WARMUP} weeks.\n\n")
    f.write(df_results.to_markdown(index=False))
print(f"Saved Markdown to {md_path}")
