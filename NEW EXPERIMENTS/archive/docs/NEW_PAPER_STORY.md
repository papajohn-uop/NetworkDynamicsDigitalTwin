# Multi-Backhaul Selection for 5G/6G Networks via a Kernel-Native Emulation Testbed (Paper 1 Blueprint)

## 1. Problem Statement & Endgame

### The Real-World Scenario
In next-generation 5G-Advanced and 6G deployments, a local network (e.g., private 5G cell, edge node, or mobile tactical unit) often has access to **multiple concurrent backhaul connections** to reach the public internet[cite: 1, 2]:
1. **Terrestrial High-Speed Link** (e.g., optical fiber or dedicated microwave link)[cite: 1, 2]
2. **Cellular Wireless Backhaul** (e.g., public 5G/LTE macrocell relay)[cite: 1, 2]
3. **Non-Terrestrial Network (NTN)** (e.g., LEO satellite constellations such as Starlink or OneWeb)[cite: 1, 2]

Each connection exhibits distinct, dynamically changing characteristics in terms of bandwidth, latency, jitter, and packet loss[cite: 1, 2].

### The Objective
We want to design and evaluate an **intelligent selection and steering mechanism** that evaluates all candidate backhauls in real time and dynamically assigns or migrates traffic flows to the best link based on specific application Service Level Agreements (SLAs)[cite: 1, 2].

#### Example A: Single-Objective Selection (Latency-Critical / URLLC) - Focus for Paper 1
* **Requirement**: Ultra-low latency and minimal jitter[cite: 1, 2].
* **Mechanism**: Monitor round-trip latency on candidate links and route traffic through the path with the lowest measured delay[cite: 1, 2].
* **Paper 1 Formulation**:
  $$i^* = \arg\min_{i \in \{1, 2, 3\}} (\text{RTT}_i)$$
  $$\text{Trigger migration if } \text{SRTT}_{\text{current}} > \text{RTT}_{\text{target}} + \delta$$
[cite: 1, 2]

#### Example B: Single-Objective Selection (Throughput-Critical / eMBB) - Context & Future Work
* **Requirement**: Maximum bulk data transfer speed[cite: 1, 2].
* **Mechanism**: Monitor available bottleneck bandwidth and loss rate to select the path offering the highest effective goodput[cite: 1, 2].

#### Example C: Multi-Objective Selection (Balanced / Mixed Traffic) - Reserved for Paper 2
* **Requirement**: Simultaneously satisfy conflicting requirements (e.g., acceptable latency, high bandwidth, and low packet loss)[cite: 1, 2].
* **Mechanism**: Formulate a Multi-Criteria Decision-Making (MCDM) scoring system or utility function:
  $$U_i = w_{\text{lat}} \cdot f(L_i) + w_{\text{tput}} \cdot f(B_i) + w_{\text{loss}} \cdot f(P_i) - \text{Cost}_{\text{handover}}$$
  The candidate link maximizing utility $U_i$ is chosen[cite: 1, 2].

> **Source Paper Reuse Status for Section 1**:
> - *Directly Reusable*: General background paragraphs arguing why discrete-event simulators (ns-3) lack real Linux socket lifecycles and why physical commercial backhaul trials lack repeatability.
> - *Brand New*: Multi-backhaul 5G/NTN routing challenge[cite: 1, 2], URLLC vs. eMBB SLA tension[cite: 1, 2], and framing the emulator as an enabling methodology rather than the primary contribution.

---

## 2. Methodology: Why Custom Emulation?

