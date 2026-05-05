---
output:
  pdf_document: default
  html_document: default
---
# Reorganisation of an Outpatient Radiology Department
## Simulation Modelling and Analysis (2025-2026)

---

## 1. Introduction

### 1.1. System Description
In this project, we analyze and improve the performance of an outpatient radiology department using discrete-event simulation. The department currently uses a cyclic appointment schedule with 146 elective slots and a variable number of urgent slots. Elective patients arrive according to appointments (with potential unpunctuality and no-shows), while urgent patients arrive unannounced throughout the day. The goal of this study is to minimize the weighted waiting times for both urgent and elective patients by redesigning the capacity distribution (urgent vs. elective slots) and the timing of urgent slots.

### 1.2. Overview of Research Test Design
The study evaluates the system by varying three main factors:
1. **Urgent Slot Capacity:** Ranging between 10 and 17 slots. Configurations with 18 or more urgent slots were excluded from the experimental design following our preliminary analysis, which revealed that these configurations push the system beyond its capacity limits, leading to fundamentally unstable behaviour (see Section 3).
2. **Timing Strategy:** Three strategies for distributing urgent slots over the day/week.
3. **Appointment Rules:** Four different single-pass appointment scheduling rules (Plain FCFS, Bailey-Welch, Blocking, Benchmarking).

Our analysis proceeds through several statistical phases: establishing steady-state behaviour (warm-up), determining batch means parameters for independent sampling, establishing a variance baseline, applying variance reduction (Antithetic Variables), executing a full-factorial screening design across all 96 valid configurations, and finally a comparative analysis to identify the best system configuration.

---

## 2. Statistical Analysis & Warm-up

### 2.1. Welch's Method and Warm-up Period
Before applying the batch means method, it is essential to determine and remove the initial warm-up period to eliminate transient initialization bias in the simulation output. To do this, we applied Welch's method across 10 distinct and representative experimental designs. These designs were chosen at random to ensure a diverse mix of urgent slots, scheduling rules, and timing strategies.

By plotting the moving average of the objective function for these designs, we visually inspected the point at which the output stabilized. When determining the universal warm-up length, we analyzed the worst-case scenario among these representative designs. Notably, configurations operating at near-full capacity (such as those with 18 urgent slots) were excluded from this specific baseline determination, as their extreme instability (which is further analyzed in later sections) skews the steady-state convergence.

Based on the remaining worst-case convergence, we observed a cutoff value of roughly 63 weeks. To maintain consistency and robustness across the majority of our experiments, we conservatively selected a universal warm-up period of **60 weeks**. This period is sufficient to remove initialization bias for approximately 90% of our tested scenarios, ensuring that only steady-state behaviour is considered in our final performance evaluations.

### 2.2. Batch Means Method
To conduct a statistically valid analysis of our steady-state simulation results, we applied the Batch Means Method. Because consecutive outputs in discrete-event simulations are autocorrelated, the batch means method groups observations into batches to form approximately independent data points.

Based on our worst-case scenario analysis, we determined that a batch size of $M = 80$ weeks ensures that the lag-based correlation falls below the 0.01 threshold. We sequentially determined that $L = 22$ batches are required to achieve the target precision. This yields a total simulation run length of:

$$W_{total} = W_{warmup} + L \times M = 60 + 22 \times 80 = 1820 \text{ weeks}$$

To establish a baseline of the natural system variance across different configurations, we simulated 11 representative experimental designs. The table below summarizes the 95% confidence intervals, standard deviations, coefficient of variation (CV), and relative precision ($\gamma$) for these designs using $M=80$ and $L=22$.

