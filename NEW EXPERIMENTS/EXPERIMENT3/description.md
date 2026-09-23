# Experiment 3: Parametric Sweeps under Impairments (TCP CUBIC)

## 1. Overview & Objective

Experiment 3 transitions beyond the idealized baseline scenario (C0) to systematically evaluate file transfer performance and handover dynamics under controlled network impairments. Using **TCP CUBIC** as the transport-layer congestion control algorithm, this experiment isolates three fundamental network degradation dimensions:

1. **Network Latency Sweep**: Quantifying the impact of round-trip propagation delay on session resumption, TCP 3-way handshake overhead, and slow-start BDP filling.
2. **Packet Loss Sweep**: Analyzing the degradation of steady-state throughput and post-handover recovery latency when packets are randomly dropped.
3. **Latency Jitter Sweep**: Evaluating transport stability under packet delay variation around a nominal 40ms baseline.

The core objective is to determine how handover overhead ($\Delta T$) and total migration completion time scale when the underlying transmission medium deviates from pristine conditions.

---

## 2. Experimental Setup & Topology

- **Emulation Environment**: Dual isolated Linux network namespaces (`left-ns` as client, `right-ns` as server).
- **Subnet Architecture**:
  - **Path 1 (Subnet 1)**: `10.0.1.1/24` (Client) $\longleftrightarrow$ `10.0.1.2/24` (Server) on `veth-left1` / `veth-right1`
  - **Path 2 (Subnet 2)**: `10.0.2.1/24` (Client) $\longleftrightarrow$ `10.0.2.2/24` (Server) on `veth-left2` / `veth-right2`
- **Application Layer**: 
  - Server: Isolated Python FTP daemon (`pyftpdlib`) bound to `0.0.0.0:2121` inside `right-ns`.
  - Client: `lftp` inside `left-ns` in passive FTP mode, leveraging byte-range resume (`get -c`).
- **Traffic Control Architecture (`tc`)**:
  - When network impairments (delay, jitter, or loss) are configured, a hierarchical qdisc structure is deployed:
    1. **Root Qdisc (`netem`)**: Injects artificial propagation delay, statistical jitter, and random packet loss.
    2. **Inner Class (`htb`)**: Throttles link capacity to **50 Mbit/s** (`ceil 50mbit quantum 1500`).
    3. **Leaf Qdisc (`fq_codel`)**: Manages fair queueing and active buffer management.

---

## 3. Congestion Control Algorithm (CCA)

- **Algorithm**: **TCP CUBIC** (`cwnd_mode: cubic`)
- **Characteristics**: CUBIC models window growth via a cubic curve centered at elapsed time $t = K$, decoupling window expansion from round-trip time (RTT). This experiment explores CUBIC's ability to recover after link migration when operating over high-BDP and lossy channels.
- **Cache Isolation**: 
  - TCP metrics caching disabled inside namespaces: `net.ipv4.tcp_no_metrics_save = 1`.
  - Kernel routing caches flushed between runs (`ip route flush cache`) to prevent state leakage between iterations.
  - Per-route congestion control enforced on virtual interfaces: `congctl cubic`.

---

## 4. Parametric Sweep Matrix & Configurations

The experiment evaluates **14 distinct impairment configurations** across 3 sweep strategies at a constant bottleneck rate of **50 Mbit/s**, evaluated across two payload file sizes (**100 MB** and **200 MB**):

### 4.1 Latency Sweep (5 Configurations)
Evaluates scaling behavior across round-trip times ($\text{RTT} \approx 2 \times \text{Latency}$):
- **Fixed Parameters**: Rate = 50 Mbit/s, Jitter = 0ms, Loss = 0%
- **Latency Values**: `10ms`, `20ms`, `40ms`, `80ms`, `160ms`
- **Theoretical Hypothesis**: Handover overhead scales linearly with round-trip latency ($\Delta T \propto \text{RTT}$) due to the TCP 3-way handshake, FTP control negotiation round-trips, and slow-start BDP inflation:
  $$\Delta T(\text{RTT}) \approx T_{\text{failover}} + 3 \times \text{RTT} + \text{RTT} \cdot \left\lceil \log_2 \left(\frac{C \cdot \text{RTT}}{\text{IW} \cdot \text{MSS}}\right) \right\rceil$$

