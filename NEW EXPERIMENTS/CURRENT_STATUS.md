# Edge Multi-Backhaul Softwarization: System Architecture, 3-Phase Methodology & Policy Matrix

## 1. System & Testbed Architecture Overview

The experimental framework deploys a lightweight, bare-metal Linux network emulation environment designed to replicate heterogeneous 5G/6G multi-backhaul paths without simulator abstractions or field-trial overheads.

### 1.1 Architectural Progression: Phase 1 (2-Namespace Direct) vs. Phase 2 & 3 (3-Namespace Gateway)

The emulation framework utilizes a deliberate two-stage architectural progression:

```
[PHASE 1: 2-NAMESPACE DIRECT CALIBRATION]
┌─────────────────────────┐                            ┌─────────────────────────┐
│        ns_client        │     Subnet 1 (10.0.1.0/24) │        ns_server        │
│       (`left-ns`)       ╞════════════════════════════╡       (`right-ns`)      │
│   veth-left1 (10.0.1.1) │     [tc htb / netem]       │ veth-right1 (10.0.1.2)  │
│                         │     Subnet 2 (10.0.2.0/24) │                         │
│   veth-left2 (10.0.2.1) ╞════════════════════════════╡ veth-right2 (10.0.2.2)  │
│   (Bulk LFTP Client)    │     [tc htb / netem]       │ (Dual-Homed FTP Daemon) │
└─────────────────────────┘                            └─────────────────────────┘

                                     │
                                     ▼ (Evolution to Edge Gateway Softwarization)

[PHASE 2 & 3: 3-NAMESPACE EDGE AGGREGATION GATEWAY]
┌─────────────────────────┐                            ┌─────────────────────────┐           ┌─────────────────────────┐
│        ns_client        │ Link A: Fiber (10.0.1.0/24)│        ns_router        │ Sink Link │        ns_server        │
│   (Multi-Homed Edge)    ├───────────────────────────▶│  (Aggregation Gateway)  ├──────────▶│ (Remote Cloud Endpoint)│
│                         │ Link B: Cell  (10.0.2.0/24)│   [tc netem / htb]      │(10.0.3/24)│                         │
│  [Telemetry & Steering] ├───────────────────────────▶│                         │           │     Single Destination  │
│  ip route replace def   │                            │  Intermediate Channel   │           │      IP: 10.0.3.2       │
└─────────────────────────┘                            └─────────────────────────┘           └─────────────────────────┘
```

1. **Phase 1 Architecture (Direct 2-Namespace Calibration):**
   * **Why 2 Namespaces:** Designed strictly to isolate transport-layer physics (congestion window deflation, Mathis loss scaling, token-bucket burstiness) without intermediate forwarding hops or route lookup overhead.
   * **Dual-Homed Destination:** The server namespace (`right-ns`) was directly dual-homed on both subnets (`10.0.1.2` and `10.0.2.2`).
   * **Migration Mechanics:** During mid-transfer migration runs, `lftp` halted at the 50% byte threshold on Subnet 1 (`10.0.1.2`), tore down its socket, and re-anchored directly to the secondary server IP on Subnet 2 (`10.0.2.2`).
   * **Traffic Control Location:** Applied directly on the virtual interface endpoints (`veth-left1/2` and `veth-right1/2`).

2. **Phase 2 & 3 Architecture (3-Namespace Edge Gateway):**
   * **Why 3 Namespaces (`ns_router`):** In a production 5G/6G edge network (e.g., 3GPP ATSSS), remote cloud destinations have a **single, fixed destination IP address** (`10.0.3.2`).
   * **Transparent Routing:** The client does not re-anchor to a different IP. Instead, `ns_client` changes its local routing table via Netlink (`ip route replace default via 10.0.1.2 dev veth_fiber_c`), while packets transparently traverse `ns_router` to reach `ns_server`.
   * **Decoupled Impairment Injection:** `ns_router` acts as an independent wireless channel where the Hero Trace transient spike ($88\text{ ms}$ at $t = 5.0\text{--}5.1\text{ s}$) and persistent structural step ($95\text{ ms}$ at $t = 10.0\text{ s}$) are injected dynamically without modifying client or server stack configurations.

---

### 1.2 System Specifications (Phase 2 & 3 Testbed)

* **Isolation Layer:** Implemented via Linux Network Namespaces (`netns`), instantiating three discrete network domains:
  * `ns_client`: The multi-homed edge terminal or gateway running active monitoring and flow steering daemons.
  * `ns_router`: The intermediate aggregation node hosting fine-grained queue management and synthetic link impairments.
  * `ns_server`: The remote destination endpoint hosting application and sink services.
* **Dual-Backhaul Topology:** Full-duplex Virtual Ethernet (`veth`) pairs interconnect namespaces across two distinct subnets:
  * **Link A (Primary Terrestrial / Fiber):** Subnet `10.0.1.0/24`. Configured pristine at 100 Mbps bottleneck capacity, 2 ms one-way delay (4 ms base RTT), 0% loss, managed by `fq_codel`.
  * **Link B (Secondary Wireless / Cellular Relay):** Subnet `10.0.2.0/24`. Configured impaired at 50 Mbps bottleneck capacity, 25 ms one-way delay (50 ms base RTT) with $\pm 5$ ms Gaussian jitter, 0.5% stochastic drop rate, managed by `fq_codel`.
  * **Sink Link:** Subnet `10.0.3.0/24`. High-capacity, unimpaired path bridging `ns_router` to `ns_server`.
* **Kernel Traffic Control (`tc`):** Egress queues inside `ns_router` combine Hierarchical Token Bucket (`htb`) for rate policing, Network Emulator (`netem`) for delay/jitter/loss injection, and Fair Queue CoDel (`fq_codel`) to eliminate synthetic bufferbloat artifacts.
* **Route Cache Hardening:** Execution of `sysctl -w net.ipv4.tcp_no_metrics_save=1` across all namespaces guarantees that TCP route-metrics (CWND, ssthresh, smoothed RTT) do not leak across consecutive migrations or test runs.
* **Pure Latency Telemetry Scope:** Telemetry and steering stability are evaluated purely via out-of-band ICMP ping probing ($T_p = 100$ ms) without background payload traffic. This deliberate decoupling isolates the control-plane decision dynamics, route replacement latency, and policy stability from confounding transport-layer congestion variables.

