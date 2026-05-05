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
1. **Urgent Slot Capacity:** Ranging between 10 and 20 slots.
2. **Timing Strategy:** Three strategies for distributing urgent slots over the day/week.
3. **Appointment Rules:** Four different single-pass appointment scheduling rules (Plain FCFS, Bailey-Welch, Blocking, Benchmarking).

Our analysis proceeds through several statistical phases: establishing steady-state behavior (warm-up), determining batch means parameters for independent sampling, establishing a variance baseline, applying variance reduction (Antithetic Variables), executing a screening experimental design, and finally using a ranking and selection procedure to statistically verify the best system configuration.

---

## 2. Statistical Analysis & Warm-up

### 2.1. Welch’s Method and Warm-up Period
Before applying the batch means method, it is essential to determine and remove the initial warm-up period to eliminate transient initialization bias in the simulation output. To do this, we applied Welch's method across 10 distinct and representative experimental designs. These designs were chosen at random to ensure a diverse mix of urgent slots, scheduling rules, and timing strategies.

By plotting the moving average of the objective function for these designs, we visually inspected the point at which the output stabilized. When determining the universal warm-up length, we analyzed the worst-case scenario among these representative designs. Notably, configurations operating at near-full capacity (such as those with 18 urgent slots) were excluded from this specific baseline determination, as their extreme instability (which is further analyzed in later sections) skews the steady-state convergence. 

Based on the remaining worst-case convergence, we observed a cutoff value of roughly 63 weeks. To maintain consistency and robustness across the majority of our experiments, we conservatively selected a universal warm-up period of **60 weeks**. This period is sufficient to remove initialization bias for approximately 90% of our tested scenarios, ensuring that only steady-state behavior is considered in our final performance evaluations.

### 2.2. Batch Means Method
To conduct a statistically valid analysis of our steady-state simulation results, we applied the Batch Means Method. Because consecutive outputs in discrete-event simulations are autocorrelated, the batch means method groups observations into batches to form approximately independent data points.

Based on our worst-case scenario analysis, we determined that a batch size of $M = 80$ weeks ensures that the lag-based correlation falls below the 0.01 threshold. We sequentially determined that $L = 22$ batches are required to achieve the target precision. 

To establish a baseline of the natural system variance across different configurations, we simulated 11 representative experimental designs. The table below summarizes the 95% confidence intervals, standard deviations, coefficient of variation (CV), and relative precision ($\gamma$) for these designs using $M=80$ and $L=22$.

| Design | Avg_Obj ($\bar{D}$) | Var ($S^2$) | StdDev ($S$) | Half-Width ($\epsilon$) | 95% CI | Coeff of Var (CV) | Rel Precision ($\gamma$) |
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

The table below illustrates the Batch Means Method results after applying the Antithetic Variables method across the same 11 representative designs.

| Design    |   Avg_Obj (Y_bar) |   Var (S^2_Y) |   StdDev (S_Y) |   Half-Width (eps) | 95% CI            |   Coeff of Var (CV) |   Rel Precision ($\gamma$) |
|:----------|------------------:|--------------:|---------------:|-------------------:|:------------------|--------------------:|------------------------:|
| **S1-U14-R1** |            0.4885 |        0.0006 |         0.0240 |             0.0106 | [0,4779 ; 0,4991] |              0.0491 |                  0.0218 |
| **S1-U18-R4** |            2.3745 |        0.8888 |         0.9428 |             0.4180 | [1,9565 ; 2,7925] |              0.3970 |                  0.1760 |
| **S3-U17-R2** |            0.7404 |        0.0509 |         0.2256 |             0.1000 | [0,6403 ; 0,8404] |              0.3047 |                  0.1351 |
| **S1-U11-R3** |            0.4576 |        0.0001 |         0.0085 |             0.0038 | [0,4538 ; 0,4613] |              0.0186 |                  0.0082 |
| **S2-U17-R2** |            0.8094 |        0.0515 |         0.2268 |             0.1006 | [0,7089 ; 0,9100] |              0.2803 |                  0.1243 |
| **S3-U14-R3** |            0.4603 |        0.0006 |         0.0240 |             0.0106 | [0,4497 ; 0,4710] |              0.0522 |                  0.0231 |
| **S3-U17-R3** |            0.7429 |        0.0510 |         0.2259 |             0.1001 | [0,6428 ; 0,8430] |              0.3040 |                  0.1348 |
| **S3-U13-R3** |            0.4401 |        0.0002 |         0.0155 |             0.0069 | [0,4332 ; 0,4469] |              0.0352 |                  0.0156 |
| **S1-U14-R4** |            0.4870 |        0.0006 |         0.0241 |             0.0107 | [0,4764 ; 0,4977] |              0.0494 |                  0.0219 |
| **S2-U16-R1** |            0.6278 |        0.0075 |         0.0867 |             0.0384 | [0,5893 ; 0,6662] |              0.1381 |                  0.0612 |
| **S2-U13-R4** |            0.5303 |        0.0003 |         0.0164 |             0.0073 | [0,5230 ; 0,5376] |              0.0310 |                  0.0137 |

