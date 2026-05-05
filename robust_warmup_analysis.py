import sys
import os
import random
import numpy as np
import matplotlib.pyplot as plt

# Voeg de map met de simulatiecode toe aan het pad
sys.path.append(os.path.join(os.getcwd(), "smaproject2026", "python-code"))

from simulation import Simulation

def calculate_welch_moving_avg(data, window_size):
    T = len(data)
    moving_avgs = np.zeros(T)
    for t in range(T):
        if t < window_size:
            end_idx = 2 * t + 1
            moving_avgs[t] = np.mean(data[:min(end_idx, T)])
        else:
            start_idx = t - window_size
            end_idx = t + window_size + 1
            moving_avgs[t] = np.mean(data[start_idx:min(end_idx, T)])
    return moving_avgs

def run_robust_analysis(num_samples=10, R=100, W=200, window_size=15):
    # Alle mogelijke combinaties (10 tot en met 18 urgente slots)
    strategies = [1, 2, 3]
    num_urgents = list(range(10, 19))
    rules = [1, 2, 3, 4]
    
    all_combinations = []
    for s in strategies:
        for n in num_urgents:
            for r in rules:
                all_combinations.append((s, n, r))
    
    # Kies 10 willekeurige combinaties
    sampled_combinations = random.sample(all_combinations, num_samples)
    
    plt.figure(figsize=(14, 8))
    warmup_results = []
    
    print(f"Start Robust Warm-up Analyse op {num_samples} willekeurige scenario's...")
    
    for idx, (strat, num_u, rule) in enumerate(sampled_combinations):
        scenario_label = f"S{strat}-U{num_u}-R{rule}"
        print(f"  Scenario {idx+1}/{num_samples}: {scenario_label}")
        
        all_reps_data = np.zeros((R, W))
        # Dummy filename since we use setupScenario
        sim = Simulation("", W, R, rule)
        sim.setupScenario(strat, num_u, rule)
        
        for r in range(R):
            sim.resetSystem()
            random.seed(r)
            sim.runOneSimulation()
            all_reps_data[r] = sim.getWeeklyObjectiveValues()
        
        mean_per_week = np.mean(all_reps_data, axis=0)
        moving_avg = calculate_welch_moving_avg(mean_per_week, window_size)
        
        # Bereken cutoff (1% van steady state)
        steady_state_avg = np.mean(moving_avg[-50:])
        warmup_week = 0
        marge = 0.01 * steady_state_avg
        for w in range(W):
            if abs(moving_avg[w] - steady_state_avg) < marge:
                warmup_week = w
                break
        
        warmup_results.append(warmup_week)
        plt.plot(range(W), moving_avg, label=f"{scenario_label} (Cutoff: {warmup_week})")
        print(f"    -> Gedetecteerde warm-up: week {warmup_week}")

    fixed_warmup = 60
    plt.axvline(x=fixed_warmup, color='black', linestyle='--', linewidth=2, label="Determined cutoff value")
    
    plt.title(f"Robust Welch Vergelijking ({num_samples} scenario's)")
    plt.xlabel("Weken")
    plt.ylabel("Objective Function (Welch MA)")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("robust_welch_comparison.png")
    
    print("\n" + "="*40)
    print(f"ROBUUSTE ANALYSE VOLTOOID")
    print(f"Individuele cutoffs: {warmup_results}")
    print(f"GEKOZEN VEILIGE WARM-UP PERIODE: WEEK {fixed_warmup}")
    print("="*40)
    print("Vergelijkingsgrafiek opgeslagen als 'robust_welch_comparison.png'.")

if __name__ == "__main__":
    run_robust_analysis()