### System Architecture Schematic (Phase 2 & 3)

```
                  ┌─────────────────────────────────────────────────────────────┐
                  │                          ns_client                          │
                  │                                                             │
                  │  ┌───────────────────────┐       ┌───────────────────────┐  │
                  │  │   telemetry_daemon    │       │  steering_controller  │  │
                  │  │ (100ms ICMP prober)   │──────▶│ (Policy 1, 2, 3 or 4) │  │
                  │  └──────────┬────────────┘       └───────────┬───────────┘  │
                  │             │                                │              │
                  │             │                                ▼              │
                  │             │                     ip route replace default  │
                  └─────────────┼────────────────────────────────┼──────────────┘
                                │                                │
             ┌──────────────────┴───────────────┐                │
             │                                  │                │
             ▼ veth_fiber_c                     ▼ veth_cell_c    │
       (10.0.1.1/24)                      (10.0.2.1/24)          │
             │                                  │                │
             │   Link A (Primary): 100M, 2ms    │   Link B (Secondary): 50M, 25ms ± 5ms, 0.5% loss
             │                                  │
             ▼ veth_fiber_r                     ▼ veth_cell_r    │
       (10.0.1.2/24)                      (10.0.2.2/24)          │
  ┌─────────────────────────────────────────────────────────────┐│
  │                          ns_router                          ││
  │   tc netem/htb queues on egress; synthetic impairment       ││
  │   injection point (Hero Trace & Monte Carlo noise generator)││
  │                                                             ││
  │                          veth_sink_r (10.0.3.1/24)          ││
  └──────────────────────────────┬──────────────────────────────┘│
                                 │ Sink Link (100M, 0ms)         │
                                 ▼ veth_sink_s (10.0.3.2/24)     │
  ┌─────────────────────────────────────────────────────────────┐│
  │                          ns_server (Destination: 10.0.3.2)  │◀
  └─────────────────────────────────────────────────────────────┘
```

---

## 2. Three-Phase Experimental Methodology

The evaluation decouples low-level physical rate shaping from active edge routing logic across three sequential phases:

### Phase 1: Platform Verification & Calibration (Completed Empirical Benchmark)

Before deploying dynamic steering logic, the emulation platform underwent exhaustive verification across **1,520 empirical benchmark transfers** deployed on the direct 2-namespace point-to-point testbed (`left-ns` $\longleftrightarrow$ `right-ns`). This verified that the Linux kernel network stack, traffic control queuing disciplines, and namespace migration mechanisms operate with high physical fidelity and zero virtualization artifacts.

#### 1. Phase 1 Experimental Test Matrix (1,520 Runs Total)

| Experiment ID | Evaluation Profile | Target CCA | Evaluated Impairment Sweeps | Evaluated Payloads | Runs per Config | Total Transfers | Primary Verification Objective |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **Experiment 1** | Pristine Baseline & Migration | **TCP CUBIC** | Rate: 50 Mbps, Delay: 0 ms, Loss: 0%, Jitter: 0 ms | 50, 100, 150, 200, 250, 300, 350, 400, 450, 500 MB | 10 Baseline + 10 Migration | **200** | Confirm HTB token-bucket policing, testbed isolation, and evaluate handover scaling across file sizes. |
| **Experiment 2** | Pristine Baseline & Migration | **TCP Reno** | Rate: 50 Mbps, Delay: 0 ms, Loss: 0%, Jitter: 0 ms | 50, 100, 150, 200, 250, 300, 350, 400, 450, 500 MB | 10 Baseline + 10 Migration | **200** | Verify classic AIMD slow-start behavior and check algorithmic parity against CUBIC in clean channels. |
| **Experiment 3** | Parametric Impairment Sweeps | **TCP CUBIC** | • **3A (Latency):** 10, 20, 40, 80, 160 ms<br>• **3B (Loss):** 0.1%, 0.5%, 1%, 2%, 5%<br>• **3C (Jitter):** ±2, ±5, ±10, ±20 ms | 100 MB, 200 MB (+ baseline size sweeps) | 10 per config (Baseline & Migration) | **560** | Quantify high-BDP window inflation, Mathis inverse-square-root loss decay, and jitter dispersion stability. |
| **Experiment 4** | Parametric Impairment Sweeps | **TCP Reno** | • **4A (Latency):** 10, 20, 40, 80, 160 ms<br>• **4B (Loss):** 0.1%, 0.5%, 1%, 2%, 5%<br>• **4C (Jitter):** ±2, ±5, ±10, ±20 ms | 100 MB, 200 MB (+ baseline size sweeps) | 10 per config (Baseline & Migration) | **560** | Evaluate classic RTT-dependent AIMD growth under increasing propagation delay and channel loss. |

---

#### 2. Core Empirical Findings & Discovered Transport Envelopes

Phase 1 established six foundational empirical findings that provide the ground truth for our edge steering engine:

1. **The Handover Invariance Law ($O(1)$ Scaling):**
   * Mid-transfer handover dead-time ($\Delta T = T_{\text{migration}} - T_{\text{baseline}}$) is **asymptotically constant and strictly independent of payload volume** ($r \approx 0.05$):
     $$\Delta T_{\text{CUBIC}} = 52.24 \pm 30.67\text{ ms} \quad (\text{Median } = 52.20\text{ ms})$$
     $$\Delta T_{\text{Reno}} = 54.67 \pm 39.20\text{ ms} \quad (\text{Median } = 53.31\text{ ms})$$
   * The net delta of $+2.43\text{ ms}$ between Reno and CUBIC is statistically insignificant ($p > 0.05$).
   * **Physical Proof:** Because data transfer resumes seamlessly from the exact byte offset $S/2$ on the target interface, delivery duration cancels out:
     $$\Delta T(S) = \left[ \frac{S/2}{G} + T_{\text{failover}} + \frac{S/2}{G} \right] - \frac{S}{G} = T_{\text{failover}} \approx \text{Constant}$$

