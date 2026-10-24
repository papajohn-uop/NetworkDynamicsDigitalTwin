# Phase 3: Comparative Robustness & Performance Evaluation

This package contains the experimental test harnesses, stochastic channel models, and statistical analysis routines for benchmarking the $2 \times 2$ policy steering taxonomy.

---

## 1. Overview & Evaluation Methodology

Phase 3 subjects the four flow steering policies to two complementary rigorous evaluations:
1. **Part A: Deterministic Micro-Benchmark (Hero Trace)**:
   - Evaluates an active flow on Link B over a 20.0-second timeline (200 discrete polling samples at 100 ms).
   - Injects two controlled channel events:
     - **Transient Micro-Burst ($t = 5.0\text{--}5.1$ s)**: RTT jumps to $88\text{ ms}$ for exactly 100 ms (1 polling tick), then immediately recovers to nominal $50\text{ ms}$.
     - **Persistent Structural Step ($t \ge 10.0$ s)**: RTT permanently steps to $95\text{ ms}$, breaching the $\tau = 65\text{ ms}$ SLA ceiling.
   - Followed by 10 seconds of post-handover observation on Link A (Fiber, $4.3\text{ ms}$) confirming zero route flapping.
2. **Part B: Randomized Monte Carlo Stress-Testing**:
   - Executes **120 automated trial iterations** ($N = 30$ runs per policy).
   - Generates stochastic wireless fading with:
     - Background Gaussian jitter: $\mathcal{N}(50\text{ ms}, 5^2)$
     - Poisson noise micro-bursts ($\lambda = 0.5\text{ s}^{-1}$)
     - Random structural step onset $t_{\text{step}} \sim \mathcal{U}[5.0, 9.0]\text{ s}$
   - Computes empirical statistics for route flapping, false handover ratios, and SLA violation lag.

---

## 2. Package Architecture

```
phase3_eval/
├── __init__.py               # Package exports & public API
├── run_hero_trace.py         # Part A: Deterministic micro-benchmark runner
├── run_monte_carlo.py        # Part B: 120-run stochastic batch orchestrator
├── analyze_phase3.py         # Plotting & statistical aggregation routine
└── README.md                 # Usage documentation & methodology reference
```

---

## 3. CLI Usage & Execution

### 3.1 Running the Hero Trace Micro-Benchmark
Run all 4 policies through the deterministic Hero Trace:
```bash
sudo python3 phase3_eval/run_hero_trace.py --policy all
```
*Outputs per-tick CSV traces to `ANALYSIS_RESULTS/PHASE3/hero_trace_policy_{1,2,3,4}.csv`.*

### 3.2 Running the Monte Carlo Stress-Testing Suite
Execute the 120-run stochastic evaluation:
```bash
sudo python3 phase3_eval/run_monte_carlo.py --runs 30
```
*Outputs raw trial logs to `ANALYSIS_RESULTS/PHASE3/monte_carlo_trials.csv` and statistical aggregates to `ANALYSIS_RESULTS/PHASE3/monte_carlo_summary.json`.*

### 3.3 Generating Publication Figures & LaTeX Tables
Generate all publication figures and LaTeX tables:
```bash
python3 phase3_eval/analyze_phase3.py
```
*Generates:*
- `plots/hero_trace_comparative.png` and `.pdf` (Figure 3 in conference paper)
- `plots/monte_carlo_pareto.png` and `.pdf` (Pareto frontier curve)
- `plots/monte_carlo_boxplots.png` and `.pdf` (Flapping frequency and detection lag boxplots)
- Formatted LaTeX markup for Table V and Table VI.
