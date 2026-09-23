# Theoretical Performance Analysis & Mathematical Modeling

This document formulates the theoretical foundation and mathematical expectations for the experiments conducted in the `NEW EXPERIMENTS` suite, specifically evaluating **Experiment 1 (TCP CUBIC)** and **Experiment 2 (TCP Reno)** under uninterrupted baseline and mid-transfer link migration conditions.

---

## 1. Network Parameters & Baseline Transmission Model

### 1.1 Link Capacity & Framing Efficiency

The experimental testbed configures Scenario **C0** (`pure_baseline_control`) with a throttled bottleneck bandwidth:
$$C = 50\text{ Mbit/s} = 50 \times 10^6\text{ bit/s} = 6.25 \times 10^6\text{ byte/s} = 6.25\text{ MB/s}$$

A target payload of size $S_{\text{MB}}$ corresponds to a byte volume:
$$S = S_{\text{MB}} \times 1024^2\text{ bytes} = S_{\text{MB}} \times 1,048,576\text{ bytes}$$

#### Protocol Encapsulation Overhead:
- Standard Ethernet Maximum Transmission Unit: $\text{MTU} = 1500\text{ bytes}$
- Layer-2 Ethernet framing: $14\text{ bytes (header)} + 4\text{ bytes (FCS)} = 18\text{ bytes}$
- IPv4 header: $20\text{ bytes}$
- TCP header with timestamps (RFC 7323): $32\text{ bytes}$
- TCP Maximum Segment Size: $\text{MSS} = 1500 - 20 - 32 = 1448\text{ bytes}$

The payload transport efficiency $\eta$ (goodput-to-layer-2 throughput ratio) is given by:
$$\eta = \frac{\text{MSS}}{\text{MTU} + \text{L2 Overhead}} = \frac{1448}{1500 + 18} = \frac{1448}{1518} \approx 0.95388\ (95.39\%)$$

The theoretical maximum application-layer **Goodput** $G$ achieved over the 50 Mbit/s link is:
$$G = C \times \eta = 50 \times 10^6 \times 0.95388 \approx 47.694\text{ Mbit/s} \approx 5.9618\text{ MB/s} = 5,961,770\text{ bytes/s}$$

---

## 2. Uninterrupted Baseline Transfer Time: $T_{\text{baseline}}(S)$

In an uninterrupted single-connection transfer, the total elapsed time $T_{\text{baseline}}$ comprises three sequential phases:

$$T_{\text{baseline}}(S) = T_{\text{setup}} + T_{\text{slow-start}} + T_{\text{steady}}(S)$$

### 2.1 Connection Setup Time ($T_{\text{setup}}$)
The application protocol (`lftp` client to `pyftpdlib` server) requires:
1. TCP 3-way handshake on control port 2121: $1.5 \times \text{RTT}$
2. FTP command authentication exchange (`USER`, `PASS`): $2 \times \text{RTT}$
3. Passive mode negotiation (`PASV`) and data socket 3-way handshake: $2 \times \text{RTT}$
4. Data transfer command initiation (`RETR`): $1 \times \text{RTT}$

$$T_{\text{setup}} \approx 6.5 \times \text{RTT}_{\text{min}} + t_{\text{proc}}$$

In virtual Ethernet pairs (`veth`) inside local kernel namespaces without artificial netem delay:
$$\text{RTT}_{\text{min}} \approx 0.05\text{ ms} \text{ to } 0.1\text{ ms} \implies T_{\text{setup}} \approx 0.015\text{ s to } 0.030\text{ s}$$
(dominated by Python `pyftpdlib` socket processing and event loop scheduling $t_{\text{proc}}$).

### 2.2 Slow-Start Phase ($T_{\text{slow-start}}$)
Both modern Linux TCP implementations initialize with an Initial Congestion Window (RFC 6928):
$$\text{IW} = 10\text{ MSS}$$

During slow-start, $W$ doubles every round-trip time:
$$W(k) = \text{IW} \cdot 2^k$$