2. **Hyperbolic Overhead Amortization ($\rho(S) \propto 1/S$):**
   * Because absolute handover dead-time is invariant ($\approx 52\text{--}55\text{ ms}$) while transmission time scales linearly with payload volume ($T \propto S$), the relative handover penalty decays as an inverse hyperbola:
     * **At 50 MB:** $\rho = 0.48\%$ (CUBIC) and $0.66\%$ (Reno)
     * **At 100 MB:** $\rho = 0.33\%$ (CUBIC) and $0.33\%$ (Reno)
     * **At 500 MB:** $\rho = 0.08\%$ (CUBIC) and $0.08\%$ (Reno) — a **$10\times$ relative penalty reduction**.
   * *System Implication:* Handover dead-time is completely negligible for elephant and bulk flows.

3. **Pristine Algorithmic Parity ($\Delta \le 0.03\%$):**
   * Under pristine channel conditions (0% loss, 0 ms delay), TCP CUBIC and TCP Reno achieve identical transfer times and goodputs across all payload scales.
   * For a 500 MB transfer, baseline durations are **$87.848\text{ s}$** (CUBIC) and **$87.874\text{ s}$** (Reno) — a negligible delta of $+26.0\text{ ms}$ ($+0.03\%$). Both algorithms operate strictly in slow-start up to the HTB token-bucket ceiling without loss-driven window reductions.

4. **High-BDP Latency Divergence (+48.6% Speedup for CUBIC):**
   * When propagation delay sweeps up to 160 ms (base RTT $= 320\text{ ms}$, representing Non-Terrestrial Network / Satellite paths, $\text{BDP} \approx 2.0\text{ MB} = 1,380\text{ pkts}$), pristine parity collapses.
   * CUBIC achieves a **$+48.6\%$ speedup** over Reno. CUBIC's RTT-decoupled polynomial window curve ($W_{\text{cubic}}(t) = C(t-K)^3 + W_{\text{max}}$) rapidly inflates the window, whereas Reno's linear growth ($\frac{1}{\text{RTT}}$ per ACK) crawls, adding $+28.22\text{ s}$ on baseline and $+31.20\text{ s}$ on migration.

5. **The Loss-Regime Inversion ("Reno's Revenge"):**
   * Under channel packet drops ($p \ge 1\%$), the performance hierarchy dramatically inverts: **TCP Reno decisively outperforms CUBIC by up to 3.8 minutes!**
   * **Algorithmic Rationale:** In lossy channels where window sizes remain small, CUBIC operates in its "TCP-friendly" emulation mode. Because CUBIC uses a backoff factor of $\beta_{\text{cubic}} = 0.7$ (reducing CWND by 30%), its AIMD increase slope is restricted to:
     $$\alpha_{\text{friendly}} = 3 \cdot \frac{1 - \beta}{1 + \beta} = 3 \cdot \frac{0.3}{1.7} \approx 0.53\text{ MSS/RTT}$$
     In contrast, classic TCP Reno ($\beta_{\text{reno}} = 0.5$) increases by a full **$1.0\text{ MSS/RTT}$**, recovering its window nearly **$2\times$ faster** than CUBIC under continuous drops.

6. **Handover Overhead Negligibility in Lossy Wireless Channels:**
   * In lossy regimes ($p \ge 1\%$), Retransmission Timeouts (RTO) introduce massive random variance ($\sigma \approx 12\text{--}26\text{ s}$).
   * This stochastic channel noise completely dwarfs the deterministic physical handover dead-time ($\approx 55\text{ ms}$), meaning that link migration introduces virtually zero incremental penalty in degraded wireless channels.

---

#### 3. Summary of Quantitative Benchmark Results (Phase 1 Baseline & Sweeps)

| Metric / Scenario | TCP CUBIC (Empirical) | TCP Reno (Empirical) | Relative Advantage / Key Finding |
| :--- | :---: | :---: | :--- |
| **Mean Handover Overhead ($\Delta T$)** | **$52.24 \pm 30.67$ ms** | **$54.67 \pm 39.20$ ms** | **Handover Invariance Law ($O(1)$)**; net delta $+2.43$ ms ($p > 0.05$). |
| **Median Handover Overhead** | **$52.20$ ms** | **$53.31$ ms** | Robust non-parametric parity. |
| **Overhead at 50 MB Payload** | $40.50$ ms ($\rho = 0.48\%$) | $55.45$ ms ($\rho = 0.66\%$) | Baseline switching cost. |
| **Overhead at 500 MB Payload** | $66.42$ ms ($\rho = 0.08\%$) | $71.18$ ms ($\rho = 0.08\%$) | **$10\times$ Relative Penalty Amortization.** |
| **500 MB Pristine Baseline Duration** | $87.848 \pm 0.052$ s | $87.874 \pm 0.046$ s | **Algorithmic Parity ($\Delta = +0.03\%$)**. |
| **200 MB Completion @ 160 ms Delay** | **$43.71$ s** | **$71.93$ s** | **CUBIC is +48.6% faster** in high-BDP satellite regimes. |
| **200 MB Migration @ 160 ms Delay** | **$65.28$ s** | **$96.48$ s** | Reno incurs $+31.20$ s migration penalty. |
| **200 MB Completion @ 1.0% Loss** | $378.14$ s ($6.3$ min) | **$149.82$ s ($2.5$ min)** | **Reno is 3.8 minutes faster (Loss Inversion).** |
| **200 MB Completion @ 5.0% Loss** | $1,288.6$ s ($21.5$ min) | **$974.2$ s ($16.2$ min)** | Reno maintains recovery advantage under severe loss. |
| **Mathis Loss Model Decay Fit** | $R^2 = 0.994$ | $R^2 = 0.991$ | Validates inverse-square-root goodput collapse ($G \propto 1/\sqrt{p}$). |

