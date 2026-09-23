# Baseline Analysis Results (Scenario C0)
## TCP CUBIC vs. TCP Reno Handover Evaluation

This directory contains the standardized statistical results, comparative tables, and overall metrics for **Experiment 1 (TCP CUBIC)** and **Experiment 2 (TCP Reno)** across 10 payload scales (50MB to 500MB).

For the full detailed benchmark report, see [BASELINE_EXPERIMENTS_REPORT.md](../../BASELINE_EXPERIMENTS_REPORT.md).

---

## Artifact Index:

### CSV Statistical Tables:
1. [table1_cubic_statistical_summary.csv](table1_cubic_statistical_summary.csv): Detailed statistical profile for TCP CUBIC across all 10 payload sizes (Mean, Std, Median, Variance, Range, 95% Confidence Interval, Relative Overhead).
2. [table2_reno_statistical_summary.csv](table2_reno_statistical_summary.csv): Detailed statistical profile for TCP Reno across all 10 payload sizes.
3. [table3_cubic_vs_reno_comparison.csv](table3_cubic_vs_reno_comparison.csv): Side-by-side comparative table matching terminal analysis output (CUBIC vs. Reno Baseline, Migration, and Overhead deltas).
4. [table4_overall_protocol_metrics.csv](table4_overall_protocol_metrics.csv): High-level benchmark summary across the entire suite (overall mean overheads, variance, relative decay, and scientific conclusions).
5. [full_statistical_profile_cubic_vs_reno.csv](full_statistical_profile_cubic_vs_reno.csv): Comprehensive 24-dimension consolidated dataset for LaTeX/plotting pipelines.

### Associated Plots (in `../../plots/`):
- [Figure 1: Total Completion Time Comparison](../../plots/cubic_vs_reno_total_time.png)
- [Figure 2: Absolute Handover Overhead Bar Chart](../../plots/cubic_vs_reno_overhead.png)
- [Figure 3: Handover Overhead Line Trajectory](../../plots/cubic_vs_reno_handover_line.png)
- [Figure 4: Relative Overhead Decay Curve](../../plots/cubic_vs_reno_relative_decay.png)
- [Figure 5: Statistical Dispersion Boxplots](../../plots/cubic_vs_reno_boxplots.png)

---

## Executive Summary of Results:
- **Baseline Parity**: Under pristine conditions (0% loss, 0ms delay), CUBIC and Reno have virtually identical completion times ($\Delta \le 0.03\%$).
- **Overhead Invariance**: Handover overhead remains flat between $43\text{ ms}$ and $71\text{ ms}$ across all payload sizes (Overall Mean: **$52.24\text{ ms}$** for CUBIC vs. **$54.67\text{ ms}$** for Reno, Net Delta: **$+2.43\text{ ms}$**, statistically insignificant).
- **Amortization**: Relative overhead drops from $0.48\% - 0.66\%$ at 50MB down to $0.08\%$ at 500MB ($10\times$ reduction).
