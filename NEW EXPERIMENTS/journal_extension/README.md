# Future Journal Extension Repository

**Working Title:** *A Lightweight Kernel-Native Network Digital Twin for Transport Dynamics in Multi-Homed Subnet Handovers*  
**Target Venue:** IEEE Transactions on Network and Service Management (IEEE TNSM) / IEEE Transactions on Mobile Computing (TMC)  
**Status:** Complete Empirical Manuscript (1,520 Experimental Runs)

---

## Contents

- **`journal_draft.md`**: Complete, publication-length draft (598 lines) detailing:
  - Phase 1 Baseline Verification across 10 payload scales ($50\text{ MB} \to 500\text{ MB}$, 200 runs).
  - Parametric Impairment Sweeps across Latency ($10\text{--}160$\,ms), Packet Loss ($0.1\%\text{--}5\%$), and Delay Jitter ($\pm 2\text{--}\pm 20$\,ms) across 56 configurations (1,120 runs).
  - Head-to-Head Comparative Study: **TCP CUBIC vs. TCP Reno**.
  - The 5 Discovered Empirical Transport Laws:
    1. *Handover Invariance Law* ($\Delta T \approx 52\text{--}55$\,ms $O(1)$ scaling).
    2. *Hyperbolic Overhead Amortization* ($\rho(S) \propto 1/S$).
    3. *Pristine Link Algorithmic Parity* ($\Delta \le 0.03\%$).
    4. *High-BDP Latency Divergence* ($+48.6\%$ CUBIC speedup).
    5. *Loss-Regime Inversion / Reno's Revenge* (Reno finishes up to 3.8 minutes faster under channel loss).
  - Comprehensive statistical summaries (Tables 1–9) and visual plots (Figures 1–13).

---

## Relationship to the Conference Paper (`paper/`)

1. **Stage 1 (Conference Paper in `paper/`):**
   - Title: *Kernel-Native Emulation and Latency-Driven Dynamic Flow Steering for Heterogeneous 5G/6G Multi-Backhaul Networks*
   - Focus: 3-namespace aggregation gateway (`ns_client` $\to$ `ns_router` $\to$ `ns_server`), active $100$\,ms ICMP telemetry, $2 \times 2$ policy matrix, Hero Trace micro-bursts, and Monte Carlo fading evaluation.
   - Summarizes Phase 1 as calibration highlights.

2. **Stage 2 (Journal Extension here):**
   - After the conference paper is submitted, this draft will incorporate the Phase 2/3 dynamic flow steering engine and multi-objective MCDM optimization to form the full 12–15 page archival journal paper.
