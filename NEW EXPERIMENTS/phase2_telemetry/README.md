# Phase 2: Active Dual-Path Telemetry & 2x2 Steering Controller

This package implements the active telemetry prober and dynamic flow steering engine for the 3-namespace 5G/6G multi-backhaul emulation platform.

---

## 1. Overview & Architecture

In next-generation multi-access edge networks (e.g., 3GPP ATSSS), edge devices must dynamically switch between heterogeneous access links (such as Terrestrial Fiber and Cellular Wireless) to satisfy stringent latency Service Level Agreements (SLAs).

The `phase2_telemetry` module provides:
1. **Out-of-Band Path Telemetry (`telemetry_daemon.py`)**:
   - High-precision raw ICMP probing (`socket.SOCK_RAW, socket.IPPROTO_ICMP`) operating at $T_{\text{poll}} = 100$\,ms.
   - Dual-path simultaneous sampling via Linux source-policy routing:
     - **Link A (Fiber)**: Sourced from `10.0.1.1` $\to$ routed via Table 101 to `10.0.3.2`.
     - **Link B (Cellular)**: Sourced from `10.0.2.1` $\to$ routed via Table 102 to `10.0.3.2`.
   - Real-time computation of EWMA smoothed RTT ($SRTT$, $\alpha = 0.125$), FIFO sliding window moving average ($\mu_{\mathcal{W}}$, $N = 3$), and temporal violation counters ($c_{\text{raw}}$ and $c_{\text{win}}$).
2. **2x2 Policy Steering Engine (`steering_controller.py`)**:
   - Evaluates link quality across two dimensions: **Filtering Depth** (single sample vs. rolling window) and **Temporal Persistence** (single tick vs. hysteresis counter).
   - Executes atomic Linux Netlink default route replacements (`ip route replace default via ...`) to steer flows to the optimal backhaul link.

---

## 2. The 2x2 Decision Policy Taxonomy

Target SLA latency threshold is $\tau = 65.0$\,ms:

| Policy ID | Name | Mathematical Criterion | Operational Characteristic |
| :---: | :--- | :--- | :--- |
| **Policy 1** | **Strict Raw** | $\mathcal{C}_1(t) = \mathbb{I}(RTT(t) > \tau)$ | Memoryless single-sample evaluation. Fastest reaction ($100$\,ms), but vulnerable to wireless micro-bursts and route flapping. |
| **Policy 2** | **Raw + Hysteresis** | $\mathcal{C}_2(t) = \prod_{j=0}^{K-1} \mathbb{I}(RTT(t-j) > \tau)$ | Evaluates raw samples with temporal hysteresis ($K=2$). Rejects isolated micro-spikes without window lag. **Pareto-Optimal ($200$\,ms detection lag)**. |
| **Policy 3** | **Rolling Window Only** | $\mathcal{C}_3(t) = \mathbb{I}(\mu_{\mathcal{W}}(t) > \tau)$ | Evaluates arithmetic moving average over $N=3$ samples ($300$\,ms). Smooths moderate jitter but vulnerable to large outlier spikes. |
| **Policy 4** | **Window + Hysteresis** | $\mathcal{C}_4(t) = \prod_{m=0}^{K-1} \mathbb{I}(\mu_{\mathcal{W}}(t-m) > \tau)$ | Requires the rolling window mean to violate $\tau$ for $K=2$ consecutive ticks. Maximum protection, but highest detection lag ($400$\,ms). |

---

## 3. Usage & CLI Examples

### 3.1 Running Telemetry Daemon Standalone
Run continuous telemetry monitoring across both backhaul links:
```bash
# Monitor both links with live console updates
sudo python3 phase2_telemetry/telemetry_daemon.py

# Probe for 10 ticks and save to CSV
sudo python3 phase2_telemetry/telemetry_daemon.py --count 10 --log telemetry.csv
```

### 3.2 Running Steering Controller
Run the dynamic steering engine under a specific policy:
```bash
# Run Policy 2 (Raw + Hysteresis) for 20 seconds
sudo python3 phase2_telemetry/steering_controller.py --policy 2 --duration 20.0

# Run Policy 1 (Strict Raw) and halt immediately upon first route switch
sudo python3 phase2_telemetry/steering_controller.py --policy 1 --stop-on-trigger

# Run Policy 4 (Window + Hysteresis) and export complete CSV trace
sudo python3 phase2_telemetry/steering_controller.py --policy 4 --duration 20.0 --log trace_policy4.csv
```

### 3.3 Programmatic Python API
The controller can be integrated directly into experimental drivers:
```python
from phase2_telemetry import SteeringController, PolicyType

# Instantiate controller
controller = SteeringController(
    policy=PolicyType.RAW_HYSTERESIS,
    tau=65.0,
    window_size=3,
    persistence=2,
    interval=0.1,
)

# Run an 8.0-second session with live impairment injection callback
records = controller.run(
    duration=8.0,
    stop_on_trigger=False,
    tick_callback=lambda tick, rel_time, data: print(f"Tick {tick}: {data['rtt_sample']} ms"),
)

# Access summary metrics
summary = controller.get_summary()
print(f"Handovers: {summary['handover_count']}, SLA Violation: {summary['sla_violation_duration_ms']} ms")
```

---

## 4. Source Files

- [`telemetry_daemon.py`](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/phase2_telemetry/telemetry_daemon.py): Raw ICMP prober, EWMA smoothed RTT, sliding window buffer, and multi-path telemetry prober.
- [`steering_controller.py`](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/phase2_telemetry/steering_controller.py): 2x2 policy engine, atomic Netlink route actuator, and event trace recorder.
- [`__init__.py`](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/phase2_telemetry/__init__.py): Public package exports and initialization.
