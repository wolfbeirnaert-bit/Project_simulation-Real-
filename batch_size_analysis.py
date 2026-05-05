import sys
import os
import random
import numpy as np
import matplotlib.pyplot as plt

# Voeg de map met de simulatiecode toe aan het pad
sys.path.append(os.path.join(os.getcwd(), "smaproject2026", "python-code"))

from simulation import Simulation

def autocorrelatie(x, lag):
    n = len(x)
    mean = np.mean(x)
    numerator = np.sum((x[:n-lag] - mean) * (x[lag:] - mean))
    denominator = np.sum((x - mean)**2)
    return numerator / denominator

def run_batch_analysis(W=300, warmup=60):
    print(f"Start Batch Size Analyse (Autocorrelatie)...")
    input_file = "smaproject2026/input-S1-14.txt"
    
    # We draaien één lange simulatie om de afhankelijkheid tussen weken te zien
    sim = Simulation(input_file, W, 1, 1) 
    sim.setupScenario(1, 14, 1) # Standaard scenario S1, 14 urgent slots, Rule 1
    
    random.seed(42)
    sim.runOneSimulation()
    
    # Haal de wekelijkse objectieve waarden op en gooi de warmup weg
    data = np.array(sim.getWeeklyObjectiveValues()[warmup:])
    
    lags = range(1, 51)
    threshold = 0.01
    correlations = [autocorrelatie(data, l) for l in lags]
    
    # Zoek de eerste L waar correlatie < 0.01
    determined_L = 1
    for i, corr in enumerate(correlations):
        if abs(corr) < threshold:
            determined_L = lags[i]
            break
            
    # Plot ACF
    plt.figure(figsize=(12, 6))
    plt.stem(lags, correlations)
    plt.axhline(y=threshold, color='red', linestyle='--', label=f'{threshold} Drempelwaarde')
    plt.axhline(y=-threshold, color='red', linestyle='--')
    plt.axvline(x=determined_L, color='green', linestyle=':', label=f'Geadviseerde L = {determined_L}')
    
    plt.title("Autocorrelatiefunctie (ACF) per Week")
    plt.xlabel("Lag (L) in weken")
    plt.ylabel("Autocorrelatie")
    plt.legend()
    plt.grid(True)
    plt.savefig("batch_autocorrelation.png")
    
    print("\n" + "="*40)
    print(f"BATCH SIZE ANALYSE VOLTOOID")
    print(f"Eerste lag L waarbij correlatie < 0.05: {determined_L} weken")
    print(f"Advies voor Batch Size: Gebruik batches van minstens {determined_L} weken.")
    print("="*40)
    print("ACF-grafiek opgeslagen als 'batch_autocorrelation.png'.")

if __name__ == "__main__":
    run_batch_analysis()