### Phase 2: Dual-Path Telemetry & 2x2 Steering Framework
* Detailed documentation & results: [`phase2_telemetry/PHASE2_EXPERIMENTS.md`](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/phase2_telemetry/PHASE2_EXPERIMENTS.md)
* Modular LaTeX Section: [`paper/phase2_telemetry.tex`](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/paper/phase2_telemetry.tex)
* Out-of-band periodic active ICMP probing at 100 ms intervals across both interfaces.
* Decouples link health inspection from user payload dynamics.
* Evaluates a $2 \times 2$ decision taxonomy (Filtering Depth vs. Persistence).
* Executes Netlink route replacement and application re-anchoring.

### Phase 3: Comparative Robustness & Performance Evaluation (20.0s Timeline)
* **Part A: Deterministic Micro-Benchmark (Hero Trace)**
  * Detailed documentation: [`phase3_eval/HERO_TRACE_EXPERIMENT.md`](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/phase3_eval/HERO_TRACE_EXPERIMENT.md)
  * Modular LaTeX Section: [`paper/hero_trace.tex`](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/paper/hero_trace.tex)
  * 20.0s session timeline with 100 ms telemetry sampling interval.
  * Transient micro-burst (88 ms for 100 ms at $t = 5.0\text{--}5.1$ s).
  * Persistent structural degradation (delay steps to 95 ms at $t = 10.0$ s, breaching SLA $\tau=65$ ms).
  * Isolates false alarms from true SLA restoration across all 4 policies.
* **Part B: Randomized Monte Carlo Stress-Testing**
  * Detailed documentation: [`phase3_eval/MONTE_CARLO_EXPERIMENT.md`](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/phase3_eval/MONTE_CARLO_EXPERIMENT.md)
  * 400 automated test iterations ($N = 100$ runs per policy across 20.0s sessions).
  * Poisson-distributed noise bursts ($\lambda = 0.5\text{ s}^{-1}$) and random step arrivals ($t_{\text{step}} \sim \mathcal{U}(5.0, 9.0)\text{ s}$).
  * High-precision empirical aggregates: False alarm ratios, detection lag distributions, and SLA violation metrics.

---

## 3. The 2x2 Decision Policy Taxonomy

The steering engine evaluates path health across two design dimensions:
1. **Filtering Depth:** Instantaneous single sample vs. an arithmetic moving average across an $N$-sample sliding window.
2. **Temporal Persistence:** Memoryless single-tick reaction ($K=1$) vs. a multi-tick hysteresis confirmation counter ($K \ge 2$).

The target SLA threshold is configured at $\tau = 65$ ms. Sliding window size is fixed at $N = 3$ samples (300 ms depth), and hysteresis persistence is set to $K = 2$ consecutive intervals (200 ms confirmation).

| Persistence \ Depth | Single Sample (Raw RTT) | Averaged (Rolling Window, $N=3$) |
| :--- | :--- | :--- |
| **No Hysteresis ($K = 1$)** | **Policy 1: Strict Raw**<br>• Evaluates $RTT(t) > \tau$<br>• Zero memory / fastest reaction<br>• High false alarm risk | **Policy 3: Rolling Window Only**<br>• Evaluates $\text{Mean}(\mathcal{W}) > \tau$<br>• Dilutes moderate jitter<br>• Vulnerable to large single outliers |
| **With Hysteresis ($K = 2$)** | **Policy 2: Raw + Hysteresis**<br>• $RTT(t) > \tau$ for 2 ticks in a row<br>• Rejects micro-bursts without buffer lag<br>• **Pareto-Optimal ($200$ ms delay)** | **Policy 4: Window + Hysteresis**<br>• $\text{Mean}(\mathcal{W}) > \tau$ for 2 ticks in a row<br>• Maximum false-alarm protection<br>• Highest detection lag ($400$ ms) |

### Detailed Behavioral Descriptions

* **Policy 1 (Strict Raw RTT):**
  * **Operational Logic:** Evaluates each raw latency sample against the SLA ceiling. If an individual probe exceeds 65 ms, migration triggers immediately on that tick.
  * **Strengths:** Fastest possible reaction time ($T_{\text{detect}} = 100$ ms).
  * **Weaknesses:** Extreme vulnerability to wireless channel noise. Isolated packet delays, MAC-layer retransmissions, or RF scheduling jitter trigger false alarms, causing route flapping and unnecessary transport state resets.

* **Policy 2 (Raw RTT + Hysteresis):**
  * **Operational Logic:** Evaluates raw latency samples, but requires the threshold violation to persist across $K=2$ consecutive polling intervals before committing to a route switch.
  * **Strengths:** Effectively suppresses isolated transient micro-bursts without maintaining multi-sample memory buffers. Triggers within 200 ms on genuine structural path failure.
  * **System Verdict:** **Pareto-Optimal.** Delivers low false-positive rates with minimal detection lag.

* **Policy 3 (Rolling Window Average):**
  * **Operational Logic:** Maintains a FIFO ring buffer of the latest $N=3$ samples and evaluates their simple arithmetic mean against the SLA ceiling on every tick.
  * **Strengths:** Smooths moderate, high-frequency delay oscillations by diluting temporary spikes across the buffer window.
  * **Weaknesses:** A severe outlier spike (e.g., 150 ms) can inflate the 3-sample average above 65 ms, still causing an accidental trigger on a single bad interval.

* **Policy 4 (Rolling Window + Hysteresis):**
  * **Operational Logic:** Calculates the moving average across the $N=3$ sample buffer and requires this calculated mean to violate the SLA threshold for $K=2$ consecutive ticks.
  * **Strengths:** Maximum resilience against erratic channel variance. Produces near-zero false handovers in volatile environments.
  * **Weaknesses:** High cumulative detection latency ($T_{\text{detect}} \approx 400\text{--}500$ ms). The active flow lingers on the degraded link for multiple round trips, prolonging packet loss and throughput collapse before re-anchoring occurs.

---

## 4. Phase 3 Evaluation Scenarios

### Part A: Deterministic Micro-Benchmark (Hero Trace)
Evaluates an active session initially bound to Link B (50 ms base RTT, 10.0.2.0/24) communicating with `ns_server` (10.0.3.2) under two controlled events over a 20.0-second timeline:

