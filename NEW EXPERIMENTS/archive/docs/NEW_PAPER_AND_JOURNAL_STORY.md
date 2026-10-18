# Multi-Backhaul Selection for 5G/6G Networks via a Kernel-Native Emulation Testbed

## 1. Problem Statement & Endgame

### The Real-World Scenario
In next-generation 5G-Advanced and 6G deployments, a local network (e.g., private 5G cell, edge node, or mobile tactical unit) often has access to **multiple concurrent backhaul connections** to reach the public internet:
1. **Terrestrial High-Speed Link** (e.g., optical fiber or dedicated microwave link)
2. **Cellular Wireless Backhaul** (e.g., public 5G/LTE macrocell relay)
3. **Non-Terrestrial Network (NTN)** (e.g., LEO satellite constellations such as Starlink or OneWeb)

Each connection exhibits distinct, dynamically changing characteristics in terms of bandwidth, latency, jitter, and packet loss.

### The Objective
We want to design and evaluate an **intelligent selection and steering mechanism** that evaluates all candidate backhauls in real time and dynamically assigns or migrates traffic flows to the best link based on specific application Service Level Agreements (SLAs).

#### Example A: Single-Objective Selection (Latency-Critical / URLLC)
* **Requirement**: Ultra-low latency and minimal jitter.
* **Mechanism**: Monitor round-trip latency on candidate links and route traffic through the path with the lowest measured delay.

#### Example B: Single-Objective Selection (Throughput-Critical / eMBB)
* **Requirement**: Maximum bulk data transfer speed.
* **Mechanism**: Monitor available bottleneck bandwidth and loss rate to select the path offering the highest effective goodput.

#### Example C: Multi-Objective Selection (Balanced / Mixed Traffic)
* **Requirement**: Simultaneously satisfy conflicting requirements (e.g., acceptable latency, high bandwidth, and low packet loss).
* **Mechanism**: Formulate a Multi-Criteria Decision-Making (MCDM) scoring system or utility function:
  $$U_i = w_{\text{lat}} \cdot f(L_i) + w_{\text{tput}} \cdot f(B_i) + w_{\text{loss}} \cdot f(P_i) - \text{Cost}_{\text{handover}}$$
  The candidate link maximizing utility $U_i$ is chosen.

---

## 2. Methodology: Why Custom Emulation?

To design and test such a selection mechanism, we face a methodological challenge:
1. **Field Testing is Infeasible**: Testing over live commercial satellite or cellular networks is costly, non-reproducible, and uncontrollable due to uncontrolled background traffic and atmospheric RF noise.
2. **Pure Simulation (e.g., ns-3) is Insufficient**: Discrete-event simulators abstract away the real Linux kernel network stack, omitting socket lifecycle events, route-cache flushing, bufferbloat, and netlink interface notification delays.
3. **Our Solution**: Build a lightweight, bare-metal **Kernel-Native Emulation Platform** using:
   - Linux Network Namespaces (`netns`) for process and network stack isolation.
   - Virtual Ethernet pairs (`veth`) representing multi-homed backhaul links.
   - Linux Traffic Control (`tc`) with Hierarchical Token Bucket (`htb`), Network Emulator (`netem`), and Fair Queue CoDel (`fq_codel`) to inject reproducible rate limits, delays, jitter, and loss.

---

## 3. The Two-Stage Paper Architecture

Before we can use our emulator to test multi-backhaul selection algorithms, **we must rigorously verify that the emulator itself faithfully reproduces real-world network dynamics and Linux TCP stack behavior**.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        STAGE 1: EMULATOR VERIFICATION SUITE                            │
│  Goal: Prove that our custom emulation harness (netns + veth + tc) behaves accurately   │
│        across both pristine and degraded channel conditions without artifacts.         │
│                                                                                        │
│  • Part 1: Pristine Link Verification (Exp 1 & Exp 2)                                  │
│  • Part 2: Parametric Impairment Verification (Exp 3 & Exp 4)                          │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼ (Emulator is verified & calibrated)
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                    STAGE 2: MULTI-BACKHAUL SCENARIOS & SELECTION                       │
│  Goal: Emulate realistic heterogeneous backhaul paths and evaluate dynamic link        │
│        selection and traffic steering algorithms.                                      │
│                                                                                        │
│  • Part 3: Heterogeneous Backhaul Scenario Profiles (Fiber vs. 5G vs. NTN/Satellite)   │
│  • Part 4: Dynamic Link Selection Algorithm Evaluation (Single & Multi-Objective)      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Test Specifications to Be Executed

### Stage 1: Emulator Verification & Calibration Test Matrix
*(Designed to validate emulator correctness against transport-layer theoretical models. Tests are performed for both uninterrupted baselines and mid-transfer link migrations.)*

