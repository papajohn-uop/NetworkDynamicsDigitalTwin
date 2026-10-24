# Emulation Testbed Scripts & Topology Guide

This directory contains the orchestration, driver, and configuration scripts for the kernel-native 5G/6G multi-backhaul emulation testbed.

---

## 1. Primary Topology Script: `setup_phase2_topology.sh`

[`setup_phase2_topology.sh`](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/scripts/setup_phase2_topology.sh) provisions, configures, and tests the 3-namespace multi-backhaul emulation environment required for Phase 2 (Active Telemetry & Flow Steering) and Phase 3 (Hero Trace & Monte Carlo Robustness Benchmarking).

### Topology Architecture

```
+---------------------------------------------------------------------------------------+
|                                    HOST LINUX KERNEL                                  |
|                                                                                       |
|  +-------------------------+                           +---------------------------+  |
|  |   CLIENT NAMESPACE      |                           |     ROUTER NAMESPACE      |  |
|  |      (`ns_client`)      |                           |       (`ns_router`)       |  |
|  |                         |                           |                           |  |
|  |   +------------------+  |     Link A (10.0.1.0/24)  |   +------------------+    |  |
|  |   | `veth_client_a`  |==|===========================|==| `veth_router_a`  |    |  |
|  |   |   10.0.1.1/24    |  |   (Fiber: 100M, ~4ms RTT) |   |   10.0.1.2/24    |    |  |
|  |   +------------------+  |                           |   +------------------+    |  |
|  |                         |                           |         │ (tc shaping)    |  |
|  |   +------------------+  |     Link B (10.0.2.0/24)  |   +------------------+    |  |
|  |   | `veth_client_b`  |==|===========================|==| `veth_router_b`  |    |  |
|  |   |   10.0.2.1/24    |  | (Cellular: 50M, ~50ms RTT)|   |   10.0.2.2/24    |    |  |
|  |   +------------------+  |                           |   +------------------+    |  |
|  |                         |                           |         │ (IP Forwarding) |  |
|  |   Policy Routing:       |                           |   +------------------+    |  |
|  |   - Table 101 -> Link A |                           |   |  `veth_r_sink`   |    |  |
|  |   - Table 102 -> Link B |                           |   |   10.0.3.1/24    |    |  |
|  |   - Default   -> Link B |                           |   +------------------+    |  |
|  +-------------------------+                           +-------------║-------------+  |
|                                                                      ║                |
|                                                Sink Link             ║ (10.0.3.0/24)  |
|                                                (Pristine Gigabit)    ║                |
|                                                        +-------------║-------------+  |
|                                                        |     SERVER NAMESPACE      |  |
|                                                        |       (`ns_server`)       |  |
|                                                        |                           |  |
|                                                        |   +------------------+    |  |
|                                                        |   |  `veth_server`   |    |  |
|                                                        |   |   10.0.3.2/24    |    |  |
|                                                        |   +------------------+    |  |
|                                                        |                           |  |
|                                                        |   Invariant Target IP:    |  |
|                                                        |        10.0.3.2           |  |
|                                                        +---------------------------+  |
+---------------------------------------------------------------------------------------+
```

---

## 2. Key Technical Mechanisms

1. **Destination IP Invariance (`10.0.3.2`)**:  
   In operational multi-access edge networks, a mobile node switches backhaul paths without requiring the remote cloud server to change its IP address. Placing the server in a separate subnet (`10.0.3.0/24`) behind `ns_router` allows `ns_client` to switch routes transparently to the same invariant destination IP (`10.0.3.2`).
2. **Dual-Path Out-of-Band Telemetry via Linux Policy Routing**:  
   To measure path latencies concurrently across both Link A and Link B without confounding application default routes, `ns_client` uses Linux source-policy routing:
   - Packets sourced from `10.0.1.1` consult **Table 101** $\to$ routed exclusively via `veth_client_a` (Link A).
   - Packets sourced from `10.0.2.1` consult **Table 102** $\to$ routed exclusively via `veth_client_b` (Link B).
   - Untagged application traffic uses the **main routing table**, which initially defaults to Link B and is dynamically switched to Link A by the steering controller.
3. **Traffic Control (`tc`) Shaping**:  
   Channel constraints and impairments are enforced on the gateway interfaces inside `ns_router`:
   - **Link A (Fiber)**: HTB 100 Mbit/s, netem 2 ms one-way delay (yielding ~4 ms RTT), fq_codel leaf.
   - **Link B (Cellular)**: HTB 50 Mbit/s, netem 25 ms one-way delay (yielding ~50 ms RTT), fq_codel leaf.
4. **Kernel Cache Hardening**:  
   `sysctl -w net.ipv4.tcp_no_metrics_save=1` is applied across all namespaces to prevent Linux from caching historical smoothed RTT and CWND values across connections.
5. **Interface Name Length (`IFNAMSIZ = 15`)**:  
   Linux Netlink limits network interface names to 15 characters (plus null byte). All interfaces use standardized short names (e.g., `veth_r_sink`, `veth_server`, `veth_client_a`).

