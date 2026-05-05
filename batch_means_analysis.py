"""
Batch Means Method — gebaseerd op de slides van Simulation Modelling and Analysis.

Notatie (uit slides, pagina 35-37 Discrete Event Systems):
  L  = aantal batches
  M  = batch grootte (weken per batch)
  Dk = batchgemiddelde van batch k  =  (1/M) * som van observaties in batch k
  D̄  = overall gemiddelde           =  (1/L) * som van Dk
  S² = steekproefvariantie          =  (1/(L-1)) * som van (Dk - D̄)²
  Var[D̄] = S²/L
  ε  = Z_{α/2} * S / √L             (half-breedte 95% BI)

Bepaling van L (aantal batches):
  Stap 1: Kies n >= 30, genereer n batchgemiddelden
  Stap 2: Bereken X̄ en S²
  Stap 3: Als ε <= ε_target: stop.
          Anders: w3 = n_required = ⌈(Z*S/ε_target)²⌉, genereer extra batches

Warm-up  : 60 weken (Welch-analyse)
Batch M  : 5 * decorrelatie-lag via ACF (drempel |ACF| < 0.01)
L batches: w3 bepaald via sequentiële procedure → finale run met L = w3
"""

import sys
import os
import random
import math
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

sys.path.append(os.path.join(os.getcwd(), "smaproject2026", "python-code"))
from simulation import Simulation

# ── Globale parameters ────────────────────────────────────────────────────────
WARMUP       = 60      # weken warm-up (uit Welch-analyse)
N0           = 30      # minimum aantal batches voor sequentiële procedure
ALPHA        = 0.05    # significantieniveau (95% BI)
EPS_TARGET   = 0.015   # gewenste maximale half-breedte ε (user-defined)
ACF_THRESH   = 0.01    # drempelwaarde autocorrelatie voor batch grootte bepaling
W_LONG       = 800     # weken voor de lange ACF-run
SEED         = 42      # reproduceerbare resultaten
# ─────────────────────────────────────────────────────────────────────────────


def t_crit(df: int) -> float:
    """t_{α/2, df} voor tweezijdig 95% BI via t-verdeling (df = L-1)."""
    return stats.t.ppf(1 - ALPHA / 2, df)


def compute_acf(data: np.ndarray, max_lag: int) -> np.ndarray:
    """Berekent de autocorrelatiefunctie (ACF) tot en met max_lag."""
    n    = len(data)
    mean = np.mean(data)
    var  = np.sum((data - mean) ** 2)
    acf  = np.zeros(max_lag)
    for lag in range(1, max_lag + 1):
        cov = np.sum((data[:n - lag] - mean) * (data[lag:] - mean))
        acf[lag - 1] = cov / var
    return acf


