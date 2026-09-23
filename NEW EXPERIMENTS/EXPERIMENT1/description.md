# Experiment 1: Baseline Control Evaluation (TCP CUBIC)

## 1. Overview & Objective

Experiment 1 establishes the baseline benchmark for file transfer performance under uninterrupted conditions versus mid-transfer IP migration (hard link failover across distinct subnets). This experiment focuses specifically on the **TCP CUBIC** congestion control algorithm, the default congestion control mechanism in Linux kernels.

The objective is to quantify the exact handover/migration overhead introduced when a client experiences an abrupt link interruption at 50% download progress and resumes the transfer over an alternate IP subnet, comparing it against a seamless, single-connection transfer.

---

## 2. Experimental Setup & Topology

- **Emulation Environment**: Dual isolated Linux network namespaces (`left-ns` as client, `right-ns` as server).
- **Subnet Architecture**:
  - **Path 1 (Subnet 1)**: `10.0.1.1/24` (Client) $\longleftrightarrow$ `10.0.1.2/24` (Server) on `veth-left1` / `veth-right1`
  - **Path 2 (Subnet 2)**: `10.0.2.1/24` (Client) $\longleftrightarrow$ `10.0.2.2/24` (Server) on `veth-left2` / `veth-right2`
- **Application Layer**: 
  - Server: Isolated Python FTP daemon (`pyftpdlib`) bound to `0.0.0.0:2121` inside `right-ns`.
  - Client: `lftp` inside `left-ns` in passive FTP mode, leveraging byte-range resume (`get -c`).
- **Network Impairment (Traffic Control)**:
  - Scenario **C0** (`pure_baseline_control`):
    - **Bandwidth**: 50 Mbit/s (enforced via HTB class rate limiter with `fq_codel` leaf queue)
    - **Latency**: 0 ms (no artificial delay added)
    - **Jitter**: 0 ms
    - **Packet Loss**: 0%

---

## 3. Congestion Control Algorithm (CCA)

- **Algorithm**: **TCP CUBIC** (`cwnd_mode: cubic`)
- **Characteristics**: CUBIC scales the congestion window as a cubic function of the elapsed time since the last congestion event, making window growth independent of RTT.
- **Cache Isolation**: 
  - TCP metrics caching disabled inside namespaces: `net.ipv4.tcp_no_metrics_save = 1`.
  - Kernel routing caches flushed between runs (`ip route flush cache`) to prevent state leakage between iterations.
  - Per-route congestion control enforced on virtual interfaces: `congctl cubic`.

---

## 4. Test Execution Protocol

For each target file size and iteration, two consecutive runs are conducted:

### Run 1: Realistic IP Migration Test (Subnet 1 $\rightarrow$ Subnet 2)
1. Subnet 1 links are brought **UP**; Subnet 2 links are held **DOWN**.
2. LFTP begins downloading the target payload from Server IP `10.0.1.2:2121`.
3. Download progress is actively monitored. When exactly **50%** of the payload is received:
   - The active LFTP process is interrupted (`kill`).
   - Hard failover is triggered: Subnet 1 interfaces (`veth-left1`, `veth-right1`) are immediately torn **DOWN**.
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

## 5. Parameter Matrix

| Parameter | Configuration |
| :--- | :--- |
| **Scenario** | C0 (`pure_baseline_control`) |
| **Congestion Control** | TCP CUBIC |
| **Throttling Rate** | 50 Mbit/s |
| **Latency / Jitter / Loss** | 0 ms / 0 ms / 0% |
| **File Sizes (MB)** | 50, 100, 150, 200, 250, 300, 350, 400, 450, 500 MB (10 sizes) |
| **Iterations per Size** | 10 iterations |
| **Cooldown Period** | 5 seconds between iterations |
| **Total Benchmark Pairs** | 100 runs (100 baseline + 100 migration = 200 transfers total) |

---

## 6. Output Artifacts & Telemetry

Results are written to `./results/`:

1. **Transfer Duration & Overhead Metrics**:
   - Filename: `pure_baseline_control_<size>MB.csv`
   - Fields: `timestamp`, `configured_rate`, `configured_latency`, `configured_jitter`, `configured_loss`, `cwnd_mode`, `file_size_mb`, `baseline_time_sec`, `migration_time_sec`, `overhead_sec`
2. **High-Resolution Kernel CWND Telemetry**:
   - Filename: `real_kernel_cwnd_pure_baseline_control_<size>MB.csv`
   - Polled every **20 ms (0.02s)** on the sender side (`right-ns`) via `ss -t -i -n`.
   - Fields: `timestamp`, `session_type` (`Migration` / `Baseline`), `cwnd_segments`

---

## 7. How to Run

From the `EXPERIMENT1` directory:

```bash
python3 ../scripts/batch_runner.py ./config.json
```