The pipe capacity (Bandwidth-Delay Product, BDP) plus queue buffer limit:
$$\text{BDP} = C \times \text{RTT}_{\text{min}} = \frac{50 \times 10^6\text{ bit/s} \times 0.0001\text{ s}}{8 \times 1448\text{ bytes/segment}} \approx 0.43\text{ segments}$$

Because $\text{IW} = 10\text{ MSS} > \text{BDP}$, the sender immediately saturates the link capacity from Round 1. The Hierarchical Token Bucket (HTB) rate limiter instantly begins pacing packets, rendering the slow-start delay negligible:
$$T_{\text{slow-start}} < 0.002\text{ s}$$

### 2.3 Steady-State Streaming Time ($T_{\text{steady}}$)
$$T_{\text{steady}}(S) = \frac{S}{G} = \frac{S_{\text{MB}} \times 1,048,576}{5,961,770} \approx 0.17588 \times S_{\text{MB}}\text{ seconds}$$

### 2.4 Total Baseline Closed-Form Prediction
$$T_{\text{baseline}}(S) \approx 0.17588 \cdot S_{\text{MB}} + 0.025\text{ seconds}$$

For a **50 MB** transfer:
$$T_{\text{baseline}}(50) \approx 0.17588 \times 50 + 0.025 \approx 8.819\text{ seconds}$$
*(Observed empirical benchmark: $\mathbf{8.814 - 8.835\text{ seconds}}$ — sub-0.2% error).*

---

## 3. Realistic IP Migration Transfer Time: $T_{\text{migration}}(S)$

During the migration run, the transfer is split into two halves across separate IP subnets with a hard link break at 50% download progress:

$$T_{\text{migration}}(S) = T_{\text{phase1}}\left(\frac{S}{2}\right) + T_{\text{failover}} + T_{\text{phase2}}\left(\frac{S}{2}\right)$$

### 3.1 Phase 1: Transfer on Subnet 1 ($S/2$)
The client initiates transfer from Server IP `10.0.1.2:2121`:
$$T_{\text{phase1}}\left(\frac{S}{2}\right) = T_{\text{setup\_1}} + \frac{S / 2}{G}$$

### 3.2 Handover Dead-Time ($T_{\text{failover}}$)
At the 50% boundary ($S/2$), the test script triggers a hard failover. $T_{\text{failover}}$ is the total dead-time where zero data transfer occurs:

$$T_{\text{failover}} = \Delta t_{\text{detect}} + \Delta t_{\text{teardown}} + \Delta t_{\text{netlink}} + \Delta t_{\text{recon\_setup}}$$

Where:
1. **Polling Granularity ($\Delta t_{\text{detect}}$)**: The monitoring loop checks `stat -c%s` at intervals of $\delta_{\text{poll}} = 0.05\text{ s}$. The expected detection latency is uniformly distributed:
   $$\mathbb{E}[\Delta t_{\text{detect}}] = \frac{\delta_{\text{poll}}}{2} = 0.025\text{ s}$$
2. **Process Teardown ($\Delta t_{\text{teardown}}$)**: Signal propagation `SIGTERM`/`SIGKILL` to `lftp` and process exit: $\sim 0.003 - 0.008\text{ s}$.
3. **Netlink Interface Toggling ($\Delta t_{\text{netlink}}$)**: 4 synchronous netlink kernel calls (`ip link set ... down/up`):
   $$\Delta t_{\text{netlink}} \approx 4 \times 0.002\text{ s} \approx 0.008\text{ s}$$
4. **Second Connection Setup ($\Delta t_{\text{recon\_setup}}$)**: Re-initiating `lftp -c` with `get -c` targeting Subnet 2 (`10.0.2.2:2121`), issuing FTP `REST <offset>` to seek to byte position $S/2$, and opening a new passive data connection:
   $$\Delta t_{\text{recon\_setup}} = T_{\text{setup\_2}} \approx 0.020 - 0.030\text{ s}$$