To design and test such a selection mechanism, we face a methodological challenge:
1. **Field Testing is Infeasible**: Testing over live commercial satellite or cellular networks is costly, non-reproducible, and uncontrollable due to uncontrolled background traffic and atmospheric RF noise[cite: 1, 2].
2. **Pure Simulation (e.g., ns-3) is Insufficient**: Discrete-event simulators abstract away the real Linux kernel network stack, omitting socket lifecycle events, route-cache flushing, bufferbloat, and netlink interface notification delays[cite: 1, 2].
3. **Our Solution**: Build a lightweight, bare-metal **Kernel-Native Emulation Platform** using:
   - Linux Network Namespaces (`netns`) for process and network stack isolation[cite: 1, 2].
   - Virtual Ethernet pairs (`veth`) representing multi-homed backhaul links[cite: 1, 2].
   - Linux Traffic Control (`tc`) with Hierarchical Token Bucket (`htb`), Network Emulator (`netem`), and Fair Queue CoDel (`fq_codel`) to inject reproducible rate limits, delays, jitter, and loss[cite: 1, 2].
   - Disabling route-cache persistence via `sysctl -w net.ipv4.tcp_no_metrics_save=1` to guarantee run-to-run statistical independence.
   - Non-intrusive polling telemetry using `ss -tin` over Netlink logging socket parameters (`snd_cwnd`, `rtt`, `retrans`) every 100 ms to `live_progress_trace.csv`.

> **Source Paper Reuse Status for Section 2**:
> - *Directly Reusable (100%)*: Descriptions of `netns` namespace boundaries, `veth` mechanics, `tc` qdisc pipeline (HTB, netem, fq_codel), `tcp_no_metrics_save` cache isolation, and the `ss` polling daemon.
> - *Brand New*: Update the network schematic diagram to explicitly label three egress interfaces: `veth_fiber` (Link 1), `veth_cell` (Link 2), and `veth_ntn` (Link 3)[cite: 1, 2].

---

## 3. The Two-Stage Paper Architecture

Before we can use our emulator to test multi-backhaul selection algorithms, **we must rigorously verify that the emulator itself faithfully reproduces real-world network dynamics and Linux TCP stack behavior**[cite: 1, 2].

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        STAGE 1: EMULATOR VERIFICATION SUITE                            │
│  Goal: Prove that our custom emulation harness (netns + veth + tc) behaves accurately   │
│        across both pristine and degraded channel conditions without artifacts.         │
│                                                                                        │
│  • Part 1: Pristine Link Verification (Rate Throttling & Invariant Handover Cost)      │
│  • Part 2: Parametric Impairment Verification (RTT Delay Scaling & Mathis Loss Decay)  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼ (Emulator is verified & calibrated)
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                    STAGE 2: MULTI-BACKHAUL SCENARIOS & SELECTION                       │
│  Goal: Emulate realistic heterogeneous backhaul paths and evaluate dynamic link        │
│        selection and traffic steering algorithms.                                      │
│                                                                                        │
│  • Part 3: Heterogeneous Backhaul Scenario Profiles (Fiber vs. 5G vs. NTN/Satellite)   │
│  • Part 4: Dynamic Latency-Driven Steering & Re-Anchoring Evaluation (POC-01 to 03)   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

> **Source Paper Reuse Status for Section 3**:
> - *Directly Reusable*: None (structural framing concept).
> - *Brand New*: The explicit two-stage narrative flow (calibration first, application steering second) to eliminate the Reviewer 1 criticism regarding scientific rigor[cite: 1, 2].

---

## 4. Test Specifications & Section Layout for Paper 1

### Stage 1: Emulator Verification & Calibration Highlights (Section III of Paper)

*(Strictly scoped to TCP CUBIC highlights to demonstrate rate enforcement, linear RTT delay scaling, and loss degradation without cluttering the conference paper.)*

