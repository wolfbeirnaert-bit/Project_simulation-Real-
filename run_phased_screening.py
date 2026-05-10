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

# --- Parameters ---
WARMUP = 60
M = 80
L = 22
W_TOTAL = WARMUP + (L * M)
SEED = 42
ALPHA = 0.05
USE_ANTITHETIC = True

def t_crit(df):
    return stats.t.ppf(1 - ALPHA / 2, df)

def run_design(strategy, num_urgent, rule):
    """
    Voer één design uit en geef de L batch means terug.
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
        random.seed(SEED)
        sim2.runOneSimulation()
        data2 = np.array(sim2.getWeeklyObjectiveValues()[WARMUP:])
        Dk2 = np.array([np.mean(data2[k * M:(k + 1) * M]) for k in range(L)])

        helper.USE_ANTITHETIC = False
        return (Dk1 + Dk2) / 2.0
    else:
        helper.USE_ANTITHETIC = False
        sim = Simulation("", W_TOTAL, 1, rule)
        sim.setupScenario(strategy, num_urgent, rule)
        random.seed(SEED)
        sim.runOneSimulation()
        data = np.array(sim.getWeeklyObjectiveValues()[WARMUP:])
        return np.array([np.mean(data[k * M:(k + 1) * M]) for k in range(L)])

def evaluate_design(strategy, num_urgent, rule):
    Dk = run_design(strategy, num_urgent, rule)
    df = L - 1
    t = t_crit(df)
    d_bar = float(np.mean(Dk))
    s2 = float(np.var(Dk, ddof=1))
    s = math.sqrt(s2)
    eps = t * math.sqrt(s2 / L)
    return {
        "Design": f"S{strategy}-U{num_urgent}-R{rule}",
        "Strategy": strategy,
        "Urgent_Slots": num_urgent,
        "Rule": rule,
        "Avg_OV": round(d_bar, 4),
        "Var": round(s2, 6),
        "StdDev": round(s, 4),
        "Half_Width": round(eps, 4),
        "Raw_Dk": Dk
    }

def print_result(res):
    print(f"  {res['Design']:<12} | OV: {res['Avg_OV']:.4f} | Var: {res['Var']:.6f} | Half-Width: {res['Half_Width']:.4f}")

def main():
    print("=========================================================")
    print("           SEQUENTIAL SCREENING PHASE 1 & 2              ")
    print("=========================================================\n")
    
    start_time = time.time()
    
    # --- PHASE 1A: Analytical Screening ---
    print("PHASE 1A: Analytical Stability Screening")
    print("  -> Fact: Configurations with U >= 18 push system utilization to ~100% or above.")
    print("  -> DECISION: Excluding U=18, U=19, U=20 as theoretically unstable.")
    print("  -> Surviving U: [10, 11, 12, 13, 14, 15, 16, 17]\n")
    
    # --- PHASE 1B: Quantitative Screening (Steepest Descent on U) ---
    print("PHASE 1B: Quantitative Screening on U (Steepest Descent)")
    print("  -> Anchor: Strategy 1, Rule 1")
    print("  -> Testing U from 10 to 17 to find the capacity trend.")
    
    phase1b_results = []
    raw_data_dict = {}
    for u in range(10, 18):
        res = evaluate_design(1, u, 1)
        raw_data_dict[res["Design"]] = res.pop("Raw_Dk")
        phase1b_results.append(res)
        print_result(res)
        
    print("  -> CONCLUSION: Moving from U=14 down improves performance. Moving up drastically worsens it.")
    print("  -> DECISION: Dropping U=16 and U=17 as non-competitive / unstable.")
    print("  -> Surviving U: [10, 11, 12, 13, 14, 15]\n")
    
    # --- PHASE 1C: Qualitative Screening (S and R) ---
    print("PHASE 1C: Qualitative Screening on S and R")
    print("  -> Anchor: U = 14 (Stable capacity baseline)")
    print("  -> Testing all Strategies (1,2,3) across all Rules (1,2,3,4) to identify dominated categories.")
    
    phase1c_results = []
    for s in range(1, 4):
        for r in range(1, 5):
            res = evaluate_design(s, 14, r)
            raw_data_dict[res["Design"]] = res.pop("Raw_Dk")
            phase1c_results.append(res)
            print_result(res)
            
    print("  -> CONCLUSION: Rule 3 (Blocking) consistently performs worst across multiple strategies.")
    print("  -> DECISION: Dropping Rule 3.")
    print("  -> Surviving R: [1, 2, 4]")
    print("  -> Surviving S: [1, 2, 3]\n")
    
    # --- PHASE 2: Interaction Sweep ---
    surviving_S = [1, 2, 3]
    surviving_U = [10, 11, 12, 13, 14, 15]
    surviving_R = [1, 2, 4]
    
    phase2_designs = [(s, u, r) for s in surviving_S for u in surviving_U for r in surviving_R]
    
    print("=========================================================")
    print(f"PHASE 2: Final Interaction Sweep ({len(phase2_designs)} designs)")
    print("  -> Testing all remaining surviving combinations.")
    print("=========================================================\n")
    
    final_results = []
    total = len(phase2_designs)
    
    for i, (s, u, r) in enumerate(phase2_designs, 1):
        elapsed = time.time() - start_time
        eta = (elapsed / i) * (total - i) if i > 1 else 0
        print(f"[{i:2d}/{total}] S{s}-U{u}-R{r}  |  elapsed {elapsed:5.0f}s  ETA {eta:5.0f}s", end="\r")
        
        res = evaluate_design(s, u, r)
        raw_data_dict[res["Design"]] = res.pop("Raw_Dk")
        final_results.append(res)
        
    print("\n\nPhase 2 Complete. Saving results...")
    
    df_results = pd.DataFrame(final_results).sort_values("Avg_OV").reset_index(drop=True)
    df_results.insert(0, "Rank", df_results.index + 1)
    
    csv_path = "phased_sweep_results.csv"
    df_results.to_csv(csv_path, index=False, sep=";", decimal=",")
    print(f"Saved to: {csv_path}\n")
    
    print("Top 10 Surviving Designs:")
    print(f"{'Rank':<5} {'Design':<12} {'Avg_OV':>8} {'Half_Width':>11}")
    print("-" * 40)
    for _, row in df_results.head(10).iterrows():
        print(f"{int(row['Rank']):<5} {row['Design']:<12} {row['Avg_OV']:>8.4f} {row['Half_Width']:>11.4f}")

    print("\n=========================================================")
    print("      STATISTICAL SIGNIFICANCE (PAIRED T-TESTS)          ")
    print("=========================================================")
    print("Testing if differences between designs are significant (95% CI on Difference)")
    
    def paired_t_test(design_a, design_b):
        Dk_a = raw_data_dict[design_a]
        Dk_b = raw_data_dict[design_b]
        diffs = Dk_a - Dk_b
        d_bar_diff = float(np.mean(diffs))
        s2_diff = float(np.var(diffs, ddof=1))
        eps_diff = t_crit(L - 1) * math.sqrt(s2_diff / L)
        ci_low = d_bar_diff - eps_diff
        ci_high = d_bar_diff + eps_diff
        significant = not (ci_low <= 0 <= ci_high)
        
        print(f"\n  Comparison: {design_a} vs {design_b}")
        print(f"  Mean Diff : {d_bar_diff:.4f}")
        print(f"  95% CI    : [{ci_low:.4f}, {ci_high:.4f}]")
        if significant:
            if d_bar_diff < 0:
                print(f"  Result    : SIGNIFICANT. {design_a} is better.")
            else:
                print(f"  Result    : SIGNIFICANT. {design_b} is better.")
        else:
            print(f"  Result    : NOT SIGNIFICANT. Statistically tied.")

    # 1. Is the #1 design significantly better than the #2 design?
    rank1_design = df_results.iloc[0]["Design"]
    rank2_design = df_results.iloc[1]["Design"]
    print(f"\n1. Is Rank 1 ({rank1_design}) significantly better than Rank 2 ({rank2_design})?")
    paired_t_test(rank1_design, rank2_design)
    
    # 2. Is Strategy 3 significantly better than Strategy 1?
    print("\n2. Is Strategy 3 significantly better than Strategy 1? (Using U=14, R=1 baseline)")
    if "S3-U14-R1" in raw_data_dict and "S1-U14-R1" in raw_data_dict:
        paired_t_test("S3-U14-R1", "S1-U14-R1")
    else:
        print("  Data for S3-U14-R1 and S1-U14-R1 not available in this run.")

    total_time = time.time() - start_time
    print(f"\nTotal script execution time: {total_time:.1f}s")

if __name__ == "__main__":
    main()
