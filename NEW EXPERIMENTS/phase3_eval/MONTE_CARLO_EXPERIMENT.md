# Phase 3 Stochastic Benchmark: 400-Trial Monte Carlo Evaluation

This document details the experimental design, stochastic channel model, and statistical analysis for the **Monte Carlo Robustness Suite** ($N = 100$ runs per policy, 400 trials total).

---

## 1. Overview & Evaluation Objective

While the deterministic **Hero Trace** ([`phase3_eval/HERO_TRACE_EXPERIMENT.md`](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/phase3_eval/HERO_TRACE_EXPERIMENT.md)) provides precise temporal dissection of a single controlled micro-burst and step event, real-world wireless and non-terrestrial backhauls exhibit stochastic fading, variable burst intervals, and unpredictable failure onsets.

The Monte Carlo benchmark stress-tests the $2 \times 2$ policy matrix over a large statistical sample ($N = 100$ independent trials per policy, 400 trials total) to quantify:
1. **False Handover Ratio (%):** The probability that a policy mistakenly triggers a route switch during pre-step transient noise ($t < t_{\text{step}}$).
2. **SLA Violation Detection Lag ($T_{\text{detect}}$):** The elapsed time (in ms) from the true onset of structural degradation ($t_{\text{step}}$) until the policy executes a Netlink route switch.
3. **Route Flapping Frequency:** The average number of handovers triggered per session.
4. **Cumulative SLA Violation Duration:** The total time (in ms) user traffic is subjected to RTTs exceeding $\tau = 65.0\text{ ms}$.

---

## 2. Stochastic Channel Emulation Model

Each trial executes inside the 3-namespace Linux emulation environment over a **20.0-second session** with telemetry polled at $T_{\text{poll}} = 100\text{ ms}$ (10 Hz).

### 2.1 Baseline Channel Parameters
* **Link A (Backup Fiber):** HTB $100\text{ Mbit/s}$, delay $2.0\text{ ms}$ (RTT $\approx 4.3\text{ ms}$), $0.0\%$ loss.
* **Link B (Cellular Relay):** HTB $50\text{ Mbit/s}$, delay $25.0\text{ ms}$, Gaussian jitter $\pm 2.5\text{ ms}$ (nominal RTT $\approx 50.7\text{ ms}$), $0.5\%$ loss.
* **SLA Threshold ($\tau$):** $65.0\text{ ms}$.

### 2.2 Stochastic Disturbance Generation

For each trial index $k \in \{0, \dots, 99\}$, an identical stochastic profile is pre-generated across all 4 policies to ensure fair, paired comparative evaluation:

1. **Random Step Onset ($t_{\text{step}}$):**
   The onset of permanent structural degradation is drawn from a continuous uniform distribution:
   $$t_{\text{step}} \sim \mathcal{U}(5.0, 9.0)\text{ seconds}$$
   At $t \ge t_{\text{step}}$, Link B permanently degrades to $+40\text{ ms}$ delay ($RTT \approx 95.5\text{ ms}$), violating $\tau$.

2. **Poisson Arrival Process of Micro-Bursts:**
   In the pre-step window $t \in [0.5, t_{\text{step}} - 0.2]$, transient noise bursts arrive according to a Poisson process with intensity parameter:
   $$\lambda = 0.5\text{ s}^{-1} \quad (\text{mean inter-arrival time } \mathbb{E}[\Delta t] = 2.0\text{ s})$$
   For each arrival:
   * **Duration:** $d_{\text{burst}} \sim \mathcal{U}(80, 150)\text{ ms}$ (spanning 1 to 2 discrete telemetry polling ticks).
   * **Delay Amplitude:** $A_{\text{burst}} \sim \mathcal{U}(32.0, 55.0)\text{ ms}$, driving RTT up to $82\text{--}105\text{ ms}$ ($> \tau$).
   * Upon burst completion, the channel immediately reverts to nominal baseline ($50.7\text{ ms}$).

---

## 3. Evaluated Performance Metrics

For each trial, the orchestrator records:
* **False Alarm ($FA$):**
  $$FA = \begin{cases} 1, & \text{if first handover occurs at } t_{\text{handover}} < t_{\text{step}} \\ 0, & \text{otherwise} \end{cases}$$
* **Detection Lag ($T_{\text{detect}}$):**
  If a policy suffered a false alarm, $T_{\text{detect}} = 0\text{ ms}$ (as it is already on Link A). Otherwise:
  $$T_{\text{detect}} = \max(0.0, (t_{\text{handover}} - t_{\text{step}}) \times 1000.0) \quad (\text{ms})$$
* **SLA Violation Duration:**
  $$\text{Duration} = \sum_{t} \mathbb{I}(RTT(t) > \tau) \times T_{\text{poll}} \quad (\text{ms})$$

---

## 4. Execution & Orchestration

The test harness is implemented in [`phase3_eval/run_monte_carlo.py`](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/phase3_eval/run_monte_carlo.py).

```bash
# Execute 100 runs per policy (400 trials total) across 20.0s timeline
sudo python3 phase3_eval/run_monte_carlo.py --runs 100 --duration 20.0
```

* Results are written to:
  * Raw trial-by-trial log: `ANALYSIS_RESULTS/PHASE3/monte_carlo_trials.csv`
  * Statistical summary: `ANALYSIS_RESULTS/PHASE3/monte_carlo_summary.json`
* Once complete, publication plots and LaTeX tables are generated via:
  ```bash
  python3 phase3_eval/analyze_phase3.py
  ```