| Test ID | Test Category | Target Protocol | Parameter Configuration | Evaluated Payloads | Iterations | Verification Purpose & Paper Role |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **EXP 1** | Pristine Verification | **TCP CUBIC** | Rate: 50 Mbit/s<br>Delay: 0 ms<br>Loss: 0%<br>Jitter: 0 ms[cite: 1, 2] | 50, 100, 150, 200, 250, 300, 350, 400, 450, 500 MB[cite: 1, 2] | 10 per size (100 pairs)[cite: 1, 2] | **Rate Accuracy & Overhead Invariance**: Prove transfer completion time scales linearly ($R^2 > 0.999$) and migration penalty $\Delta T \approx 55\text{ ms} \pm 4\text{ ms}$ is strictly an $O(1)$ constant across file sizes[cite: 1, 2]. |
| **EXP 3A** | Latency Sweep Verification | **TCP CUBIC** | Rate: 50 Mbit/s<br>Delay: `10, 20, 40, 80, 160 ms`<br>Loss: 0%, Jitter: 0 ms[cite: 1, 2] | 100 MB[cite: 1, 2] | 10 per config (50 pairs)[cite: 1, 2] | **Delay Proportionality**: Prove injected delay scales round-trip times and switching overhead linearly ($\Delta T \propto \text{RTT}$) as predicted by transport theory[cite: 1, 2]. |
| **EXP 3B** | Loss Sweep Verification | **TCP CUBIC** | Rate: 50 Mbit/s<br>Delay: 20 ms<br>Loss: `0.1%, 0.5%, 1%, 2%, 5%`[cite: 1, 2] | 100 MB[cite: 1, 2] | 10 per config (50 pairs)[cite: 1, 2] | **Mathis Window Decay**: Prove packet drops trigger expected kernel window reductions and goodput decay proportional to $1/\sqrt{p}$[cite: 1, 2]. |

*(Note: Reno sweeps EXP 2 and EXP 4A–4C, jitter sweeps EXP 3C, and large-scale dispersion tables are held back for the Journal Paper 2 extension)[cite: 1, 2].*

> **Source Paper Reuse Status for Stage 1 (Section III)**:
> - *Directly Reusable*: The 100 MB baseline pristine data point and the 20 ms / 0.5% loss data point; the technical prose explaining HTB token-bucket bursts (~70 Mbps transient overshoot) and related literature citations (Devera, Jacobson).
> - *Brand New*: Running payload sweeps from 50 to 500 MB for EXP 1[cite: 1, 2]; delay sweep across 10–160 ms for EXP 3A[cite: 1, 2]; loss sweep across 0.1%–5% for EXP 3B[cite: 1, 2]; plotting curves with 95% confidence interval error bars.

---

### Stage 2: 5G Multi-Backhaul Scenarios & Selection Evaluation (Section IV of Paper)

#### A. Candidate Backhaul Link Profiles to Be Emulated
To represent a real-world multi-homed 5G edge deployment, the verified emulator will instantiate candidate backhaul paths with contrasting latency and impairment profiles[cite: 1, 2]:

| Backhaul Link ID | Representative Medium | Bottleneck Bandwidth | One-Way Latency | Jitter | Loss Rate | Primary Characteristic |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Link 1: Primary (Low-Latency)** | Terrestrial Fiber / mmWave Direct[cite: 1, 2] | **100 Mbit/s**[cite: 1, 2] | **2 ms**[cite: 1, 2] | 0 ms[cite: 1, 2] | 0.0%[cite: 1, 2] | Ultra-low latency path; preferred for latency-critical traffic[cite: 1, 2]. |
| **Link 2: Secondary (Cellular Relay)** | 5G Macrocell Wireless Relay[cite: 1, 2] | **50 Mbit/s**[cite: 1, 2] | **25 ms**[cite: 1, 2] | 5 ms[cite: 1, 2] | 0.5%[cite: 1, 2] | Moderate latency path; mobile, subject to intermediate congestion[cite: 1, 2]. |
| **Link 3: Backup (Satellite NTN)** | Non-Terrestrial LEO Satellite[cite: 1, 2] | **20 Mbit/s**[cite: 1, 2] | **60 ms**[cite: 1, 2] | 15 ms[cite: 1, 2] | 1.5%[cite: 1, 2] | High propagation latency; ubiquitous coverage fallback[cite: 1, 2]. |

#### B. Paper 1 Scope: Latency-Based Selection PoC Matrix
*(Proof-of-Concept for Paper 1 focused specifically on latency monitoring, lowest-RTT path selection, and dynamic failover)[cite: 1, 2].*