def determine_batch_size(strategy: int = 1, num_urgent: int = 14, rule: int = 1):
    """
    Bepaalt M (batch grootte) via de eerste lag waarbij |ACF(lag)| < ACF_THRESH.
    Conservatieve keuze: M = 5 * decorrelatie-lag.
    """
    sim = Simulation("", W_LONG, 1, rule)
    sim.setupScenario(strategy, num_urgent, rule)
    random.seed(SEED)
    sim.runOneSimulation()

    data    = np.array(sim.getWeeklyObjectiveValues()[WARMUP:])
    max_lag = min(100, len(data) // 4)
    acf     = compute_acf(data, max_lag)

    decorr_lag = max_lag
    for lag_idx, rho in enumerate(acf):
        if abs(rho) < ACF_THRESH:
            decorr_lag = lag_idx + 1
            break

    M = max(5, decorr_lag * 5)
    print(f"  Decorrelatie-lag (|ACF| < {ACF_THRESH}): {decorr_lag} weken")
    print(f"  Gekozen batch grootte M = 5 × {decorr_lag} = {M} weken")
    return M, acf, max_lag, decorr_lag


def get_batch_means(data: np.ndarray, M: int) -> np.ndarray:
    """Verdeelt data in L niet-overlappende batches van grootte M en geeft Dk."""
    L = len(data) // M
    return np.array([np.mean(data[k * M:(k + 1) * M]) for k in range(L)])


def find_w3(strategy: int, num_urgent: int, rule: int,
            M: int, eps_target: float = EPS_TARGET) -> int:
    """
    Sequentiële procedure (Stap 1-3) om w3 = vereist aantal batches te bepalen.

    Stap 1: genereer n0 = 30 batchgemiddelden
    Stap 2: bereken X̄ en S²
    Stap 3: ε = Z*S/√n → als ε <= eps_target: stop, anders: w3 = ⌈(Z*S/eps_target)²⌉
    """
    print(f"\n  Sequentiële procedure om w3 te bepalen (n0 = {N0}):")

    # Stap 1
    W_run = WARMUP + N0 * M
    sim   = Simulation("", W_run, 1, rule)
    sim.setupScenario(strategy, num_urgent, rule)
    random.seed(SEED)
    sim.runOneSimulation()

    data = np.array(sim.getWeeklyObjectiveValues()[WARMUP:])
    Dk   = get_batch_means(data, M)
    n    = len(Dk)

    # Stap 2
    x_bar = np.mean(Dk)
    s2    = np.var(Dk, ddof=1)
    s     = math.sqrt(s2)

    # Stap 3 — Z-waarde (n=30 → centrale limietstelling geldt)
    Z          = stats.norm.ppf(1 - ALPHA / 2)
    eps        = Z * s / math.sqrt(n)
    w3         = math.ceil((Z * s / eps_target) ** 2)

    print(f"  Stap 2: X̄ = {x_bar:.6f},  S² = {s2:.8f},  S = {s:.6f}")
    print(f"  Stap 3: Z_{{α/2}} = {Z:.4f}  (n={n} ≥ 30 → Z-benadering geldig)")
    print(f"          ε = Z·S/√n = {Z:.4f}·{s:.4f}/√{n} = {eps:.6f}  "
          f"(target ε = {eps_target})")
    print(f"          w3 = ⌈(Z·S/ε_target)²⌉ = "
          f"⌈({Z:.4f}·{s:.4f}/{eps_target})²⌉ = {w3}")

    if eps <= eps_target:
        print(f"          ε ≤ ε_target → procedure stopt bij n0 = {n}")
        print(f"          w3 = {w3} → gebruik w3 = {w3} voor finale run")
    else:
        print(f"          ε > ε_target → {w3} batches vereist voor finale run")

    return w3, s, x_bar


def run_batch_means(strategy: int, num_urgent: int, rule: int,
                    L: int, M: int) -> dict:
    """
    Definitieve batch means simulatie met L batches van M weken (slides notatie).

    Volgt exact het voorbeeld uit de slides (pagina 35-37):
      Dk     = (1/M) * Σ observaties in batch k
      D̄      = (1/L) * Σ Dk
      S²     = (1/(L-1)) * Σ(Dk - D̄)²
      Var[D̄] = S²/L
      ε      = Z_{α/2} * S/√L   met S = √S²
      95% BI = [D̄ - ε, D̄ + ε]
    """
    scenario  = f"S{strategy}-U{num_urgent}-R{rule}"
    W_total   = WARMUP + L * M

    print(f"\n  Scenario : {scenario}")
    print(f"  L = {L} batches,  M = {M} weken/batch")
    print(f"  Warm-up  = {WARMUP} weken")
    print(f"  Totale simulatielengte: {WARMUP} + {L}×{M} = {W_total} weken")

    sim = Simulation("", W_total, 1, rule)
    sim.setupScenario(strategy, num_urgent, rule)
    random.seed(SEED)
    sim.runOneSimulation()

    data = np.array(sim.getWeeklyObjectiveValues()[WARMUP:])
    Dk   = get_batch_means(data, M)
    L    = len(Dk)          # werkelijk aantal volledige batches

    # Slides-formules — t-verdeling met df = L-1
    df       = L - 1
    t        = t_crit(df)
    d_bar    = np.mean(Dk)                         # D̄
    s2       = np.var(Dk, ddof=1)                  # S²  = (1/(L-1)) * Σ(Dk-D̄)²
    s        = math.sqrt(s2)                       # S
    var_dbar = s2 / L                              # Var[D̄] = S²/L
    eps      = t * math.sqrt(var_dbar)             # ε = t_{α/2,L-1} * S/√L
    ci_low   = d_bar - eps
    ci_high  = d_bar + eps

    print(f"\n  Batchgemiddelden Dk (k=1..{L}) berekend.")
    print(f"  D̄      = (1/L) × ΣDk                           = {d_bar:.6f}")
    print(f"  S²     = (1/(L-1)) × Σ(Dk-D̄)²                  = {s2:.8f}")
    print(f"  S      = √S²                                    = {s:.6f}")
    print(f"  Var[D̄] = S²/L = {s2:.6f}/{L}                     = {var_dbar:.8f}")
    print(f"  t_{{α/2,{df}}} = {t:.4f}  (df = L-1 = {df}, L={L} < 30 → t-verdeling)")
    print(f"  ε      = t × S/√L = {t:.4f}×{s:.4f}/√{L}          = {eps:.6f}")
    print(f"  95% BI = [D̄-ε, D̄+ε] = [{ci_low:.6f}, {ci_high:.6f}]")

    return {
        "scenario":  scenario,
        "L":         L,
        "M":         M,
        "Dk":        Dk,
        "d_bar":     d_bar,
        "s2":        s2,
        "s":         s,
        "var_dbar":  var_dbar,
        "eps":       eps,
        "ci_low":    ci_low,
        "ci_high":   ci_high,
    }


def plot_acf(acf: np.ndarray, max_lag: int, M: int,
             decorr_lag: int, filename: str = "acf_plot.png") -> None:
    lags = np.arange(1, max_lag + 1)
    plt.figure(figsize=(12, 5))
    plt.stem(lags, acf, markerfmt="C0o", linefmt="C0-", basefmt="k-")
    plt.axhline(y= ACF_THRESH, color="red", linestyle="--",
                label=f"Drempel ±{ACF_THRESH}")
    plt.axhline(y=-ACF_THRESH, color="red", linestyle="--")
    plt.axvline(x=decorr_lag, color="green", linestyle=":",
                label=f"Decorrelatie-lag = {decorr_lag}  →  M = {M} weken")
    plt.title("Autocorrelatiefunctie (ACF) — objectieffunctie per week")
    plt.xlabel("Lag (weken)")
    plt.ylabel("Autocorrelatie ρ")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    print(f"  ACF-grafiek opgeslagen als '{filename}'.")


def plot_batch_means(result: dict, filename: str = "batch_means_plot.png") -> None:
    Dk       = result["Dk"]
    d_bar    = result["d_bar"]
    eps      = result["eps"]
    L        = result["L"]
    scenario = result["scenario"]

    plt.figure(figsize=(14, 5))
    plt.plot(range(1, L + 1), Dk, "o-", markersize=4, label="Batchgemiddelden $D_k$")
    plt.axhline(y=d_bar,       color="red",    linestyle="-",
                label=f"$\\bar{{D}}$ = {d_bar:.4f}")
    plt.axhline(y=d_bar + eps, color="orange", linestyle="--",
                label=f"95% BI: [{d_bar-eps:.4f}, {d_bar+eps:.4f}]")
    plt.axhline(y=d_bar - eps, color="orange", linestyle="--")
    plt.title(f"Batchgemiddelden $D_k$ — {scenario}  (L={L}, M={result['M']})")
    plt.xlabel("Batch k")
    plt.ylabel("Objectieffunctie $D_k$")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    print(f"  Batchgemiddelden-grafiek opgeslagen als '{filename}'.")


def main():
    print("=" * 65)
    print("BATCH MEANS METHODE  (slides notatie: L batches van M weken)")
    print(f"  Warm-up         : {WARMUP} weken")
    print(f"  ACF-drempel     : |ρ| < {ACF_THRESH}")
    print(f"  ε_target        : {EPS_TARGET}")
    print(f"  t_{{α/2,df}}      : scipy.stats.t.ppf(0.975, df)  (95% BI, df=L-1)")
    print("=" * 65)

    # ── 1. Bepaal M via ACF (worst-case scenario) ────────────────────────────
    print("\nStap A — Batch grootte M via ACF (worst-case S1-U14-R1):")
    M, acf, max_lag, decorr_lag = determine_batch_size(strategy=1, num_urgent=14, rule=1)
    plot_acf(acf, max_lag, M, decorr_lag, filename="acf_batch_size.png")

    # ── 2. Sequentiële procedure → bepaal w3 ─────────────────────────────────
    print("\nStap B — Sequentiële procedure (n0=30) → w3 bepalen:")
    w3, s_pilot, xbar_pilot = find_w3(
        strategy=1, num_urgent=14, rule=1, M=M, eps_target=EPS_TARGET
    )
    print(f"\n  → Finale run uitvoeren met L = w3 = {w3} batches, M = {M} weken")
    print(f"    Totale simulatielengte: {WARMUP} + {w3}×{M} = {WARMUP + w3*M} weken")

    # ── 3. Definitieve batch means run met L = w3 ─────────────────────────────
    print("\nStap C — Definitieve batch means simulatie (slides formules):")
    result = run_batch_means(
        strategy=1, num_urgent=14, rule=1, L=w3, M=M
    )
    plot_batch_means(result, filename="batch_means_plot.png")

    # ── Samenvatting ──────────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("SAMENVATTING")
    print("=" * 65)
    print(f"  Scenario          : {result['scenario']}")
    print(f"  Warm-up periode   : {WARMUP} weken")
    print(f"  Batch grootte  M  : {result['M']} weken  (5 × decorrelatie-lag {decorr_lag})")
    print(f"  Aantal batches L  : {result['L']}  (w3 uit sequentiële procedure)")
    print(f"  Totale run        : {WARMUP + result['L']*result['M']} weken")
    print(f"  D̄  (gemiddelde)   : {result['d_bar']:.6f}")
    print(f"  S² (variantie)    : {result['s2']:.8f}")
    print(f"  S  (std. dev.)    : {result['s']:.6f}")
    print(f"  Var[D̄] = S²/L    : {result['var_dbar']:.8f}")
    t_final = t_crit(result['L'] - 1)
    print(f"  t_{{α/2,{result['L']-1}}}          : {t_final:.4f}  (df = L-1 = {result['L']-1})")
    print(f"  ε  = t·S/√L       : {result['eps']:.6f}  (target: {EPS_TARGET})")
    print(f"  95% BI            : [{result['ci_low']:.6f}, {result['ci_high']:.6f}]")
    print("=" * 65)


if __name__ == "__main__":
    main()