| Design | Avg_Obj ($\bar{D}$) | Var ($S^2$) | StdDev ($S$) | Half-Width ($\epsilon$) | 95% CI | CV | Rel Precision ($\gamma$) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **S1-U14-R1** | 0.4762 | 0.0015 | 0.0386 | 0.0171 | [0.4591 ; 0.4933] | 0.0811 | 0.0360 |
| **S1-U18-R4** | 0.8340 | 0.0827 | 0.2876 | 0.1275 | [0.7065 ; 0.9615] | 0.3448 | 0.1529 |
| **S3-U17-R2** | 0.5465 | 0.0117 | 0.1082 | 0.0480 | [0.4985 ; 0.5944] | 0.1981 | 0.0878 |
| **S1-U11-R3** | 0.4542 | 0.0003 | 0.0182 | 0.0081 | [0.4461 ; 0.4622] | 0.0401 | 0.0178 |
| **S2-U17-R2** | 0.6162 | 0.0119 | 0.1091 | 0.0484 | [0.5678 ; 0.6646] | 0.1771 | 0.0785 |
| **S3-U14-R3** | 0.4468 | 0.0016 | 0.0398 | 0.0177 | [0.4291 ; 0.4645] | 0.0892 | 0.0395 |
| **S3-U17-R3** | 0.5493 | 0.0118 | 0.1084 | 0.0481 | [0.5013 ; 0.5974] | 0.1974 | 0.0875 |
| **S3-U13-R3** | 0.4320 | 0.0009 | 0.0307 | 0.0136 | [0.4184 ; 0.4457] | 0.0711 | 0.0315 |
| **S1-U14-R4** | 0.4748 | 0.0015 | 0.0385 | 0.0171 | [0.4577 ; 0.4919] | 0.0812 | 0.0360 |
| **S2-U16-R1** | 0.5657 | 0.0050 | 0.0704 | 0.0312 | [0.5345 ; 0.5969] | 0.1244 | 0.0552 |
| **S2-U13-R4** | 0.5219 | 0.0009 | 0.0297 | 0.0132 | [0.5087 ; 0.5351] | 0.0570 | 0.0253 |

The results indicate that while some configurations (e.g., S1-U11-R3) are highly stable with a relative precision of ~1.78%, others (e.g., S1-U18-R4) exhibit substantial natural variance with a relative precision exceeding 15%. This variance highlights the necessity of employing variance reduction techniques to ensure robust statistical comparisons between the designs.

---