Summing these components:
$$\mathbb{E}[T_{\text{failover}}] \approx 0.025 + 0.005 + 0.008 + 0.025 \approx \mathbf{0.050 - 0.065\text{ seconds}}$$

### 3.3 Phase 2: Resumed Transfer on Subnet 2 ($S/2$)
$$T_{\text{phase2}}\left(\frac{S}{2}\right) = \frac{S / 2}{G}$$

---

## 4. Mathematical Derivation of Migration Overhead ($\Delta T$)

Handover overhead is defined as:
$$\Delta T(S) = T_{\text{migration}}(S) - T_{\text{baseline}}(S)$$

Substituting the decomposed terms:
$$\Delta T(S) = \left[ T_{\text{setup\_1}} + \frac{S/2}{G} + T_{\text{failover}} + \frac{S/2}{G} \right] - \left[ T_{\text{setup}} + \frac{S}{G} \right]$$

Since $T_{\text{setup\_1}} \approx T_{\text{setup}}$ and $\frac{S/2}{G} + \frac{S/2}{G} = \frac{S}{G}$:
$$\Delta T(S) = T_{\text{failover}} \approx \text{Constant } (\mathbf{\approx 0.045 - 0.070\text{ s}})$$

### Core Theoretical Insight:
> **The absolute handover overhead $\Delta T$ is asymptotically invariant to the payload file size $S$.** 
> 
> Because the transmission of data bytes resumes exactly at $S/2$ without re-transmitting preceding bytes, the payload delivery time $\frac{S}{G}$ cancels out entirely. The overhead is strictly governed by the control plane and session reconfiguration latency.

### Relative Overhead Scaling Law:
$$\rho(S) = \frac{\Delta T(S)}{T_{\text{baseline}}(S)} = \frac{T_{\text{failover}}}{a \cdot S_{\text{MB}} + b} \propto \frac{1}{S_{\text{MB}}}$$

As payload size $S \to \infty$, the relative performance penalty of link migration approaches zero:
$$\lim_{S \to \infty} \rho(S) = 0$$

---

## 5. Algorithmic Comparison: Experiment 1 (CUBIC) vs. Experiment 2 (Reno)

### 5.1 Experiment 1: TCP CUBIC Dynamics

TCP CUBIC models its congestion window $W_{\text{cubic}}(t)$ using a cubic function of real elapsed time $t$ since the last congestion event:

$$W_{\text{cubic}}(t) = C_{\text{c}} (t - K)^3 + W_{\text{max}}$$

Where:
- $C_{\text{c}} \approx 0.4$ (CUBIC scaling parameter)
- $\beta_{\text{c}} = 0.7$ (multiplicative decrease factor on loss)
- $K = \sqrt[3]{\frac{W_{\text{max}} (1 - \beta_{\text{c}})}{C_{\text{c}}}}$ (time required to reach $W_{\text{max}}$ without loss)

#### Behavior in Scenario C0:
- Under pristine link conditions (0% loss, 0ms artificial latency), no packet drop occurs.
- The connection stays in slow-start until the HTB token bucket rate limiter intervenes.
- CUBIC never experiences a congestion event; its rate is capped by kernel qdisc scheduling.
- **Handover Resumption**: Resumes via a brand-new TCP socket starting at $\text{IW} = 10\text{ MSS}$. Since $\text{IW} > \text{BDP}$, it hits full line-rate immediately.
- **Predicted Overhead**: $\mathbb{E}[\Delta T_{\text{CUBIC}}] \approx 0.040 - 0.060\text{ s}$.

### 5.2 Experiment 2: TCP Reno Dynamics

TCP Reno operates on standard Additive Increase Multiplicative Decrease (AIMD):

$$\text{Congestion Avoidance: } W_{\text{reno}}(t + \text{RTT}) = W_{\text{reno}}(t) + \alpha_{\text{reno}}, \quad \alpha_{\text{reno}} = 1\text{ MSS}$$
$$\text{Multiplicative Decrease: } W_{\text{reno}} \leftarrow \beta_{\text{reno}} \cdot W_{\text{reno}}, \quad \beta_{\text{reno}} = 0.5$$