### Impact on Stable Systems
For configurations that do not push the system to its capacity limits (e.g., 11 to 14 urgent slots), the antithetic pairing successfully slashed the variance by more than half without extending the simulation runtime. For example, in design **S1-U11-R3**, the variance dropped from 0.0003 to 0.0001, and the relative precision ($\gamma$) improved from 1.78% to 0.82%. Similarly, for **S1-U14-R1**, the variance dropped from 0.0015 to 0.0006 ($\gamma$ improved from 3.6% to 2.18%). This mathematically confirms the efficacy of the antithetic variates approach for stabilizing estimates in normal operating conditions.

### The Phenomenon of Heavily Loaded Systems
Conversely, the variance reduction technique exposed a critical vulnerability in heavily-loaded configurations (systems approaching 100% utilization, such as 17 or 18 urgent slots). For **S1-U18-R4**, the baseline mean was 0.8340. However, when the antithetic counterpart ($1 - U$) was run, the combined mean skyrocketed to 2.3745, and the variance heavily increased rather than decreasing. 

This happens because queue waiting times are convex relative to system utilization. When the antithetic sequence generates shorter inter-arrival times and longer service times, an already saturated queue completely breaks down, sending waiting times toward infinity. This finding is a powerful empirical proof that any design allocating 17 or 18 urgent slots is fundamentally unstable and highly susceptible to operational variability. Consequently, these heavily loaded capacities should be avoided in the final system redesign.

### 3.1. Confidence Interval Estimation
Since we are estimating the population mean based on a relatively small sample size ($n = L = 22$ batches), we used the $t$-distribution rather than the normal distribution. This adjustment accounts for the additional uncertainty in estimating the population standard deviation from a small sample. The general formula for the confidence interval of the mean is given by:

$$ CI = \left[ \bar{Y} - t_{\alpha/2, n-1} \cdot \frac{S_Y}{\sqrt{n}} \ ; \ \bar{Y} + t_{\alpha/2, n-1} \cdot \frac{S_Y}{\sqrt{n}} \right] $$

For example, using the baseline design (**S1-U14-R1**) after applying antithetic variables, we derived the following summary statistics (based on $n = 22$ batches):
- Mean objective function value: $\bar{Y} = 0.4885$
- Sample standard deviation: $S_Y = 0.0240$
- Number of batches: $n = 22$
- Corresponding $t$-value for a 95% confidence level and $n - 1 = 21$ degrees of freedom: $t_{0.025, 21} \approx 2.0796$

Substituting these values into the confidence interval formula:

$$ CI = \left[ 0.4885 - 2.0796 \cdot \frac{0.0240}{\sqrt{22}} \ ; \ 0.4885 + 2.0796 \cdot \frac{0.0240}{\sqrt{22}} \right] = [0.4779 \ ; \ 0.4991] $$

This narrow confidence interval reflects the low variability across batch means (especially after applying variance reduction), indicating a high degree of precision in the estimated objective function for stable system configurations.

## 4. Experimental Design (Screening)
*(To be populated...)*

## 5. Comparative Analysis & Ranking and Selection
*(To be populated...)*

## 6. Conclusion
*(To be populated...)*