| Test ID | Evaluation Scenario | Tested Selection Strategy | Evaluation Objective | Performance Metrics Measured |
| :--- | :--- | :--- | :--- | :--- |
| **POC-01** | Static Baseline (Control)[cite: 1, 2] | **Fixed Default Path** (No dynamic steering)[cite: 1, 2] | Establish reference delivery latency and completion times when traffic is locked to a degraded cellular or satellite link[cite: 1, 2]. | End-to-End RTT, Transfer Completion Time, Goodput[cite: 1, 2]. |
| **POC-02** | Static Lowest-Latency Selection[cite: 1, 2] | **Initial Best-Path Binding**<br>$i^* = \arg\min(RTT_i)$[cite: 1, 2] | Probe candidate paths at session initiation and immediately bind the flow to the lowest-latency backhaul (Link 1)[cite: 1, 2]. | Initial Connection Setup Time, Steady-State RTT, Goodput[cite: 1, 2]. |
| **POC-03** | Dynamic Latency-Triggered Migration[cite: 1, 2] | **Real-Time Threshold Migration**<br>Migrate if $\text{SRTT}_{\text{current}} > \text{RTT}_{\text{target}} + \delta$[cite: 1, 2] | In-flight migration: Detect latency degradation on the active link (Link 2) and dynamically steer/re-anchor the flow to Link 1[cite: 1, 2]. | Detection Time, Migration Overhead ($\Delta T$), RTT Recovery Latency, Flow Continuity[cite: 1, 2]. |

> **Source Paper Reuse Status for Stage 2 (Section IV)**:
> - *Directly Reusable*: The bash script shell hooks that invoke `ip route replace` and restart application-level transfer sessions (`lftp`).
> - *Brand New (100%)*: All text formulating the heterogeneous link profiles[cite: 1, 2], the mathematical threshold migration logic[cite: 1, 2], and the execution data for POC-01, POC-02, and POC-03[cite: 1, 2].
> - *Hero Figure (New)*: A three-panel synchronized time-series plot of POC-03 showing:
>   1. Throughput (Mbps) transitioning from Link 2 (50 Mbps) to Link 1 (100 Mbps) with a 55 ms dip[cite: 1, 2].
>   2. RTT (ms) dropping from 50 ms down to 4 ms[cite: 1, 2].
>   3. CWND (`snd_cwnd`) resetting to $IW=10$ and quickly scaling on the pristine link.

---

### Section V: Related Work & Discussion (Target: ~0.5 Page)

* **Testbed Comparison**: Contrast lightweight kernel-native emulation (`netns` + `tc`) against discrete-event simulators (ns-3) and heavy physical testbeds[cite: 1, 2].
* **Dynamic Multipath Management**: Position against 3GPP AT3S (Access Traffic Steering, Switching, and Splitting) and SDN edge frameworks.
* **State Reset vs. State Preservation**: Contrast application-level session re-anchoring (which resets congestion state) against MPTCP and QUIC connection migration (which attempt to preserve state). Highlight that escaping a lossy, degraded link via a clean state reset avoids carrying damaged congestion windows into a high-capacity link.

> **Source Paper Reuse Status for Section V**:
> - *Directly Reusable*: Existing literature citations comparing Mininet, CORE, and physical testbeds.
> - *Brand New*: Citations and text discussing 3GPP AT3S, 5G/6G NTN backhauls, and the empirical justification for transport state reset over degraded paths.

---

### Section VI: Conclusion and Future Work (Target: ~0.5 Page)

* **Conclusion**: Summarize how Stage 1 calibration verified rate accuracy and constant $O(1)$ switching overhead ($\Delta T \approx 55$ ms), and how Stage 2 demonstrated that latency-driven session re-anchoring successfully bounds RTT across heterogeneous backhauls[cite: 1, 2].
* **Future Work**: Explicitly outline the roadmap for the upcoming journal paper:
  - Multi-objective decision-making (TOPSIS/AHP) combining bandwidth, loss, and latency[cite: 1, 2].
  - Anti-flapping hysteresis mechanisms accounting for empirical switching costs[cite: 1, 2].
  - Dynamic orbital satellite fading models and TCP Reno/BBR comparative evaluations[cite: 1, 2].

> **Source Paper Reuse Status for Section VI**:
> - *Brand New (100%)*: Single integrated section addressing Reviewer 2, providing a clean synthesis and establishing the journal extension boundary[cite: 1, 2].