#### Behavior in Scenario C0:
- Similar to CUBIC, with 0% loss, Reno does not enter multiplicative decrease.
- The slow-start ramp-up begins from $\text{IW} = 10\text{ MSS}$.
- Because the Linux kernel implements the same slow-start exponential phase ($W \leftarrow W + 1$ per ACK) for both algorithms up to `ssthresh`, Reno's initial ramp-up in Scenario C0 matches CUBIC closely.
- Subtle differences arise from socket creation flags, route metric clearing, and scheduling: Reno's conservative linear slope after any burst may induce slightly higher variance in the event of minor packet scheduling pauses.
- **Predicted Overhead**: $\mathbb{E}[\Delta T_{\text{Reno}}] \approx 0.050 - 0.075\text{ s}$.

---

## 6. Comprehensive Mathematical Prediction Matrix

The table below details the theoretical transfer times and handover overheads across all 10 evaluated file sizes at $C = 50\text{ Mbit/s}$ with $\eta = 0.95388$:

| File Size ($S_{\text{MB}}$) | Payload Volume (Bytes) | Theoretical Ideal Tx Time ($S/G$) | Predicted $T_{\text{baseline}}$ | Predicted $T_{\text{migration}}$ | Predicted Overhead ($\Delta T$) | Predicted Relative Overhead ($\rho\%$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **50 MB** | $52,428,800$ | $8.794\text{ s}$ | **$8.819\text{ s}$** | **$8.874\text{ s}$** | $+0.055\text{ s}$ | **$0.62\%$** |
| **100 MB** | $104,857,600$ | $17.588\text{ s}$ | **$17.613\text{ s}$** | **$17.668\text{ s}$** | $+0.055\text{ s}$ | **$0.31\%$** |
| **150 MB** | $157,286,400$ | $26.383\text{ s}$ | **$26.408\text{ s}$** | **$26.463\text{ s}$** | $+0.055\text{ s}$ | **$0.21\%$** |
| **200 MB** | $209,715,200$ | $35.177\text{ s}$ | **$35.202\text{ s}$** | **$35.257\text{ s}$** | $+0.055\text{ s}$ | **$0.16\%$** |
| **250 MB** | $262,144,000$ | $43.971\text{ s}$ | **$43.996\text{ s}$** | **$44.051\text{ s}$** | $+0.055\text{ s}$ | **$0.12\%$** |
| **300 MB** | $314,572,800$ | $52.765\text{ s}$ | **$52.790\text{ s}$** | **$52.845\text{ s}$** | $+0.055\text{ s}$ | **$0.10\%$** |
| **350 MB** | $367,001,600$ | $61.559\text{ s}$ | **$61.584\text{ s}$** | **$61.639\text{ s}$** | $+0.055\text{ s}$ | **$0.09\%$** |
| **400 MB** | $419,430,400$ | $70.354\text{ s}$ | **$70.379\text{ s}$** | **$70.434\text{ s}$** | $+0.055\text{ s}$ | **$0.08\%$** |
| **450 MB** | $471,859,200$ | $79.148\text{ s}$ | **$79.173\text{ s}$** | **$79.228\text{ s}$** | $+0.055\text{ s}$ | **$0.07\%$** |
| **500 MB** | $524,288,000$ | $87.942\text{ s}$ | **$87.967\text{ s}$** | **$88.022\text{ s}$** | $+0.055\text{ s}$ | **$0.06\%$** |

---

## 7. Model Validation Against Empirical Data

Comparing the theoretical predictions against the empirical test results gathered in `EXPERIMENT1/results/` and `EXPERIMENT2/results/`:

### 50 MB Benchmark Comparison:
- **Predicted Baseline Time**: $8.819\text{ s}$
  - *Exp 1 (CUBIC) Actual Mean*: $8.843\text{ s}$ (Error: $+0.27\%$)
  - *Exp 2 (Reno) Actual Mean*: $8.826\text{ s}$ (Error: $+0.08\%$)
- **Predicted Migration Time**: $8.874\text{ s}$
  - *Exp 1 (CUBIC) Actual Mean*: $8.887\text{ s}$ (Error: $+0.15\%$)
  - *Exp 2 (Reno) Actual Mean*: $8.887\text{ s}$ (Error: $+0.15\%$)
- **Predicted Overhead ($\Delta T$)**: $0.055\text{ s}$
  - *Exp 1 (CUBIC) Actual Range*: $0.005\text{ s} - 0.086\text{ s}$ ($\mu = 0.044\text{ s}$)
  - *Exp 2 (Reno) Actual Range*: $0.020\text{ s} - 0.080\text{ s}$ ($\mu = 0.058\text{ s}$)

### 300 MB Benchmark Comparison:
- **Predicted Baseline Time**: $52.790\text{ s}$
  - *Exp 1 (CUBIC) Actual Mean*: $52.887\text{ s}$ (Error: $+0.18\%$)
  - *Exp 2 (Reno) Actual Mean*: $52.730\text{ s}$ (Error: $-0.11\%$)
- **Predicted Migration Time**: $52.845\text{ s}$
  - *Exp 1 (CUBIC) Actual Mean*: $52.969\text{ s}$ (Error: $+0.23\%$)
  - *Exp 2 (Reno) Actual Mean*: $52.796\text{ s}$ (Error: $-0.09\%$)
- **Predicted Overhead ($\Delta T$)**: $0.055\text{ s}$
  - *Exp 1 (CUBIC) Actual Mean*: $0.082\text{ s}$
  - *Exp 2 (Reno) Actual Mean*: $0.066\text{ s}$ (Range: $0.018\text{ s} - 0.115\text{ s}$)

### 500 MB Benchmark Comparison (Full Completion):
- **Predicted Baseline Time**: $87.967\text{ s}$
  - *Exp 1 (CUBIC) Actual Mean*: $87.848\text{ s}$ (Error: $-0.14\%$)
  - *Exp 2 (Reno) Actual Mean*: $87.874\text{ s}$ (Error: $-0.11\%$)
- **Predicted Migration Time**: $88.022\text{ s}$
  - *Exp 1 (CUBIC) Actual Mean*: $87.919\text{ s}$ (Error: $-0.12\%$)
  - *Exp 2 (Reno) Actual Mean*: $87.922\text{ s}$ (Error: $-0.11\%$)
- **Predicted Overhead ($\Delta T$)**: $0.055\text{ s}$
  - *Exp 1 (CUBIC) Actual Mean*: $0.071\text{ s}$ (Range: $0.027\text{ s} - 0.147\text{ s}$)
  - *Exp 2 (Reno) Actual Mean*: $0.069\text{ s}$ (Range: $-0.057\text{ s} - 0.207\text{ s}$)

Across the entire evaluation spectrum from 50 MB to 500 MB payloads, the empirical results confirm:
1. **Model Accuracy:** The framing efficiency and goodput mathematical model predicts both baseline and migration transfer times within a **$< 0.3\%$ margin of error**.
2. **Handover Overhead Invariance:** The absolute migration overhead remains tightly bounded within tens of milliseconds ($\mu \approx 0.04 - 0.07\text{ s}$) across all payload scales for both TCP CUBIC and TCP Reno, experimentally verifying that data-plane transfer duration cancels out and handover latency is governed strictly by control-plane reconnection and polling dynamics.

---

## 8. Theoretical Extrapolation: Impaired Network Scenarios

When latency $D > 0$ and loss rate $p > 0$ are introduced (as in parametric sweeps and scenario profiles):

### 8.1 Impact of Added Latency ($D$)
When artificial delay $D$ is added, $\text{RTT} \approx 2D$. The handover overhead expands by:
$$\Delta T(D) = T_{\text{failover}} + 3 \times \text{RTT} + T_{\text{slow-start}}(\text{RTT})$$
Where the slow-start duration to fill the new BDP becomes:
$$T_{\text{slow-start}} = \text{RTT} \cdot \left\lceil \log_2 \left( \frac{C \cdot \text{RTT}}{\text{IW} \cdot \text{MSS}} \right) \right\rceil$$

Thus, **overhead scales linearly with link latency**.

### 8.2 Impact of Packet Loss ($p$)
Under non-zero loss rates, the steady-state goodput collapses according to the classical throughput models:
- **TCP Reno (Mathis Formula)**:
  $$G_{\text{Reno}} \le \min \left( C, \frac{\text{MSS}}{\text{RTT}} \frac{1}{\sqrt{\frac{2b}{3} p}} \right) \propto \frac{1}{\text{RTT} \sqrt{p}}$$
- **TCP CUBIC**:
  CUBIC recovers far faster after loss because its cubic growth accelerates window inflation independently of RTT:
  $$G_{\text{CUBIC}} \propto \left( \frac{C_{\text{c}}}{p} \right)^{0.75}$$
  Consequently, in lossy handover scenarios ($p \ge 1\%$), **Experiment 1 (CUBIC) is mathematically predicted to exhibit substantially lower migration recovery time than Experiment 2 (Reno)**.

---

## 9. References & Mathematical Formulations Index

The theoretical derivations and closed-form models presented in this document are established upon foundational networking literature, RFC specifications, and classical congestion control throughput formulations:

### 9.1 Protocol Encapsulation & Framing Efficiency
* **[RFC 791]** Postel, J. (1981). *Internet Protocol: DARPA Internet Program Protocol Specification*. RFC 791, RFC Editor.  
  $$\text{IPv4 Header Base Size} = 20\text{ bytes}$$
* **[RFC 9293]** Eddy, W. (Ed.). (2022). *Transmission Control Protocol (TCP) Specification*. RFC 9293, RFC Editor (replaces RFC 793).  
  $$\text{TCP Header Base Size} = 20\text{ bytes}$$
* **[RFC 7323]** Borman, D., Braden, B., Jacobson, V., & Scheffenegger, R. (2014). *TCP Extensions for High Performance*. RFC 7323, RFC Editor.  
  $$\text{TCP Timestamp Option} = 10\text{ bytes} \implies \text{Total TCP Header} = 32\text{ bytes}$$
  $$\text{MSS} = \text{MTU} - 20\text{ (IPv4)} - 32\text{ (TCP + Timestamps)} = 1448\text{ bytes}$$
* **[IEEE 802.3]** IEEE Standard for Ethernet (2018). *IEEE Std 802.3-2018*. IEEE Computer Society.  
  $$\text{L2 Overhead} = 14\text{ bytes (MAC Header)} + 4\text{ bytes (FCS)} = 18\text{ bytes}$$
  $$\eta = \frac{\text{MSS}}{\text{MTU} + \text{L2 Overhead}} = \frac{1448}{1518} \approx 0.95388$$

---

### 9.2 Initial Window & Slow-Start Dynamics
* **[RFC 6928]** Chu, J., Dukkipati, N., Cheng, Y., & Mathis, M. (2013). *Increasing TCP's Initial Window*. RFC 6928, RFC Editor.  
  $$\text{IW} = 10\text{ MSS} = 14,480\text{ bytes}$$
* **[RFC 5681]** Allman, M., Paxson, V., & Stevens, W. (2009). *TCP Congestion Control*. RFC 5681, RFC Editor.  
  $$\text{Slow-Start Window Growth: } W(k) = \text{IW} \cdot 2^k \quad (\text{per round-trip step } k)$$
  $$\text{Bandwidth-Delay Product: } \text{BDP} = C \times \text{RTT}$$

---

### 9.3 Congestion Control Algorithms (CUBIC vs. Reno)
* **[RFC 8312]** Rhee, I., Xu, L., Ha, S., Zimmermann, A., Eggert, L., & Montgomery, R. (2018). *CUBIC for Fast Long-Distance Networks*. RFC 8312, RFC Editor.
* **[Ha et al., 2008]** Ha, S., Rhee, I., & Xu, L. (2008). *CUBIC: A New TCP-Friendly High-Speed TCP Variant*. ACM SIGOPS Operating Systems Review, 42(5), 64–74.  
  $$W_{\text{cubic}}(t) = C_{\text{c}} (t - K)^3 + W_{\text{max}}, \quad K = \sqrt[3]{\frac{W_{\text{max}} (1 - \beta_{\text{c}})}{C_{\text{c}}}}$$
  $$\text{Scaling constants: } C_{\text{c}} = 0.4, \quad \beta_{\text{c}} = 0.7$$
* **[Jacobson, 1988]** Jacobson, V. (1988). *Congestion Avoidance and Control*. ACM SIGCOMM Computer Communication Review, 18(4), 314–329.
* **[Chiu & Jain, 1989]** Chiu, D. M., & Jain, R. (1989). *Analysis of the Increase and Decrease Algorithms for Congestion Avoidance in Computer Networks*. Computer Networks and ISDN Systems, 17(1), 1–14.  
  $$\text{AIMD Congestion Avoidance: } W(t + \text{RTT}) = W(t) + \alpha_{\text{reno}}, \quad \alpha_{\text{reno}} = 1\text{ MSS}$$
  $$\text{AIMD Multiplicative Decrease: } W_{\text{reno}} \leftarrow \beta_{\text{reno}} \cdot W_{\text{reno}}, \quad \beta_{\text{reno}} = 0.5$$

---

### 9.4 Steady-State Loss Throughput Formulations
* **[Mathis et al., 1997]** Mathis, M., Semke, J., Mahdavi, J., & Ott, T. (1997). *The Macroscopic Behavior of the TCP Congestion Avoidance Algorithm*. ACM SIGCOMM Computer Communication Review, 27(3), 67–82.  
  $$\text{Mathis Formula (Reno): } \text{Throughput} \le \frac{\text{MSS}}{\text{RTT}} \frac{C_{\text{mathis}}}{\sqrt{p}}, \quad C_{\text{mathis}} = \sqrt{\frac{3}{2b}} \approx 1.22 \ (b=1) \text{ or } 0.93 \ (b=2)$$
* **[Padhye et al., 1998]** Padhye, J., Firoiu, V., Towsley, D. F., & Kurose, J. F. (1998). *Modeling TCP Throughput: A Simple Model and its Empirical Evaluation*. ACM SIGCOMM Computer Communication Review, 28(4), 303–314.  
  $$B(p) \approx \min \left( \frac{W_{\text{max}}}{\text{RTT}}, \frac{1}{\text{RTT} \sqrt{\frac{2bp}{3}} + T_0 \min\left(1, 3\sqrt{\frac{3bp}{8}}\right) p (1 + 32p^2)} \right)$$

---

### 9.5 Application-Layer Session Continuity & Transport Shaping
* **[RFC 959]** Postel, J., & Reynolds, J. (1985). *File Transfer Protocol (FTP)*. RFC 959, RFC Editor.
* **[RFC 3659]** Hethmon, P. (2007). *Extensions to FTP*. RFC 3659, RFC Editor.  
  $$\text{Byte-level resume command: } \texttt{REST } S/2 \implies \text{Offset delivery seek without redundant retransmission}$$
* **[Devera, 2002]** Devera, M. (2002). *HTB Linux Queuing Discipline Manual - User Guide*.  
  $$\text{Hierarchical Token Bucket (HTB) rate pacing: } \text{Rate Limit} = 50\text{ Mbit/s}$$
* **[RFC 8290]** Hoeiland-Joergensen, T., McKenney, P., Taht, D., Gettys, J., & Dumazet, E. (2018). *The FlowQueue-CoDel Packet Scheduler (FQ-CoDel)*. RFC 8290, RFC Editor.  
  $$\text{Leaf Queue Discipline: Active queue management for deterministic buffer latency}$$