```
Timeline (Seconds):
0.0s                  5.0s   5.2s                 10.0s                             20.0s
├── Nominal Link B ───┼─Burst─┼─── Nominal Link B ─┼── Persistent Structural Step ──┤
    (50 ms RTT)        (88 ms)     (50 ms RTT)         (95 ms RTT, SLA Breached)
```

1. **Transient Spike ($t = 5.0$ s):** Link latency artificially jumps from 25 ms to 44 ms (RTT jumps to 88 ms) for 200 ms (2 polling ticks), then immediately returns to 50 ms at $t = 5.2$ s.
   * **Policy 1 (Strict Raw, $K=1$):** Triggers a false handover at $t = 5.1$ s, unnecessarily executing a Netlink route switch to Link A and resetting transport state.
   * **Policy 2 (Raw + Hysteresis, $K=2$):** Observes a single violation tick. Because the channel recovers on the next tick, the confirmation counter resets to 0 at $t = 5.2$ s. **Spike absorbed without false handover.**
   * **Policy 3 (Rolling Window Only, $N=3, K=1$):** Subject to outlier poisoning. If the spike is sufficiently elevated, the arithmetic mean $\text{Mean}(\mathcal{W}_3)$ is pulled above $\tau = 65$ ms, triggering an accidental handover on an isolated outlier.
   * **Policy 4 (Rolling Window + Hysteresis, $N=3, K=2$):** The rolling mean does not violate $\tau$ for 2 consecutive ticks. **Spike absorbed.**

2. **Persistent Structural Degradation ($t = 10.0$ s):** Link latency permanently steps to 47.5 ms (RTT jumps permanently to 95 ms, violating the 65 ms SLA ceiling).
   * **Policy 1:** Prematurely switched at $t=5.1$ s (false alarm).
   * **Policy 2:** Confirms degradation across 2 intervals and triggers route switch at $t \approx 10.2$ s (200 ms detection delay). **Pareto-Optimal Trade-off.**
   * **Policy 3:** Moving average buffer fills and violates threshold at $t \approx 10.3$ s (300 ms detection delay).
   * **Policy 4:** Window mean confirmed across 2 consecutive ticks, triggering at $t \approx 10.4$ s (400 ms detection delay).

* **Publication Visualization:** High-resolution 4-panel time-series figure showing raw RTT, rolling window averages, the $\tau = 65\text{ ms}$ SLA ceiling dashed line, and distinct markers at the exact handover execution timestamps.

---

### Part B: Randomized Monte Carlo Stress-Testing
Evaluates statistical stability and operational boundaries across **120 automated trial iterations** ($N = 30$ independent runs per policy) under combined stochastic wireless conditions:

* **Background Gaussian Jitter:** $\mathcal{N}(50\text{ ms}, 5^2)$.
* **Poisson Noise Bursts:** Arrival intensity $\lambda = 0.4\text{ s}^{-1}$, durations randomly drawn between $50\text{--}150$ ms, amplitudes between $30\text{--}60$ ms.
* **Random Structural Congestion:** Step onset uniformly distributed at $t_{\text{step}} \sim U[3.0, 7.0]$ s, elevating path delay by $+40$ ms permanently (base RTT steps to 90 ms).

**Key Evaluated Metrics ($N = 30$ runs per policy):**
1. **Flapping Rate (Handovers per Run):** Policy 1 averages 2.4 handovers per run, exhibiting continuous route oscillation. Policy 2 maintains $1.0 \pm 0.1$ handovers per run. Policy 4 eliminates false handovers ($0.0\%$).
2. **False Alarm Ratio (%):** Percentage of runs triggering an accidental handover prior to the structural step onset ($t < t_{\text{step}}$).
3. **SLA Violation Detection Lag ($T_{\text{detect}} = t_{\text{switch}} - t_{\text{step}}$):**
   * Policy 1: $100\text{ ms}$ nominal (but corrupt by prior false triggers).
   * Policy 2: Bounded to $265 \pm 28\text{ ms}$.
   * Policy 4: Suffers prolonged violation lag of $486 \pm 39\text{ ms}$.
4. **Cumulative Time in SLA Violation:** Total duration (in ms) where user traffic experiences latency exceeding 65 ms.

* **Publication Visualizations:**
  * Boxplots of Flapping Frequency and SLA Violation Lag across the 4 policies.
  * **Pareto Frontier Plot:** Detection Lag (X-axis) vs. False Alarm Rate (Y-axis), demonstrating Policy 2 at the optimal inflection point.

---

## 5. Artifact Repository Structure (GitHub Directory Layout)

To ensure repeatability, reproducibility, and compliance with IEEE open-science artifact guidelines, the accompanying repository organizes configuration scripts, experimental drivers, analysis routines, and manuscript sources into a clean, publication-ready directory tree. The manuscript sources are divided into the active IEEE conference paper ([paper/main.tex](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/paper/main.tex)) and the comprehensive future journal extension ([journal_extension/journal_draft.md](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/journal_extension/journal_draft.md)):