| Test ID | Test Category | Target Protocol | Parameter Configuration | Evaluated Payloads | Iterations | Verification Purpose |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **EXP 1** | Pristine Verification | **TCP CUBIC** | Rate: 50 Mbit/s<br>Delay: 0 ms<br>Loss: 0%<br>Jitter: 0 ms | 50, 100, 150, 200, 250, 300, 350, 400, 450, 500 MB | 10 per size (100 pairs) | Verify rate-limiter accuracy (HTB), namespace isolation, and baseline switching overhead invariance across file sizes. |
| **EXP 2** | Pristine Verification | **TCP Reno** | Rate: 50 Mbit/s<br>Delay: 0 ms<br>Loss: 0%<br>Jitter: 0 ms | 50, 100, 150, 200, 250, 300, 350, 400, 450, 500 MB | 10 per size (100 pairs) | Verify AIMD behavior in clean channels and check algorithmic parity against CUBIC. |
| **EXP 3A** | Latency Sweep Verification | **TCP CUBIC** | Rate: 50 Mbit/s<br>Delay: `10, 20, 40, 80, 160 ms`<br>Loss: 0%, Jitter: 0 ms | 100 MB, 200 MB | 10 per config (50 pairs) | Verify that injected delay scales round-trip times and switching overhead linearly ($\Delta T \propto \text{RTT}$) as predicted by theory. |
| **EXP 3B** | Loss Sweep Verification | **TCP CUBIC** | Rate: 50 Mbit/s<br>Delay: 20 ms<br>Loss: `0.1%, 0.5%, 1%, 2%, 5%` | 100 MB, 200 MB | 10 per config (50 pairs) | Verify that artificial packet drops trigger correct TCP window reductions and goodput decay following the Mathis model. |
| **EXP 3C** | Jitter Sweep Verification | **TCP CUBIC** | Rate: 50 Mbit/s<br>Delay: 40 ms<br>Jitter: `±2, ±5, ±10, ±20 ms`<br>Loss: 0% | 100 MB, 200 MB | 10 per config (40 pairs) | Verify emulator stability under packet dispersion and check transport resilience against delay variance. |
| **EXP 4A** | Latency Sweep Verification | **TCP Reno** | Rate: 50 Mbit/s<br>Delay: `10, 20, 40, 80, 160 ms`<br>Loss: 0%, Jitter: 0 ms | 100 MB, 200 MB | 10 per config (50 pairs) | Verify Reno's classic RTT-dependent AIMD growth under increasing propagation delay. |
| **EXP 4B** | Loss Sweep Verification | **TCP Reno** | Rate: 50 Mbit/s<br>Delay: 20 ms<br>Loss: `0.1%, 0.5%, 1%, 2%, 5%` | 100 MB, 200 MB | 10 per config (50 pairs) | Verify Reno's recovery dynamics under random channel drops in comparison to CUBIC. |
| **EXP 4C** | Jitter Sweep Verification | **TCP Reno** | Rate: 50 Mbit/s<br>Delay: 40 ms<br>Jitter: `±2, ±5, ±10, ±20 ms`<br>Loss: 0% | 100 MB, 200 MB | 10 per config (40 pairs) | Verify Reno transport stability under delay jitter. |

---

### Stage 2: 5G Multi-Backhaul Scenarios & Selection Evaluation

#### A. Candidate Backhaul Link Profiles to Be Emulated
To represent a real-world multi-homed 5G edge deployment, the verified emulator will instantiate candidate backhaul paths with contrasting latency profiles:

| Backhaul Link ID | Representative Medium | Bottleneck Bandwidth | One-Way Latency | Jitter | Loss Rate | Primary Characteristic |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Link 1: Primary (Low-Latency)** | Terrestrial Fiber / mmWave Direct | **100 Mbit/s** | **2 ms** | 0 ms | 0.0% | Ultra-low latency path; preferred for latency-critical traffic. |
| **Link 2: Secondary (Cellular Relay)** | 5G Macrocell Wireless Relay | **50 Mbit/s** | **25 ms** | 5 ms | 0.5% | Moderate latency path; mobile, subject to congestion. |
| **Link 3: Backup (Satellite NTN)** | Non-Terrestrial LEO Satellite | **20 Mbit/s** | **60 ms** | 15 ms | 1.5% | High propagation latency; ubiquitous coverage fallback. |

---

#### B. Paper 1 Scope: Latency-Based Selection PoC Matrix
*(Proof-of-Concept for Paper 1 focused specifically on latency monitoring, lowest-RTT path selection, and dynamic failover.)*

| Test ID | Evaluation Scenario | Tested Selection Strategy | Evaluation Objective | Performance Metrics Measured |
| :--- | :--- | :--- | :--- | :--- |
| **POC-01** | Static Baseline (Control) | **Fixed Default Path** (No dynamic steering) | Establish reference delivery latency when traffic is locked to a degraded or high-latency backhaul. | End-to-End RTT, Transfer Completion Time, Goodput. |
| **POC-02** | Static Lowest-Latency Selection | **Initial Best-Path Binding**<br>$\arg\min(RTT_i)$ | Probe candidate paths at session initiation and bind the flow to the lowest-latency backhaul. | Initial Connection Setup Time, Steady-State RTT, Goodput. |
| **POC-03** | Dynamic Latency-Triggered Migration | **Real-Time Threshold Migration**<br>Migrate if $RTT_{\text{current}} > RTT_{\text{target}} + \delta$ | In-flight migration: Detect latency degradation on the active link and dynamically steer/migrate the active flow to the low-latency link. | Detection Time, Migration Overhead ($\Delta T$), RTT Recovery Latency, Flow Continuity. |