## 3. Variance Reduction
To obtain more accurate simulation estimates without increasing the computational burden, we implemented Variance Reduction using Antithetic Variables. For every standard simulation batch generated using random number sequence $U$, we generated an antithetic counterpart using $1-U$. These paired simulation outputs are negatively correlated. By averaging the outputs of the standard and antithetic runs ($Y_k = (X_k + X'_k)/2$), the overall variance is substantially reduced.

### Impact on Stable Systems
For configurations that do not push the system to its capacity limits (e.g., 11 to 14 urgent slots), the antithetic pairing successfully reduced the variance by more than half without extending the simulation runtime. For example, in design **S1-U11-R3**, the variance dropped from 0.0003 to 0.0001, and the relative precision ($\gamma$) improved from 1.78% to 0.82%. Similarly, for **S1-U14-R1**, the variance dropped from 0.0015 to 0.0006 ($\gamma$ improved from 3.6% to 2.18%). This mathematically confirms the efficacy of the antithetic variates approach for stabilizing estimates in normal operating conditions.

### The Phenomenon of Heavily Loaded Systems
Conversely, the variance reduction technique exposed a critical vulnerability in heavily-loaded configurations (systems approaching 100% utilization, such as 17 or 18 urgent slots). For **S1-U18-R4**, the baseline mean was 0.8340. However, when the antithetic counterpart ($1 - U$) was run, the combined mean skyrocketed to 2.3745, and the variance heavily increased rather than decreasing.

This happens because queue waiting times are convex relative to system utilization. When the antithetic sequence generates shorter inter-arrival times and longer service times, an already saturated queue completely breaks down, sending waiting times toward infinity. This finding is a powerful empirical proof that any design allocating 17 or 18 urgent slots is fundamentally unstable and highly susceptible to operational variability. Consequently, configurations with 18 or more urgent slots were excluded from the full experimental design.

### 3.1. Confidence Interval Estimation
Since we are estimating the population mean based on a relatively small sample size ($n = L = 22$ batches), we used the $t$-distribution rather than the normal distribution. This adjustment accounts for the additional uncertainty in estimating the population standard deviation from a small sample. The general formula for the confidence interval of the mean is given by:

$$CI = \left[ \bar{Y} - t_{\alpha/2, n-1} \cdot \frac{S_Y}{\sqrt{n}} \ ; \ \bar{Y} + t_{\alpha/2, n-1} \cdot \frac{S_Y}{\sqrt{n}} \right]$$

For the baseline design (**S1-U14-R1**) after applying antithetic variables, the 95% CI is $[0.4779 ; 0.4991]$, with $\bar{Y} = 0.4885$, $S_Y = 0.0240$, and $t_{0.025, 21} \approx 2.0796$. This narrow interval reflects the low variability across batch means after variance reduction, indicating a high degree of precision for stable configurations.

---

## 4. Experimental Design (Screening)

### 4.1. Full-Factorial Screening Design
Following the preliminary analysis, we conducted a full-factorial screening design over all valid configurations. The experimental space covers:

- **3 timing strategies** (Strategy 1: end-of-block, Strategy 2: evenly distributed, Strategy 3: after every 6 elective slots)
- **8 urgent slot counts**: 10, 11, 12, 13, 14, 15, 16, 17 (18–20 excluded due to instability)
- **4 appointment scheduling rules** (Rule 1: FCFS, Rule 2: Bailey-Welch, Rule 3: Blocking B=2, Rule 4: Benchmarking $k_\sigma = 0.5$)

This yields **96 designs** in total ($3 \times 8 \times 4$). Each design was evaluated using the Batch Means Method with antithetic variates ($W_{warmup} = 60$, $M = 80$, $L = 22$, seed = 42). The objective function used is:

$$\text{Minimize} \quad w_e \cdot \overline{Wt_e} + w_u \cdot \overline{Wt_u}$$

with $w_e = 1/168$ (elective appointment waiting time, normalized by 1 week) and $w_u = 1/9$ (urgent scan waiting time, normalized by 9 hours). Note that elective scan waiting time and overtime are secondary objectives used only for tiebreaking.

### 4.2. Screening Results

The table below presents the top 20 designs ranked by average objective value $\bar{Y}$:

| Rank | Design | Strategy | Urgent Slots | Rule | Avg OV | Half-Width | 95% CI |
|:----:|:-------|:--------:|:------------:|:----:|:------:|:----------:|:------:|
| 1 | S3-U11-R4 | 3 | 11 | 4 | 0.4311 | 0.0040 | [0.4271 ; 0.4352] |
| 2 | S3-U11-R2 | 3 | 11 | 2 | 0.4321 | 0.0040 | [0.4280 ; 0.4361] |
| 3 | S3-U11-R1 | 3 | 11 | 1 | 0.4325 | 0.0040 | [0.4284 ; 0.4365] |
| 4 | S3-U11-R3 | 3 | 11 | 3 | 0.4344 | 0.0041 | [0.4304 ; 0.4385] |
| 5 | S3-U13-R4 | 3 | 13 | 4 | 0.4357 | 0.0069 | [0.4288 ; 0.4425] |
| 6 | S3-U13-R2 | 3 | 13 | 2 | 0.4366 | 0.0068 | [0.4297 ; 0.4434] |
| 7 | S3-U13-R1 | 3 | 13 | 1 | 0.4371 | 0.0068 | [0.4302 ; 0.4439] |
| 8 | S3-U12-R4 | 3 | 12 | 4 | 0.4378 | 0.0050 | [0.4328 ; 0.4428] |
| 9 | S3-U12-R2 | 3 | 12 | 2 | 0.4389 | 0.0050 | [0.4339 ; 0.4440] |
| 10 | S3-U13-R3 | 3 | 13 | 3 | 0.4390 | 0.0069 | [0.4321 ; 0.4459] |
| 11 | S3-U12-R1 | 3 | 12 | 1 | 0.4392 | 0.0050 | [0.4342 ; 0.4441] |
| 12 | S3-U12-R3 | 3 | 12 | 3 | 0.4413 | 0.0051 | [0.4362 ; 0.4464] |
| 13 | S3-U10-R4 | 3 | 10 | 4 | 0.4427 | 0.0035 | [0.4392 ; 0.4462] |
| 14 | S3-U10-R2 | 3 | 10 | 2 | 0.4438 | 0.0035 | [0.4402 ; 0.4473] |
| 15 | S3-U10-R1 | 3 | 10 | 1 | 0.4440 | 0.0035 | [0.4405 ; 0.4476] |
| 16 | S3-U10-R3 | 3 | 10 | 3 | 0.4461 | 0.0036 | [0.4425 ; 0.4496] |
| 17 | S1-U11-R2 | 1 | 11 | 2 | 0.4529 | 0.0037 | [0.4491 ; 0.4566] |
| 18 | S1-U11-R4 | 1 | 11 | 4 | 0.4532 | 0.0037 | [0.4495 ; 0.4570] |
| 19 | S1-U11-R1 | 1 | 11 | 1 | 0.4547 | 0.0037 | [0.4510 ; 0.4585] |
| 20 | S3-U14-R4 | 3 | 14 | 4 | 0.4559 | 0.0106 | [0.4453 ; 0.4665] |

The complete results for all 96 designs are available in `full_sweep_antithetic.csv`.

### 4.3. Key Observations

**Observation 1 — Strategy 3 dominates.**
The entire top 16 positions are occupied by Strategy 3 designs. The first non-Strategy-3 design appears only at rank 17 (S1-U11-R2, OV = 0.4529). Strategy 3, which places urgent slots after every 6 consecutive elective slots, consistently outperforms the alternatives. Strategy 2 (evenly distributed) is clearly the worst, with its best design (S2-U13-R4, OV = 0.5298) ranking only 49th overall.

| Strategy | Best Design | Best OV | Worst OV |
|:--------:|:-----------:|:-------:|:--------:|
| 1 | S1-U11-R2 | 0.4529 | 0.7883 |
| 2 | S2-U13-R4 | 0.5298 | 0.8113 |
| 3 | S3-U11-R4 | 0.4311 | 0.7418 |

**Observation 2 — 11 urgent slots is the optimal capacity allocation.**
Within Strategy 3, the best objective values are consistently achieved with 11 urgent slots. The OV increases as urgent slots deviate from this optimum in both directions: too few urgent slots leads to longer urgent scan waiting times (insufficient capacity), while too many urgent slots crowds out elective slots and increases appointment waiting times. Crucially, configurations with 15 or more urgent slots show rapidly increasing variance, confirming the approach towards instability.

| Urgent Slots | Best OV (Strategy 3) | Variance |
|:------------:|:--------------------:|:--------:|
| 10 | 0.4427 | very low |
| 11 | 0.4311 | very low |
| 12 | 0.4378 | low |
| 13 | 0.4357 | low |
| 14 | 0.4559 | medium |
| 15 | 0.4782 | medium-high |
| 16 | 0.5507 | high |
| 17 | 0.7383 | very high |

**Observation 3 — Appointment rules have minimal impact.**
Within any given strategy and urgent slot count, the four appointment scheduling rules produce very similar objective values. For the best configuration (S3-U11), the OV ranges only from 0.4311 (Rule 4) to 0.4344 (Rule 3) — a spread of just 0.0033. The best rule per slot count is consistently Rule 4 (Benchmarking) or Rule 2 (Bailey-Welch), but the differences are negligibly small.

| Rule | Best Design | Best OV |
|:----:|:-----------:|:-------:|
| 1 (FCFS) | S3-U11-R1 | 0.4325 |
| 2 (Bailey-Welch) | S3-U11-R2 | 0.4321 |
| 3 (Blocking) | S3-U11-R3 | 0.4344 |
| 4 (Benchmarking) | S3-U11-R4 | 0.4311 |

---

## 5. Comparative Analysis

### 5.1. Statistical Comparison of Top Designs
To determine whether differences between the top-performing designs are statistically significant, we examine whether their 95% confidence intervals overlap. Two designs can be considered significantly different if their confidence intervals do not overlap.

Comparing the top 4 designs (all S3-U11):

| Design | 95% CI |
|:-------|:------:|
| S3-U11-R4 | [0.4271 ; 0.4352] |
| S3-U11-R2 | [0.4280 ; 0.4361] |
| S3-U11-R1 | [0.4284 ; 0.4365] |
| S3-U11-R3 | [0.4304 ; 0.4385] |

All four confidence intervals overlap substantially. We therefore cannot statistically distinguish between these four designs based on the current sample size. All S3-U11 configurations perform equivalently well, and the choice of appointment rule within this configuration is not statistically meaningful.

### 5.2. Comparison Between Strategies
The gap between Strategy 3 and the alternatives is statistically significant. Comparing the best S3 design (S3-U11-R4, CI: [0.4271; 0.4352]) against the best S1 design (S1-U11-R2, CI: [0.4491; 0.4566]): the upper bound of S3 (0.4352) is below the lower bound of S1 (0.4491), confirming that Strategy 3 is statistically superior to Strategy 1 for the same urgent slot count.

The superiority of Strategy 2 over Strategy 3 can be definitively rejected: the best S2 design (S2-U13-R4, CI: [0.5225; 0.5371]) lies entirely above the worst S3-U11 design (CI upper bound: 0.4385).

### 5.3. Recommended Configuration
Based on the full screening and comparative analysis, the recommended configuration is:

> **Strategy 3 with 11 urgent slots (any appointment rule)**

The choice of appointment rule within this configuration does not significantly affect performance. If a single rule must be selected, **Rule 4 (Benchmarking)** achieves the lowest point estimate (OV = 0.4311), followed closely by Rule 2 (Bailey-Welch, OV = 0.4321).

This recommendation represents a change from the current schedule (Strategy 1, 14 urgent slots, Rule 1), which scores OV = 0.4880 — approximately **11% worse** than the best design.

### 5.4. Secondary Objectives
The assignment specifies that elective scan waiting time and overtime serve as secondary objectives for tiebreaking. Since the top-performing designs (S3-U11, all rules) are statistically indistinguishable on the primary objective, a formal tiebreak using secondary objectives could be applied. This analysis is left as a next step.

---

## 6. Conclusion

This study evaluated 96 appointment schedule configurations for an outpatient radiology department across three timing strategies, eight urgent slot counts (10–17), and four appointment rules, using a statistically rigorous simulation framework.

The main conclusions are:

1. **Strategy 3 is clearly the best timing strategy.** Placing an urgent slot after every 6 consecutive elective slots produces consistently lower waiting times compared to end-of-block placement (Strategy 1) or even distribution (Strategy 2). This approach provides a better balance between elective and urgent patient flows throughout the day.

2. **11 urgent slots is the optimal capacity.** This number minimizes the weighted sum of elective appointment waiting time and urgent scan waiting time. Fewer slots increase urgent patient delays; more slots create appointment backlog for elective patients. Configurations with 16 or more urgent slots show high instability.

3. **Appointment rules have negligible impact on the primary objective.** All four rules perform nearly identically within the optimal S3-U11 configuration. The Benchmarking rule (Rule 4) has a marginally lower point estimate.

4. **The recommended configuration is S3-U11-R4** (or any rule), with an estimated objective value of **0.4311**, representing an 11% improvement over the current schedule (S1-U14-R1, OV ≈ 0.488).

**Next steps** to complete the analysis include: formal tiebreaking on secondary objectives (elective scan waiting time and overtime) for the top designs, and optionally a Ranking & Selection procedure (e.g., Dudewicz-Dalal) to formally confirm the best design with a probability-of-correct-selection guarantee.