```
NEW EXPERIMENTS/
├── CURRENT_STATUS.md                                 # Executive architecture, methodology & policy matrix
│
├── paper/                                           # STAGE 1: IEEE Conference Manuscript (Active Focus)
│   ├── main.tex                                     # IEEEtran conference paper (Flow Steering & Telemetry)
│   └── references.bib                               # Complete BibTeX bibliography (17 citations)
│
├── journal_extension/                               # STAGE 2: Future Journal Manuscript (Archival Extension)
│   ├── README.md                                    # Journal extension manifest & roadmap
│   └── journal_draft.md                             # Comprehensive 1,520-run CUBIC vs Reno empirical draft
│
├── phase2_telemetry/                                # Active ICMP telemetry and 2x2 steering controller
│   ├── telemetry_daemon.py                         # 100ms lightweight prober & circular buffer
│   └── steering_controller.py                      # 2x2 policy engine & Netlink actuator
│
├── phase3_eval/                                     # Hero Trace & Monte Carlo experimental harnesses
│   ├── run_hero_trace.py                           # Part A: Deterministic micro-benchmark runner
│   ├── run_monte_carlo.py                          # Part B: 120-run stochastic batch orchestrator
│   └── analyze_phase3.py                           # Plotting & statistical aggregation routine
│
├── scripts/                                         # Testbed emulation drivers and orchestration tools
│   ├── README.md                                    # Comprehensive testbed scripts & topology manual
│   ├── setup_phase2_topology.sh                     # 3-namespace multi-backhaul topology setup & impairment injector
│   ├── batch_runner.py                              # Automated multi-run testbed execution daemon
│   ├── lftp-migration-test.sh                       # Core namespace, netlink & traffic control orchestration
│   ├── cwnd_logger.sh                               # Kernel socket state polling routine via netlink (ss)
│   └── config.json                                  # Emulation topology & impairment parameter configuration
│
├── plots/                                           # High-resolution publication-ready vector and raster charts
│   ├── cubic_vs_reno_total_time.png                 # Total completion time comparisons across payload sizes
│   ├── cubic_vs_reno_overhead.png                   # Handover dead-time (Delta T) bar chart with 95% CIs
│   ├── cubic_vs_reno_handover_line.png              # Handover invariance law flat trajectory line
│   ├── cubic_vs_reno_relative_decay.png             # Hyperbolic relative overhead decay (rho proportional to 1/S)
│   ├── cubic_vs_reno_boxplots.png                   # Statistical dispersion & variance boxplots
│   └── impairments/                                 # Delay, packet loss, and jitter sweep validation plots
│
├── ANALYSIS_RESULTS/                                # Processed CSV data and statistical profiles
│   ├── BASELINE/                                    # Processed tables for pristine verification (Exp 1 & 2)
│   ├── IMPAIRMENTS/                                 # Processed tables for latency, loss & jitter sweeps (Exp 3 & 4)
│   └── PHASE3/                                      # Processed Hero Trace & Monte Carlo benchmark datasets
│
├── EXPERIMENT1/                                     # Raw datasets & logs: TCP CUBIC baseline verification
├── EXPERIMENT2/                                     # Raw datasets & logs: TCP Reno baseline verification
├── EXPERIMENT3/                                     # Raw datasets & logs: TCP CUBIC impairment sweeps
├── EXPERIMENT4/                                     # Raw datasets & logs: TCP Reno impairment sweeps
│
├── analyze_baseline_results.py                      # Automated statistical data processor & chart generator
├── analyze_impairments_results.py                   # Parametric sweep analyzer and Mathis model validator
├── MANUAL_ANALYSIS/                                 # Exploratory parsing scripts and intermediate results
│
└── archive/                                         # Archived legacy drafts, reports & prototypes
    ├── README.md                                    # Archive manifest & component descriptions
    ├── docs/                                        # Superseded markdown drafts & intermediate reports
    └── legacy_code/                                 # Superseded prototype script folders (original_scripts, etc.)
```

### Direct Clickable Links to Primary Repository Artifacts:

* **Executive Documentation & Manuscript Sources:**
  * [CURRENT_STATUS.md](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/CURRENT_STATUS.md) — System Architecture, 3-Phase Methodology & Policy Matrix
  * [paper/main.tex](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/paper/main.tex) — Stage 1: Active IEEE Conference Manuscript
  * [paper/references.bib](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/paper/references.bib) — Conference Paper BibTeX Bibliography
  * [journal_extension/journal_draft.md](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/journal_extension/journal_draft.md) — Stage 2: Comprehensive Journal Extension Draft
  * [archive/README.md](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/archive/README.md) — Manifest of Archived Documents & Prototype Code

* **Phase 2 Telemetry & Steering Controller Engine:**
  * [phase2_telemetry/README.md](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/phase2_telemetry/README.md) — Telemetry and Steering Controller Overview & Usage Guide
  * [phase2_telemetry/telemetry_daemon.py](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/phase2_telemetry/telemetry_daemon.py) — 100ms lightweight raw ICMP prober, EWMA and sliding window tracking
  * [phase2_telemetry/steering_controller.py](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/phase2_telemetry/steering_controller.py) — 2x2 policy matrix, atomic Netlink route replacement, and event logger

* **Phase 3 Comparative Evaluation Suite:**
  * [phase3_eval/README.md](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/phase3_eval/README.md) — Phase 3 Evaluation Harness Manual & Benchmark Guide
  * [phase3_eval/run_hero_trace.py](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/phase3_eval/run_hero_trace.py) — Part A: Deterministic Micro-Benchmark Runner (Hero Trace)
  * [phase3_eval/run_monte_carlo.py](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/phase3_eval/run_monte_carlo.py) — Part B: 120-Run Randomized Monte Carlo Stress-Tester
  * [phase3_eval/analyze_phase3.py](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/phase3_eval/analyze_phase3.py) — Publication Figure Generator & LaTeX Table Aggregator

* **Core Testbed Orchestration & Drivers:**
  * [scripts/README.md](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/scripts/README.md) — Comprehensive Manual for Topology & Drivers
  * [setup_phase2_topology.sh](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/scripts/setup_phase2_topology.sh) — 3-namespace network topology provisioner, policy router & dynamic impairment injector
  * [lftp-migration-test.sh](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/scripts/lftp-migration-test.sh) — Core network namespace setup, traffic control, and migration trigger
  * [batch_runner.py](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/scripts/batch_runner.py) — Automated iteration orchestrator and batch executor
  * [cwnd_logger.sh](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/scripts/cwnd_logger.sh) — Netlink socket sampler tracking TCP CWND and RTT dynamics
  * [config.json](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/scripts/config.json) — Parameter configuration matrix for link profiles

* **Statistical Analyzers & Plotting Routines:**
  * [analyze_baseline_results.py](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/analyze_baseline_results.py) — Computes parametric and non-parametric stats and generates baseline figures
  * [analyze_impairments_results.py](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/analyze_impairments_results.py) — Sweeps parser, Mathis model curve fitter, and loss reversal analyzer

---

## 6. Implementation Roadmap & Execution Workflow (Phase 2 & Phase 3)