---

## 5. Two-Paper Publication Strategy (Conference Initial Paper $\rightarrow$ Journal Extension)

To maximize publication speed and scientific impact, the project follows a clear two-stage publication roadmap: **Paper 1 introduces the complete end-to-end framework with a clean Latency-Based Selection PoC**, while **Paper 2 serves as the definitive journal extension expanding into full Multi-Objective MCDM, all exhaustive sweep results, and dynamic channels**.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PAPER 1: THE INITIAL / CONFERENCE PAPER                         │
│  Scope: Complete End-to-End System with Latency-Driven Selection PoC                   │
│  Format: 6–8 Pages (e.g., IEEE GLOBECOM, ICC, NetSoft, WCNC)                           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  1. Motivation: 5G/6G multi-backhaul steering challenge (Fiber vs. Wireless vs. NTN).  │
│  2. Emulation Platform: Kernel-native netns + veth + tc testbed architecture.          │
│  3. Platform Verification Highlights: Proof that emulator faithfully enforces rates,   │
│     captures kernel TCP dynamics, and establishes the invariant handover overhead.     │
│  4. The Selection PoC: Latency-based monitoring and lowest-RTT path steering/migration.│
│  5. Initial Evaluation (POC-01 to POC-03): Demonstration of real-time latency detection│
│     and dynamic link migration restoring optimal RTT without breaking flows.           │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼ (Substantial Extension: ≥ 40-50% New Material)
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PAPER 2: THE EXTENDED JOURNAL PAPER                             │
│  Scope: Comprehensive Digital Twin, Full Verification Suite, Advanced MCDM & Dynamics  │
│  Format: 12–15 Pages (e.g., IEEE TNSM, IEEE TMC, Computer Networks)                    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  1. Full Verification Suite: Complete 56-configuration sweep matrix (all 1,520 runs)   │
│     with detailed statistical tables, variance, 95% CIs, and boxplots.                 │
│  2. Transport Inversion Deep Dive: Theoretical analysis of the CUBIC vs. Reno loss     │
│     reversal (explaining why Reno wins in loss and CUBIC wins in high RTT).            │
│  3. Multi-Objective MCDM Engine: Upgrade from latency-only PoC to full Multi-Objective │
│     decision-making (Bandwidth + Latency + Loss) using formal TOPSIS / AHP.            │
│  4. Dynamic & Time-Varying Channels: Satellite orbital pass-over fading, bursty cell    │
│     cross-traffic, and sudden link dropouts.                                           │
│  5. Hysteresis & Anti-Flapping: Cost-Aware Hysteresis using the exact empirical        │
│     handover penalty (ΔT ≈ 55ms + RTT) to suppress ping-pong switching.                │
│  6. Multi-Flow Scaling: Concurrent mixed traffic (simultaneous URLLC + eMBB flows).    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Side-by-Side Breakdown

| Dimension | Paper 1 (Initial / Conference: 6–8 Pages) | Paper 2 (Extended Journal: 12–15 Pages) |
| :--- | :--- | :--- |
| **Scientific Message** | *"An end-to-end framework and latency-driven selection PoC for 5G multi-backhaul, validated on a verified kernel testbed."* | *"A comprehensive digital twin with deep transport impairment characterization and advanced multi-criteria steering under dynamic 6G channels."* |
| **Emulator Verification Depth** | **Concise Highlights**: Verification of link throttling, baseline handover invariance ($O(1)$ scaling), and key impairment validation points. | **Exhaustive 56-Configuration Suite**: Full datasets from Experiments 1, 2, 3, and 4 (parametric sweeps, loss reversal physics, dispersion). |
| **Selection Mechanism** | **Latency-Driven PoC**: Real-time RTT probing, lowest-latency path selection, and threshold-triggered migration (`POC-01` to `POC-03`). | **Full Multi-Objective MCDM**: Multi-metric evaluation (Latency + Bandwidth + Loss via TOPSIS/AHP) + Cost-Aware Hysteresis. |
| **Channel Conditions** | **Controlled Link Profiles**: Backhaul links with fixed latency deltas (2ms vs. 25ms vs. 60ms). | **Dynamic & Non-Stationary Channels**: Time-varying satellite orbits, rain fade, and random cellular congestion spikes. |
| **Traffic Load** | Individual latency-sensitive and bulk flows. | Mixed, concurrent multi-user flows (simultaneous URLLC + eMBB competing for backhaul). |
| **New Material Compliance** | Initial baseline publication. | $\ge 50\%$ brand-new technical material, fulfilling IEEE/ACM journal extension criteria. |