### 4.2 Packet Loss Sweep (5 Configurations)
Evaluates transport robustness against non-congestive channel packet drops:
- **Fixed Parameters**: Rate = 50 Mbit/s, Latency = 20ms ($\text{RTT} \approx 40\text{ms}$), Jitter = 0ms
- **Loss Values**: `0.1%`, `0.5%`, `1%`, `2%`, `5%`
- **Theoretical Hypothesis**: In accordance with CUBIC's loss model ($G \propto (C_c / p)^{0.75}$), steady-state goodput will drop as loss increases, and session resumption after link migration will suffer increased recovery latency due to packet losses during slow-start.

### 4.3 Jitter Sweep (4 Configurations)
Evaluates transport stability under packet arrival dispersion:
- **Fixed Parameters**: Rate = 50 Mbit/s, Latency = 40ms ($\text{RTT} \approx 80\text{ms}$), Loss = 0%
- **Jitter Values**: `2ms`, `5ms`, `10ms`, `20ms`
- **Theoretical Hypothesis**: Jitter introduces packet reordering and variance in RTT estimation, widening RTO bounds and modulating burst pacing during initial window growth.

---

### Complete Configuration Reference Table

| # | Sweep Strategy | Rate | Latency | Jitter | Loss | File Sizes | Output CSV Base Name |
| :-: | :--- | :-: | :-: | :-: | :-: | :-: | :--- |
| 1 | **Latency** | 50 Mbit/s | **10ms** | 0ms | 0% | 100 MB, 200 MB | `sweep_latency_sweep_10ms_0ms_0` |
| 2 | **Latency** | 50 Mbit/s | **20ms** | 0ms | 0% | 100 MB, 200 MB | `sweep_latency_sweep_20ms_0ms_0` |
| 3 | **Latency** | 50 Mbit/s | **40ms** | 0ms | 0% | 100 MB, 200 MB | `sweep_latency_sweep_40ms_0ms_0` |
| 4 | **Latency** | 50 Mbit/s | **80ms** | 0ms | 0% | 100 MB, 200 MB | `sweep_latency_sweep_80ms_0ms_0` |
| 5 | **Latency** | 50 Mbit/s | **160ms** | 0ms | 0% | 100 MB, 200 MB | `sweep_latency_sweep_160ms_0ms_0` |
| 6 | **Loss** | 50 Mbit/s | 20ms | 0ms | **0.1%** | 100 MB, 200 MB | `sweep_loss_sweep_20ms_0ms_01` |
| 7 | **Loss** | 50 Mbit/s | 20ms | 0ms | **0.5%** | 100 MB, 200 MB | `sweep_loss_sweep_20ms_0ms_05` |
| 8 | **Loss** | 50 Mbit/s | 20ms | 0ms | **1%** | 100 MB, 200 MB | `sweep_loss_sweep_20ms_0ms_1` |
| 9 | **Loss** | 50 Mbit/s | 20ms | 0ms | **2%** | 100 MB, 200 MB | `sweep_loss_sweep_20ms_0ms_2` |
| 10 | **Loss** | 50 Mbit/s | 20ms | 0ms | **5%** | 100 MB, 200 MB | `sweep_loss_sweep_20ms_0ms_5` |
| 11 | **Jitter** | 50 Mbit/s | 40ms | **2ms** | 0% | 100 MB, 200 MB | `sweep_jitter_sweep_40ms_2ms_0` |
| 12 | **Jitter** | 50 Mbit/s | 40ms | **5ms** | 0% | 100 MB, 200 MB | `sweep_jitter_sweep_40ms_5ms_0` |
| 13 | **Jitter** | 50 Mbit/s | 40ms | **10ms** | 0% | 100 MB, 200 MB | `sweep_jitter_sweep_40ms_10ms_0` |
| 14 | **Jitter** | 50 Mbit/s | 40ms | **20ms** | 0% | 100 MB, 200 MB | `sweep_jitter_sweep_40ms_20ms_0` |