---

## 3. CLI Usage & Commands

The script must be run with `sudo` privileges:

```bash
sudo ./scripts/setup_phase2_topology.sh [COMMAND] [ARGUMENTS...]
```

### Available Commands:

| Command | Syntax | Description |
| :--- | :--- | :--- |
| **`setup`** *(Default)* | `sudo ./scripts/setup_phase2_topology.sh setup` | Destroys lingering namespaces, provisions `ns_client`, `ns_router`, `ns_server`, configures policy routing, applies baseline TC shaping, and executes a connectivity self-test. |
| **`teardown`** | `sudo ./scripts/setup_phase2_topology.sh teardown` | Deletes all namespaces and destroys attached virtual ethernet pairs. |
| **`status`** | `sudo ./scripts/setup_phase2_topology.sh status` | Inspects and displays all namespaces, IP assignments, default routes, policy rules, and active TC qdiscs. |
| **`test`** | `sudo ./scripts/setup_phase2_topology.sh test` | Pings `10.0.3.2` over Link A, Link B, and default route to verify latency targets. |
| **`set-impairment`** | `sudo ./scripts/setup_phase2_topology.sh set-impairment <link> <delay> [jitter] [loss] [rate]` | Dynamically updates the channel conditions on Link A or Link B in real time. |

---

## 4. Operational Examples

### Example 1: Full Testbed Setup & Verification
```bash
sudo ./scripts/setup_phase2_topology.sh setup
```
*Expected Output:*
```text
[CLEANUP] Tearing down existing namespaces and virtual links...
[SETUP] Provisioning 3-Namespace Multi-Backhaul Architecture...
[SETUP] Enabling IP Forwarding in ns_router...
[SETUP] Hardening kernel route caches (tcp_no_metrics_save=1)...
[SETUP] Setting up return routing in ns_server...
[SETUP] Configuring Linux Policy Routing in ns_client...
[SETUP] Applying Traffic Control (tc) profiles on ns_router and ns_client...
[SUCCESS] Topology successfully initialized and configured!

[TEST] Testing Dual-Path Connectivity to ns_server (10.0.3.2)...
1. Link A Probe (Sourced from 10.0.1.1 -> 10.0.3.2): [OK] SUCCESS (Avg RTT = 4.21 ms - Expected ~4 ms)
2. Link B Probe (Sourced from 10.0.2.1 -> 10.0.3.2): [OK] SUCCESS (Avg RTT = 50.32 ms - Expected ~50 ms)
3. Default Route Egress (10.0.3.2): [OK] SUCCESS (Avg RTT = 50.30 ms)
```

### Example 2: Probing Both Paths Manually
```bash
# Probe Link A (Fiber path)
sudo ip netns exec ns_client ping -c 3 -I 10.0.1.1 10.0.3.2

# Probe Link B (Cellular path)
sudo ip netns exec ns_client ping -c 3 -I 10.0.2.1 10.0.3.2
```

### Example 3: Simulating the Hero Trace Dynamic Events
```bash
# 1. Inject transient spike on Link B (delay 44ms -> RTT jumps to ~88ms):
sudo ./scripts/setup_phase2_topology.sh set-impairment B 44ms

# Verify latency jump:
sudo ip netns exec ns_client ping -c 2 -I 10.0.2.1 10.0.3.2
# Output: RTT = 88.3 ms

# 2. Revert back to baseline cellular delay (25ms -> RTT ~50ms):
sudo ./scripts/setup_phase2_topology.sh set-impairment B 25ms

# 3. Inject persistent structural degradation (delay 47.5ms -> RTT jumps to ~95ms, violating SLA):
sudo ./scripts/setup_phase2_topology.sh set-impairment B 47.5ms
```

### Example 4: Executing an Atomic Default Route Switch
```bash
# Switch active default route to Link A (Fiber):
sudo ip -n ns_client route replace default via 10.0.1.2 dev veth_client_a

# Switch active default route back to Link B (Cellular):
sudo ip -n ns_client route replace default via 10.0.2.2 dev veth_client_b
```

---

## 5. Other Scripts in this Directory

- **`lftp-migration-test.sh`**: The Phase 1 platform verification harness. Uses a 2-namespace setup (`left-ns` $\longleftrightarrow$ `right-ns`) to measure `lftp` mid-transfer session re-anchoring across 1,520 runs (archived in [`journal_extension/`](file:///home/ubuntu/papajohn/AMAZING_6G/PAPER/NEW_APPROACH/paper_repo/NEW%20EXPERIMENTS/journal_extension/)).
- **`batch_runner.py`**: Automated batch runner for executing repeated iterations of `lftp-migration-test.sh`.
- **`cwnd_logger.sh`**: Polling utility that samples `ss -tin` socket metrics at high frequency to record kernel CWND adaptations.
- **`config.json`**: JSON parameter definitions for sweep matrices.