With Phase 1 (Platform Verification & Calibration) fully concluded across 1,520 empirical transfers, the framework proceeds to software implementation and evaluation of the **Phase 2 Telemetry & Steering Controller** and **Phase 3 Comparative Robustness Suite**.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 IMPLEMENTATION & EXECUTION ROADMAP                               │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                 │
│  [MILESTONE 1: PHASE 1 CALIBRATION] - COMPLETED                                                 │
│  • 1,520 Transfers across Pristine (Exp 1-2) and Impairment Sweeps (Exp 3-4).                    │
│  • Validated O(1) Handover Invariance (ΔT ≈ 52-55 ms) and Mathis Loss Decay.                    │
│                                           │                                                     │
│                                           ▼                                                     │
│  [MILESTONE 2: PHASE 2 STEERING ENGINE] - COMPLETED                                             │
│  • Built `phase2_telemetry/telemetry_daemon.py`:                                                │
│    - Non-intrusive 100 ms active ICMP raw socket prober across candidate interfaces.            │
│    - FIFO buffer maintaining latest N=3 samples and temporal persistence counter (K=2).         │
│  • Built `phase2_telemetry/steering_controller.py`:                                             │
│    - Configurable switch selecting Policies 1, 2, 3, or 4 against threshold τ = 65 ms.          │
│    - Atomic Netlink route replacement (`ip route replace default via 10.0.1.2 dev veth_client_a`) │
│      measured live with ~5.7 ms switching latency.                                              │
│                                           │                                                     │
│                                           ▼                                                     │
│  [MILESTONE 3: PHASE 3 EVALUATION SUITE] - COMPLETED                                            │
│  • Part A: Deterministic Hero Trace Runner (`phase3_eval/run_hero_trace.py`):                   │
│    - 20.0s timeline: 5.0s baseline, 100ms micro-burst at t = 5.0-5.1s, step at t = 10.0s.       │
│    - Policy 1 triggered false alarm at t = 5.011s; Policies 2, 3, 4 absorbed spike.             │
│  • Part B: Monte Carlo Randomized Stress-Tester (`phase3_eval/run_monte_carlo.py`):             │
│    - 120 automated trial iterations (30 runs per policy across 20.0s sessions).                 │
│    - Poisson burst generator (λ = 0.5 s⁻¹) and random structural step arrivals.                 │
│    - Policy 2 cut false alarms to 30.0% while achieving fast 109 ms detection lag.              │
│                                           │                                                     │
│                                           ▼                                                     │
│  [MILESTONE 4: PAPER INTEGRATION & PLOTTING] - COMPLETED                                        │
│  • Generated Publication Figures via `phase3_eval/analyze_phase3.py`:                           │
│    - Hero trace 5-panel plot (`plots/hero_trace_5panel.pdf` and `.png`).                        │
│    - Hero trace compact plot (`plots/hero_trace_compact.pdf` and `.png`).                       │
│    - Trade-off clean plot (`plots/monte_carlo_tradeoff_clean.pdf` and `.png`).                  │
│    - Trade-off compact with embedded table (`plots/monte_carlo_tradeoff_compact_table.pdf`).    │
│    - Trade-off compact with table legend (`plots/monte_carlo_tradeoff_with_table.pdf`).        │
│    - Flapping and violation lag boxplots (`plots/monte_carlo_boxplots.pdf` and `.png`).         │
│  • Updated `paper/main.tex` with empirical Tables V & VI.                                       │
│                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.1 Architecture for Phase 2 Software Modules (Completed)

1. **`phase2_telemetry/telemetry_daemon.py` (Client-Side Active Prober):**
   * Operates inside `ns_client`.
   * Sends 100 ms lightweight active ICMP probes concurrently over `veth_fiber_c` (`10.0.1.0/24`) and `veth_cell_c` (`10.0.2.0/24`) toward `ns_server` (`10.0.3.2`).
   * Evaluates link latency purely via raw ping sockets, strictly isolating control-plane decision dynamics from background payload traffic.
   * Maintains live data structures:
     * Raw sample: $RTT(t)$
     * Moving average buffer: $\text{Mean}(\mathcal{W}_N)$ for $N = 3$
     * Temporal persistence counters: $K_{\text{raw}}$ and $K_{\text{win}}$

2. **`phase2_telemetry/steering_controller.py` (The 2x2 Policy Engine):**
   * Evaluates the active path against SLA threshold $\tau = 65\text{ ms}$.
   * Supports runtime execution of the four policies:
     * **Policy 1:** $\text{If } RTT(t) > \tau \implies \text{Trigger Handover}$
     * **Policy 2:** $\text{If } RTT(t) > \tau \text{ for } 2 \text{ consecutive ticks} \implies \text{Trigger Handover}$
     * **Policy 3:** $\text{If } \text{Mean}(\mathcal{W}_3) > \tau \implies \text{Trigger Handover}$
     * **Policy 4:** $\text{If } \text{Mean}(\mathcal{W}_3) > \tau \text{ for } 2 \text{ consecutive ticks} \implies \text{Trigger Handover}$
   * Issues atomic Netlink route replacements via `ip route replace default via 10.0.1.2 dev veth_fiber_c` (5.2--6.0 ms latency).

### 6.2 Execution Workflow for Phase 3 Benchmarks (Completed)

1. **Part A: Hero Trace Execution (`phase3_eval/run_hero_trace.py`):**
   * Initializes `ns_router` with baseline Link B conditions (50 ms base RTT).
   * Initiates continuous ICMP ping telemetry stream from `ns_client` across 20.0s timeline.
   * At $t = 5.0\text{ s}$, injects transient spike ($+38\text{ ms} \implies 88\text{ ms}$) for 100 ms, reverting at $t = 5.1\text{ s}$.
   * At $t = 10.0\text{ s}$, injects permanent structural step ($+45\text{ ms} \implies 95\text{ ms}$).
   * Captures the decision responses of Policies 1, 2, 3, and 4 to verify spike absorption and reaction lag.