---

## 5. Execution Volume & Runtime Estimates

- **Total Configurations**: 14 impairment profiles
- **File Sizes**: 2 targets (100 MB and 200 MB)
- **Iterations per Target**: 10 repetitions
- **Cooldown Interval**: 5 seconds between iterations
- **Total Benchmark Pairs**: $14 \times 2 \times 10 = \mathbf{280\text{ runs}}$ (560 individual file transfers)

| Target File Size | Single Run Time (Approx.) | Iterations | Subtotal Estimated Time |
| :---: | :---: | :---: | :---: |
| **100 MB** | $\sim 17.6\text{s (Baseline)} + 17.7\text{s (Migrate)} + 5\text{s (Cooldown)} \approx 40\text{s}$ | 140 iterations | $\sim 1.55\text{ hours}$ |
| **200 MB** | $\sim 35.2\text{s (Baseline)} + 35.3\text{s (Migrate)} + 5\text{s (Cooldown)} \approx 75.5\text{s}$ | 140 iterations | $\sim 2.93\text{ hours}$ |
| **Total Experiment 3 Runtime** | | **280 iterations** | **$\sim 4.5\text{ hours}$** |

---

## 6. Test Execution Protocol

For each configuration and iteration, two consecutive runs are conducted:

### Run 1: Realistic IP Migration Test (Subnet 1 $\rightarrow$ Subnet 2)
1. Subnet 1 links are brought **UP**; Subnet 2 links are held **DOWN**.
2. LFTP begins downloading the target payload from Server IP `10.0.1.2:2121`.
3. Download progress is actively monitored. When exactly **50%** of the payload is received:
   - The active LFTP process is interrupted (`kill`).
   - Hard failover is triggered: Subnet 1 interfaces (`veth-left1`, `veth-right1`) are torn **DOWN**.
   - Subnet 2 interfaces (`veth-left2`, `veth-right2`) are brought **UP**.
4. LFTP resumes the transfer targeting Subnet 2 Server IP `10.0.2.2:2121` using the continuation flag (`get -c`).
5. Total migration elapsed time ($T_{\text{migration}}$) is recorded upon completion.

### Run 2: Uninterrupted Baseline Test (Subnet 1)
1. Subnet 1 links are brought **UP**; Subnet 2 links remain **DOWN**.
2. LFTP executes a full, single-session uninterrupted download from Server IP `10.0.1.2:2121`.
3. Total baseline elapsed time ($T_{\text{baseline}}$) is recorded upon completion.

### Overhead Computation
$$\text{Handover Overhead} = T_{\text{migration}} - T_{\text{baseline}}$$

---

## 7. Output Artifacts & Telemetry

Results are recorded in `./results/`:

1. **Transfer Duration & Overhead Metrics**:
   - Filenames: `sweep_<sweep_name>_<lat>_<jit>_<loss>_<size>MB.csv`
   - Header Columns:  
     `timestamp,configured_rate,configured_latency,configured_jitter,configured_loss,cwnd_mode,file_size_mb,baseline_time_sec,migration_time_sec,overhead_sec`
2. **High-Resolution Kernel CWND Telemetry**:
   - Filenames: `real_kernel_cwnd_sweep_<sweep_name>_<lat>_<jit>_<loss>_<size>MB.csv`
   - Polled every **20 ms (0.02s)** on the sender side (`right-ns`) via `ss -t -i -n`.
   - Header Columns:  
     `timestamp,session_type,cwnd_segments`

---

## 8. How to Run

From the `EXPERIMENT3` directory:

```bash
python3 ../scripts/batch_runner.py ./config.json
```

To run with CLI overrides (e.g. running 1 iteration for a quick smoke test):

```bash
python3 ../scripts/batch_runner.py ./config.json 1 2 "" 100 cubic
```
*(Positional CLI Arguments: `<config_file>` `[iterations]` `[cooldown]` `[results_dir]` `[filesize]` `[cwnd_mode]`)*