2. **Part B: Monte Carlo Stress-Testing (`phase3_eval/run_monte_carlo.py`):**
   * Loops through $N = 30$ iterations for each of the 4 policies (120 runs total) across 20.0s sessions.
   * Generates dynamic stochastic channel profiles on Link B:
     * Background Gaussian jitter: $\mathcal{N}(50\text{ ms}, 5^2)$.
     * Poisson noise bursts: $\lambda = 0.5\text{ s}^{-1}$, durations $80\text{--}150\text{ ms}$, amplitudes $32\text{--}55\text{ ms}$.
     * Random structural degradation step arriving uniformly between $t = 6.0\text{ s}$ and $t = 14.0\text{ s}$.
   * Automatically parses logs into `ANALYSIS_RESULTS/PHASE3/` and computes:
     * Flapping frequency (handovers per run).
     * False positive ratio (switches triggered by transient noise).
     * True SLA violation recovery latency (time elapsed from structural step onset to route replacement).

### 6.3 System Prerequisites & Kernel Hardening

To guarantee reproducibility when running the emulation platform, the host system requires:
* **Operating System:** Bare-metal Linux kernel $\ge 5.15$ with root / `sudo` capabilities.
* **Required Kernel Modules:** `sch_htb`, `sch_netem`, `sch_fq_codel`, `cls_u32`, `veth`.
* **Required System Utilities:** `iproute2` (for `ip netns` and `tc`), `ethtool`, `python3` ($\ge 3.8$), `numpy`, `pandas`, `matplotlib`, `scipy`.
* **Mandatory Route-Cache Hardening:**
  ```bash
  sudo sysctl -w net.ipv4.tcp_no_metrics_save=1
  ```
  *(Prevents the kernel from caching CWND, ssthresh, and RTT across consecutive handovers and iterations.)*

---

## 7. Two-Stage Publication Strategy (Conference Paper First $\to$ Journal Extension)

To maximize publication speed and scientific impact, the project follows a clear two-stage publication roadmap: **Paper 1 introduces the complete end-to-end framework with the 2x2 Steering Policy Matrix and Phase 3 evaluations**, while **Paper 2 serves as the comprehensive journal extension expanding into full Multi-Objective MCDM, all 1,520 sweep runs, and dynamic satellite channels**.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PAPER 1: THE INITIAL / CONFERENCE PAPER                         │
│  Scope: Complete End-to-End System with 2x2 Steering Policy Matrix & Phase 3 Robustness│
│  Format: 6–8 Pages (Target: IEEE GLOBECOM, ICC, NetSoft, or WCNC)                      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  1. Motivation: 5G/6G multi-backhaul edge steering challenge (Fiber vs. Wireless/NTN). │
│  2. Emulation Platform: Kernel-native netns + veth + tc softwarized testbed.           │
│  3. Platform Verification Highlights: Proof of rate enforcement and O(1) Handover       │
│     Invariance Law (ΔT ≈ 52–55 ms across 50MB–500MB payloads).                         │
│  4. The 2x2 Decision Matrix: Filtering Depth vs. Temporal Persistence (Policies 1–4).  │
│  5. Phase 3 Evaluations: Deterministic Hero Trace (transient vs. structural events)    │
│     and 120-run Monte Carlo stress testing demonstrating Policy 2 Pareto-optimality.   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼ (Substantial Extension: ≥ 40-50% New Material)
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PAPER 2: THE EXTENDED JOURNAL PAPER                             │
│  Scope: Comprehensive Digital Twin, Full Verification Suite, Advanced MCDM & Dynamics  │
│  Format: 12–15 Pages (Target: IEEE TNSM, IEEE TMC, or Computer Networks)               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  1. Full Verification Suite: Complete 56-configuration sweep matrix (all 1,520 runs)   │
│     with detailed statistical tables, variance, 95% CIs, and boxplots.                 │
│  2. Transport Inversion Deep Dive: Theoretical analysis of the CUBIC vs. Reno loss     │
│     reversal (explaining why Reno wins in loss and CUBIC wins in high RTT).            │
│  3. Multi-Objective MCDM Engine: Upgrade from latency-only to Multi-Objective          │
│     decision-making (Bandwidth + Latency + Loss) using formal TOPSIS / AHP.            │
│  4. Dynamic & Time-Varying Channels: Satellite orbital pass-over fading, bursty cell    │
│     cross-traffic, and sudden link dropouts.                                           │
│  5. Hysteresis & Anti-Flapping: Cost-Aware Hysteresis using the exact empirical        │
│     handover penalty (ΔT ≈ 55 ms + RTT) to suppress ping-pong switching.               │
│  6. Multi-Flow Scaling: Concurrent mixed traffic (simultaneous URLLC + eMBB flows).    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Side-by-Side Publication Comparison

| Dimension | Paper 1 (Initial / Conference: 6–8 Pages) | Paper 2 (Extended Journal: 12–15 Pages) |
| :--- | :--- | :--- |
| **Scientific Focus** | Complete edge multi-backhaul framework with $2 \times 2$ policy matrix, validated on verified kernel testbed. | Comprehensive digital twin with deep transport impairment characterization and advanced multi-criteria steering. |
| **Platform Verification Depth** | **Concise Highlights**: Rate policing, $O(1)$ Handover Invariance ($\Delta T \approx 52\text{--}55\text{ ms}$), and key impairment points. | **Exhaustive 56-Configuration Suite**: Full datasets from Experiments 1–4 ($1,520$ runs, parametric sweeps, loss reversal physics). |
| **Steering Engine** | **$2 \times 2$ Decision Matrix**: Single-sample vs. Rolling Window, Memoryless vs. Hysteresis (Policies 1–4). | **Full Multi-Objective MCDM**: Multi-metric evaluation (Latency + Bandwidth + Loss via TOPSIS/AHP) + Cost-Aware Hysteresis. |
| **Robustness Evaluation** | **Phase 3 Benchmarks**: Deterministic Hero Trace & 120-run Monte Carlo stress testing. | **Dynamic Non-Stationary Channels**: Time-varying LEO satellite orbital passes, rain fade, and cellular burst congestion. |
| **Telemetry Scope** | Pure latency telemetry via non-intrusive ICMP ping probes ($T_p = 100\text{ ms}$). | Multi-metric telemetry (ICMP ping + Netlink socket polling + active bandwidth estimation). |
| **New Material Compliance** | Initial baseline conference publication. | $\ge 50\%$ brand-new technical material, fulfilling IEEE/ACM journal extension criteria. |