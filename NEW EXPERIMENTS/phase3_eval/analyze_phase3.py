#!/usr/bin/env python3
"""
phase3_eval/analyze_phase3.py

Publication-Ready Statistical Aggregator & Figure Generator for Phase 3 (20.0s Timeline):
  1. plots/hero_trace_comparative.png & .pdf (Figure 3 in Conference Paper)
     - 4-panel synchronized comparative latency trace (Transient Spike & Structural Step)
  2. plots/monte_carlo_pareto.png & .pdf
     - Detection Lag vs. False Handover Ratio Pareto Frontier
  3. plots/monte_carlo_boxplots.png & .pdf
     - Flapping Frequency & SLA Violation Detection Lag Boxplots
  4. Generates LaTeX / Markdown empirical tables (Table V & Table VI)
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Paths configuration
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CUR_DIR)
RESULTS_DIR = os.path.join(ROOT_DIR, "ANALYSIS_RESULTS", "PHASE3")
PLOTS_DIR = os.path.join(ROOT_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)


def plot_hero_trace_5panel(results_dir: str = RESULTS_DIR, plots_dir: str = PLOTS_DIR):
    """
    Generate 5-Panel Hero Trace Figure:
      - Subplot 1: Link latency dynamics (Raw RTT, Rolling Mean, EWMA SRTT, SLA ceiling, events)
      - Subplot 2: Policy 1 (Strict Raw, K=1)
      - Subplot 3: Policy 2 (Raw + Hysteresis, K=2)
      - Subplot 4: Policy 3 (Rolling Window Average, N=3)
      - Subplot 5: Policy 4 (Window + Hysteresis, N=3, K=2)
    """
    p1_file = os.path.join(results_dir, "hero_trace_policy_1.csv")
    p2_file = os.path.join(results_dir, "hero_trace_policy_2.csv")
    p3_file = os.path.join(results_dir, "hero_trace_policy_3.csv")
    p4_file = os.path.join(results_dir, "hero_trace_policy_4.csv")

    if not all(os.path.exists(f) for f in [p1_file, p2_file, p3_file, p4_file]):
        print("[WARN] One or more hero_trace CSV files missing. Skipping 5-panel plot.")
        return

    df1 = pd.read_csv(p1_file)
    df2 = pd.read_csv(p2_file)
    df3 = pd.read_csv(p3_file)
    df4 = pd.read_csv(p4_file)

    fig, axes = plt.subplots(5, 1, figsize=(11, 13.0), sharex=True)
    plt.subplots_adjust(hspace=0.28)

    sla_tau = 65.0
    c_blue = "#1f77b4"
    c_green = "#2ca02c"
    c_orange = "#ff7f0e"
    c_purple = "#9467bd"
    c_red = "#d62728"

    # ==================== SUBPLOT 1: Channel Scenario ====================
    ax1 = axes[0]
    ax1.plot(df2["rel_time_s"], df2["rtt_sample"], color="#4a86e8", alpha=0.45, label="Raw Sample $RTT(t)$", lw=1.2)
    ax1.plot(df2["rel_time_s"], df2["rolling_mean"], color=c_blue, lw=2.0, label="Sliding Window Mean $\\mu_{\\mathcal{W}}$ ($N=3$)")
    ax1.plot(df2["rel_time_s"], df2["srtt"], color="#0b5394", lw=1.5, linestyle=":", label="Smoothed $SRTT$ (EWMA $\\alpha=0.125$)")
    ax1.axhline(sla_tau, color=c_red, linestyle="--", lw=1.8, label=f"SLA Ceiling $\\tau = {sla_tau:.0f}$ ms")
    ax1.axvspan(5.0, 5.1, color="#f4cccc", alpha=0.7, label="Transient Micro-Burst ($88$ ms)")
    ax1.axvspan(10.0, 20.0, color="#fce5cd", alpha=0.45, label="Structural Step ($95$ ms)")
    ax1.set_ylabel("RTT (ms)", fontsize=10.5, fontweight="bold")
    ax1.set_title("(a) Channel Scenario: 100ms Micro-Burst ($t=5.0$s) and Persistent Degradation ($t=10.0$s)", fontsize=11.5, fontweight="bold")
    ax1.set_ylim(0, 115)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper left", ncol=3, fontsize=8.5, framealpha=0.9)

    # ==================== SUBPLOT 2: Policy 1 ====================
    ax2 = axes[1]
    ax2.plot(df1["rel_time_s"], df1["rtt_sample"], color=c_blue, lw=1.8, label="Policy 1 (Strict Raw, $K=1$) Active RTT")
    ax2.axhline(sla_tau, color=c_red, linestyle="--", lw=1.2, alpha=0.7)
    ax2.axvspan(5.0, 5.1, color="#f4cccc", alpha=0.5)
    ax2.axvspan(10.0, 20.0, color="#fce5cd", alpha=0.3)
    p1_switch = df1[df1["handover_executed"] == True]
    if not p1_switch.empty:
        sw_t = p1_switch.iloc[0]["rel_time_s"]
        sw_rtt = p1_switch.iloc[0]["rtt_sample"]
        ax2.scatter([sw_t], [sw_rtt], color=c_red, s=120, zorder=5, marker="X", edgecolors="black", lw=1.5)
        ax2.annotate(
            f"[!] Premature False Trigger ($t={sw_t:.2f}$s)\nSwitches to Link A (4.3 ms)",
            xy=(sw_t, sw_rtt), xytext=(sw_t + 0.6, sw_rtt + 6),
            arrowprops=dict(facecolor=c_red, shrink=0.08, width=1.5, headwidth=6),
            fontsize=9, fontweight="bold", color=c_red,
            bbox=dict(boxstyle="round,pad=0.3", fc="#fdf2f2", ec=c_red, lw=1)
        )
    ax2.set_ylabel("RTT (ms)", fontsize=10.5, fontweight="bold")
    ax2.set_title("(b) Policy 1 (Strict Raw): Unprotected Single Sample Causes Route Flapping on Micro-Burst", fontsize=11, fontweight="bold")
    ax2.set_ylim(0, 115)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right", fontsize=8.5)

    # ==================== SUBPLOT 3: Policy 2 ====================
    ax3 = axes[2]
    ax3.plot(df2["rel_time_s"], df2["rtt_sample"], color=c_green, lw=2.0, label="Policy 2 (Raw + Hysteresis, $K=2$) Active RTT")
    ax3.axhline(sla_tau, color=c_red, linestyle="--", lw=1.2, alpha=0.7)
    ax3.axvspan(5.0, 5.1, color="#f4cccc", alpha=0.5)
    ax3.axvspan(10.0, 20.0, color="#fce5cd", alpha=0.3)
    ax3.text(
        5.4, 78, "[+] Micro-Burst Absorbed\n($c_{\\mathrm{raw}}=1 \\to 0$, no switch)",
        fontsize=8.5, fontweight="bold", color="#1e4620",
        bbox=dict(boxstyle="round,pad=0.25", fc="#e6f4ea", ec=c_green, lw=1)
    )
    p2_switch = df2[df2["handover_executed"] == True]
    if not p2_switch.empty:
        sw_t = p2_switch.iloc[0]["rel_time_s"]
        sw_rtt = p2_switch.iloc[0]["rtt_sample"]
        lag_ms = int(max(0, (sw_t - 10.0) * 1000))
        ax3.scatter([sw_t], [sw_rtt], color=c_green, s=140, zorder=5, marker="*", edgecolors="black", lw=1.5)
        ax3.annotate(
            f"Policy 2 Trigger ($t={sw_t:.2f}$s, $T_{{\\mathrm{{detect}}}}={lag_ms}$ms)\nRe-Anchored to Link A",
            xy=(sw_t, sw_rtt), xytext=(sw_t + 0.6, sw_rtt - 24),
            arrowprops=dict(facecolor=c_green, shrink=0.08, width=1.5, headwidth=6),
            fontsize=9, fontweight="bold", color="#1e4620",
            bbox=dict(boxstyle="round,pad=0.3", fc="#e6f4ea", ec=c_green, lw=1)
        )
    ax3.set_ylabel("RTT (ms)", fontsize=10.5, fontweight="bold")
    ax3.set_title("(c) Policy 2 (Raw + Hysteresis, $K=2$): Temporal Confirmation Filters Micro-Burst and Triggers on Step", fontsize=11, fontweight="bold")
    ax3.set_ylim(0, 115)
    ax3.grid(True, linestyle="--", alpha=0.5)
    ax3.legend(loc="upper right", fontsize=8.5)

    # ==================== SUBPLOT 4: Policy 3 ====================
    ax4 = axes[3]
    ax4.plot(df3["rel_time_s"], df3["rtt_sample"], color=c_orange, lw=1.8, label="Policy 3 (Rolling Window Average, $N=3$) Active RTT")
    ax4.axhline(sla_tau, color=c_red, linestyle="--", lw=1.2, alpha=0.7)
    ax4.axvspan(5.0, 5.1, color="#f4cccc", alpha=0.5)
    ax4.axvspan(10.0, 20.0, color="#fce5cd", alpha=0.3)
    ax4.text(
        5.4, 78, "[+] Diluted by Window\n($\\mu_{\\mathcal{W}} = 63.3 < 65$ ms)",
        fontsize=8.5, fontweight="bold", color="#8a4200",
        bbox=dict(boxstyle="round,pad=0.25", fc="#fdf5e6", ec=c_orange, lw=1)
    )
    p3_switch = df3[df3["handover_executed"] == True]
    if not p3_switch.empty:
        sw_t = p3_switch.iloc[0]["rel_time_s"]
        sw_rtt = p3_switch.iloc[0]["rtt_sample"]
        lag_ms = int(max(0, (sw_t - 10.0) * 1000))
        ax4.scatter([sw_t], [sw_rtt], color=c_orange, s=110, zorder=5, marker="o", edgecolors="black", lw=1.5)
        ax4.annotate(
            f"Policy 3 Trigger ($t={sw_t:.2f}$s, $T_{{\\mathrm{{detect}}}}={lag_ms}$ms)",
            xy=(sw_t, sw_rtt), xytext=(sw_t + 0.6, sw_rtt - 22),
            arrowprops=dict(facecolor=c_orange, shrink=0.08, width=1.5, headwidth=6),
            fontsize=9, fontweight="bold", color="#8a4200",
            bbox=dict(boxstyle="round,pad=0.25", fc="#fdf5e6", ec=c_orange, lw=1)
        )
    ax4.set_ylabel("RTT (ms)", fontsize=10.5, fontweight="bold")
    ax4.set_title("(d) Policy 3 (Rolling Window Average): FIFO Smoothing Suppresses Noise with Moderate Reaction Lag", fontsize=11, fontweight="bold")
    ax4.set_ylim(0, 115)
    ax4.grid(True, linestyle="--", alpha=0.5)
    ax4.legend(loc="upper right", fontsize=8.5)

    # ==================== SUBPLOT 5: Policy 4 ====================
    ax5 = axes[4]
    ax5.plot(df4["rel_time_s"], df4["rtt_sample"], color=c_purple, lw=1.8, label="Policy 4 (Window + Hysteresis, $N=3, K=2$) Active RTT")
    ax5.axhline(sla_tau, color=c_red, linestyle="--", lw=1.2, alpha=0.7)
    ax5.axvspan(5.0, 5.1, color="#f4cccc", alpha=0.5)
    ax5.axvspan(10.0, 20.0, color="#fce5cd", alpha=0.3)
    p4_switch = df4[df4["handover_executed"] == True]
    if not p4_switch.empty:
        sw_t = p4_switch.iloc[0]["rel_time_s"]
        sw_rtt = p4_switch.iloc[0]["rtt_sample"]
        lag_ms = int(max(0, (sw_t - 10.0) * 1000))
        ax5.scatter([sw_t], [sw_rtt], color=c_purple, s=120, zorder=5, marker="s", edgecolors="black", lw=1.5)
        ax5.annotate(
            f"Policy 4 Trigger ($t={sw_t:.2f}$s, $T_{{\\mathrm{{detect}}}}={lag_ms}$ms)",
            xy=(sw_t, sw_rtt), xytext=(sw_t + 0.6, sw_rtt - 22),
            arrowprops=dict(facecolor=c_purple, shrink=0.08, width=1.5, headwidth=6),
            fontsize=9, fontweight="bold", color=c_purple,
            bbox=dict(boxstyle="round,pad=0.25", fc="#f3e8fd", ec=c_purple, lw=1)
        )
    ax5.set_xlabel("Elapsed Time (Seconds)", fontsize=11, fontweight="bold")
    ax5.set_ylabel("RTT (ms)", fontsize=10.5, fontweight="bold")
    ax5.set_title("(e) Policy 4 (Window + Hysteresis): Maximum Conservative Filtering Resilience", fontsize=11, fontweight="bold")
    ax5.set_ylim(0, 115)
    ax5.set_xlim(0, 20.0)
    ax5.grid(True, linestyle="--", alpha=0.5)
    ax5.legend(loc="upper right", fontsize=8.5)

    png_path = os.path.join(plots_dir, "hero_trace_5panel.png")
    pdf_path = os.path.join(plots_dir, "hero_trace_5panel.pdf")
    plt.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.savefig(pdf_path, bbox_inches="tight")
    plt.close()

    print(f"[SUCCESS] Generated 5-Panel Hero Trace: {png_path} and {pdf_path}")


def plot_hero_trace_compact(results_dir: str = RESULTS_DIR, plots_dir: str = PLOTS_DIR):
    """
    Generate 1-Plot Compact Unified Hero Trace:
      - Overlays all 4 policies on a single space-saving figure with the channel baseline.
      - Uses distinct line styles, colors, and trigger markers to avoid clutter.
    """
    p1_file = os.path.join(results_dir, "hero_trace_policy_1.csv")
    p2_file = os.path.join(results_dir, "hero_trace_policy_2.csv")
    p3_file = os.path.join(results_dir, "hero_trace_policy_3.csv")
    p4_file = os.path.join(results_dir, "hero_trace_policy_4.csv")

    if not all(os.path.exists(f) for f in [p1_file, p2_file, p3_file, p4_file]):
        print("[WARN] One or more hero_trace CSV files missing. Skipping compact plot.")
        return

    df1 = pd.read_csv(p1_file)
    df2 = pd.read_csv(p2_file)
    df3 = pd.read_csv(p3_file)
    df4 = pd.read_csv(p4_file)

    fig, ax = plt.subplots(figsize=(10.5, 5.8))

    sla_tau = 65.0
    c_blue = "#1f77b4"
    c_green = "#2ca02c"
    c_orange = "#ff7f0e"
    c_purple = "#9467bd"
    c_red = "#d62728"

    # Background shaded event regions
    ax.axvspan(5.0, 5.1, color="#f4cccc", alpha=0.75, label="Transient Micro-Burst ($88$ ms, 100ms)")
    ax.axvspan(10.0, 20.0, color="#fce5cd", alpha=0.45, label="Persistent Structural Step ($95$ ms)")
    ax.axhline(sla_tau, color=c_red, linestyle="--", lw=1.8, label=f"SLA Ceiling $\\tau = {sla_tau:.0f}$ ms")


    # Plot 4 Policy Trajectories with distinct line styles
    ax.plot(df1["rel_time_s"], df1["rtt_sample"], color=c_blue, lw=1.8, linestyle="-", label="Policy 1 (Strict Raw, $K=1$)")
    ax.plot(df2["rel_time_s"], df2["rtt_sample"], color=c_green, lw=2.4, linestyle="-", label="Policy 2 (Raw + Hysteresis, $K=2$)")
    ax.plot(df3["rel_time_s"], df3["rtt_sample"], color=c_orange, lw=1.8, linestyle="-.", label="Policy 3 (Rolling Window Average, $N=3$)")
    ax.plot(df4["rel_time_s"], df4["rtt_sample"], color=c_purple, lw=1.8, linestyle="--", label="Policy 4 (Window + Hysteresis, $N=3, K=2$)")

    # Policy 1 False Trigger Marker
    p1_switch = df1[df1["handover_executed"] == True]
    if not p1_switch.empty:
        sw_t = p1_switch.iloc[0]["rel_time_s"]
        sw_rtt = p1_switch.iloc[0]["rtt_sample"]
        ax.scatter([sw_t], [sw_rtt], color=c_red, s=130, zorder=6, marker="X", edgecolors="black", lw=1.5)
        ax.annotate(
            f"[!] P1 False Trigger ($t={sw_t:.2f}$s)\nPremature Switch to Link A",
            xy=(sw_t, sw_rtt), xytext=(sw_t - 4.5, 98),
            arrowprops=dict(facecolor=c_red, shrink=0.08, width=1.5, headwidth=6),
            fontsize=8.8, fontweight="bold", color=c_red,
            bbox=dict(boxstyle="round,pad=0.25", fc="#fdf2f2", ec=c_red, lw=1.2)
        )

    # Note that Policies 2, 3, 4 absorbed the micro-burst
    ax.text(
        5.4, 73, "[+] Micro-Burst Filtered\n(Policies 2, 3, 4 remain on B)",
        fontsize=8.2, fontweight="bold", color="#1e4620",
        bbox=dict(boxstyle="round,pad=0.25", fc="#e6f4ea", ec=c_green, lw=1)
    )

    # Policy 2 Trigger Marker
    p2_switch = df2[df2["handover_executed"] == True]
    if not p2_switch.empty:
        sw_t = p2_switch.iloc[0]["rel_time_s"]
        sw_rtt = p2_switch.iloc[0]["rtt_sample"]
        lag_ms = int(max(0, (sw_t - 10.0) * 1000))
        ax.scatter([sw_t], [sw_rtt], color=c_green, s=160, zorder=6, marker="*", edgecolors="black", lw=1.5)
        ax.annotate(
            f"P2 Trigger ($t={sw_t:.2f}$s, $T={lag_ms}$ms)\nRe-Anchored to Link A",
            xy=(sw_t, sw_rtt), xytext=(sw_t + 1.2, 92),
            arrowprops=dict(facecolor=c_green, shrink=0.08, width=1.5, headwidth=6),
            fontsize=8.8, fontweight="bold", color="#1e4620",
            bbox=dict(boxstyle="round,pad=0.25", fc="#e6f4ea", ec=c_green, lw=1.2)
        )

    # Policy 3 Trigger Marker
    p3_switch = df3[df3["handover_executed"] == True]
    if not p3_switch.empty:
        sw_t = p3_switch.iloc[0]["rel_time_s"]
        sw_rtt = p3_switch.iloc[0]["rtt_sample"]
        lag_ms = int(max(0, (sw_t - 10.0) * 1000))
        ax.scatter([sw_t], [sw_rtt], color=c_orange, s=110, zorder=6, marker="o", edgecolors="black", lw=1.5)
        ax.annotate(
            f"P3 Trigger ($t={sw_t:.2f}$s, $T={lag_ms}$ms)",
            xy=(sw_t, sw_rtt), xytext=(sw_t + 1.2, 60),
            arrowprops=dict(facecolor=c_orange, shrink=0.08, width=1.5, headwidth=6),
            fontsize=8.5, fontweight="bold", color="#8a4200",
            bbox=dict(boxstyle="round,pad=0.22", fc="#fdf5e6", ec=c_orange, lw=1)
        )

    # Policy 4 Trigger Marker
    p4_switch = df4[df4["handover_executed"] == True]
    if not p4_switch.empty:
        sw_t = p4_switch.iloc[0]["rel_time_s"]
        sw_rtt = p4_switch.iloc[0]["rtt_sample"]
        lag_ms = int(max(0, (sw_t - 10.0) * 1000))
        ax.scatter([sw_t], [sw_rtt], color=c_purple, s=110, zorder=6, marker="s", edgecolors="black", lw=1.5)
        ax.annotate(
            f"P4 Trigger ($t={sw_t:.2f}$s, $T={lag_ms}$ms)",
            xy=(sw_t, sw_rtt), xytext=(sw_t + 1.2, 30),
            arrowprops=dict(facecolor=c_purple, shrink=0.08, width=1.5, headwidth=6),
            fontsize=8.5, fontweight="bold", color=c_purple,
            bbox=dict(boxstyle="round,pad=0.22", fc="#f3e8fd", ec=c_purple, lw=1)
        )

    ax.set_xlabel("Elapsed Time (Seconds)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Active Path RTT (ms)", fontsize=11, fontweight="bold")
    ax.set_title("Synchronized Flow Steering Evaluation across Policies 1-4 (20.0s Timeline)", fontsize=12, fontweight="bold")
    ax.set_xlim(0, 20.0)
    ax.set_ylim(0, 135)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", ncol=2, fontsize=8.5, framealpha=0.92)

    png_path = os.path.join(plots_dir, "hero_trace_compact.png")
    pdf_path = os.path.join(plots_dir, "hero_trace_compact.pdf")
    plt.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.savefig(pdf_path, bbox_inches="tight")
    plt.close()

    print(f"[SUCCESS] Generated 1-Plot Compact Hero Trace: {png_path} and {pdf_path}")


def plot_hero_trace(results_dir: str = RESULTS_DIR, plots_dir: str = PLOTS_DIR):
    """Generate both 5-panel and compact Hero Trace figures."""
    plot_hero_trace_5panel(results_dir, plots_dir)
    plot_hero_trace_compact(results_dir, plots_dir)
    # Also save the 5-panel as hero_trace_comparative for full reference
    src_pdf = os.path.join(plots_dir, "hero_trace_5panel.pdf")
    dst_pdf = os.path.join(plots_dir, "hero_trace_comparative.pdf")
    src_png = os.path.join(plots_dir, "hero_trace_5panel.png")
    dst_png = os.path.join(plots_dir, "hero_trace_comparative.png")
    if os.path.exists(src_pdf):
        import shutil
        shutil.copyfile(src_pdf, dst_pdf)
        shutil.copyfile(src_png, dst_png)


def plot_monte_carlo_pareto(results_dir: str = RESULTS_DIR, plots_dir: str = PLOTS_DIR):
    """
    Generate Pareto Frontier Plot: Detection Lag (X-axis) vs. False Handover Ratio (Y-axis).
    """
    json_file = os.path.join(results_dir, "monte_carlo_summary.json")
    if not os.path.exists(json_file):
        print("[WARN] monte_carlo_summary.json not found. Skipping Pareto plot.")
        return

    with open(json_file, "r") as f:
        summary = json.load(f)

    # Extract metrics
    policies = ["STRICT_RAW", "RAW_HYSTERESIS", "ROLLING_WINDOW", "WINDOW_HYSTERESIS"]
    names = ["P1 (Strict Raw)", "P2 (Raw + Hyst)", "P3 (Rolling Window)", "P4 (Win + Hyst)"]
    colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd"]
    markers = ["X", "*", "o", "s"]

    lags = [summary[p]["detection_lag_mean_ms"] for p in policies]
    lags_std = [summary[p]["detection_lag_std_ms"] for p in policies]
    fa_rates = [summary[p]["false_alarm_ratio_pct"] for p in policies]
    fa_std = [summary[p]["false_alarm_ratio_std"] for p in policies]

    plt.figure(figsize=(7.5, 5.5))
    ax = plt.gca()

    # Draw Trade-off boundary connecting P1 -> P2 -> P4
    pareto_x = [lags[0], lags[1], lags[3]]
    pareto_y = [fa_rates[0], fa_rates[1], fa_rates[3]]
    plt.plot(pareto_x, pareto_y, "--", color="#7f7f7f", lw=1.8, label="Empirical Trade-off Boundary", zorder=1)

    # Plot policy points
    for i in range(4):
        plt.errorbar(
            lags[i], fa_rates[i],
            xerr=lags_std[i] if lags_std[i] > 0 else None,
            yerr=fa_std[i] if fa_std[i] > 0 else None,
            fmt=markers[i], color=colors[i], ecolor=colors[i],
            elinewidth=1.5, capsize=4, markersize=10,
            label=f"{names[i]} ({fa_rates[i]:.1f}%, {lags[i]:.0f}ms)",
            zorder=3
        )

    # Highlight Policy 2 optimal knee
    p2_x = lags[1]
    p2_y = fa_rates[1]
    ax.annotate(
        "Policy 2 Operating Knee\n(Low Flapping + Low Detection Lag)",
        xy=(p2_x, p2_y), xytext=(p2_x + 35, p2_y + 12),
        arrowprops=dict(facecolor="#2ca02c", shrink=0.08, width=1.5, headwidth=6),
        fontsize=9.5, fontweight="bold", color="#1e4620",
        bbox=dict(boxstyle="round,pad=0.35", fc="#e6f4ea", ec="#2ca02c", lw=1.2)
    )

    plt.xlabel("SLA Violation Detection Lag $T_{\\mathrm{detect}}$ (ms)", fontsize=11, fontweight="bold")
    plt.ylabel("False Handover Ratio (%)", fontsize=11, fontweight="bold")
    plt.title("Empirical Trade-Off: Detection Lag vs. False Handover Ratio ($N=30$ Runs/Policy)", fontsize=12, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(loc="upper right", fontsize=9.5, framealpha=0.95)
    plt.xlim(-10, max(lags) + 70)
    plt.ylim(-5, max(fa_rates) + 15)

    png_path = os.path.join(plots_dir, "monte_carlo_pareto.png")
    pdf_path = os.path.join(plots_dir, "monte_carlo_pareto.pdf")
    plt.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.savefig(pdf_path, bbox_inches="tight")
    plt.close()

    print(f"[SUCCESS] Generated Trade-Off plot: {png_path} and {pdf_path}")


def plot_monte_carlo_boxplots(results_dir: str = RESULTS_DIR, plots_dir: str = PLOTS_DIR):
    """
    Generate side-by-side boxplots for:
      (a) Route Flapping Frequency (Handovers per Run)
      (b) SLA Violation Detection Lag (ms)
    """
    csv_file = os.path.join(results_dir, "monte_carlo_trials.csv")
    if not os.path.exists(csv_file):
        print("[WARN] monte_carlo_trials.csv not found. Skipping boxplots.")
        return

    df = pd.read_csv(csv_file)
    policies = [1, 2, 3, 4]
    policy_labels = ["P1: Strict Raw", "P2: Raw + Hyst", "P3: Window", "P4: Win + Hyst"]
    colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd"]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))

    # Subplot (a): Handover Flapping Frequency
    ax1 = axes[0]
    ho_data = [df[df["policy"] == p]["handover_count"].values for p in policies]
    bp1 = ax1.boxplot(ho_data, patch_artist=True, tick_labels=policy_labels, showmeans=True)
    for patch, color in zip(bp1["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.65)
    for median in bp1["medians"]:
        median.set(color="black", linewidth=1.5)

    ax1.set_ylabel("Handovers per Run", fontsize=11, fontweight="bold")
    ax1.set_title("(a) Route Flapping Stability", fontsize=12, fontweight="bold")
    ax1.grid(True, linestyle="--", alpha=0.5, axis="y")

    # Subplot (b): SLA Violation Detection Lag
    ax2 = axes[1]
    lag_data = [df[df["policy"] == p]["detection_lag_ms"].values for p in policies]
    bp2 = ax2.boxplot(lag_data, patch_artist=True, tick_labels=policy_labels, showmeans=True)
    for patch, color in zip(bp2["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.65)
    for median in bp2["medians"]:
        median.set(color="black", linewidth=1.5)

    ax2.set_ylabel("Detection Lag $T_{\\mathrm{detect}}$ (ms)", fontsize=11, fontweight="bold")
    ax2.set_title("(b) SLA Violation Recovery Responsiveness", fontsize=12, fontweight="bold")
    ax2.grid(True, linestyle="--", alpha=0.5, axis="y")

    plt.tight_layout()

    png_path = os.path.join(plots_dir, "monte_carlo_boxplots.png")
    pdf_path = os.path.join(plots_dir, "monte_carlo_boxplots.pdf")
    plt.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.savefig(pdf_path, bbox_inches="tight")
    plt.close()

    print(f"[SUCCESS] Generated Monte Carlo Boxplots: {png_path} and {pdf_path}")


def print_paper_tables(results_dir: str = RESULTS_DIR):
    """Print LaTeX and Markdown tables for conference paper integration."""
    print("\n" + "=" * 80)
    print("CONFERENCE PAPER TABLE V: HERO TRACE MICRO-BENCHMARK (LaTeX Ready)")
    print("=" * 80)
    print(r"""\begin{table}[htbp]
\caption{Deterministic Hero Trace Micro-Benchmark (20.0s Timeline)}
\label{tab:hero_trace_metrics}
\centering
\begin{tabular}{lccccc}
\toprule
\textbf{Policy} & \textbf{Transient Burst} & \textbf{First Trigger} & \textbf{Switch Delay} & \textbf{Detection Lag} & \textbf{SLA Violation} \\
& \textbf{Response ($t=5.0$\,s)} & \textbf{Timestamp ($t$)} & \textbf{$\Delta t_{\text{route}}$ (ms)} & \textbf{$T_{\text{detect}}$ (ms)} & \textbf{Duration (ms)} \\
\midrule""")

    p_names = {
        1: "Policy 1 (Strict Raw)",
        2: "Policy 2 (Raw + Hyst)",
        3: "Policy 3 (Window)",
        4: "Policy 4 (Win + Hyst)",
    }

    for pol in [1, 2, 3, 4]:
        fpath = os.path.join(results_dir, f"hero_trace_policy_{pol}.csv")
        if os.path.exists(fpath):
            df = pd.read_csv(fpath)
            switches = df[df["handover_executed"] == True]
            t_first = switches["rel_time_s"].iloc[0] if len(switches) > 0 else None
            sw_lat = switches["switch_latency_ms"].iloc[0] if len(switches) > 0 else None
            false_trig = any(switches["rel_time_s"] < 9.0) if len(switches) > 0 else False
            step_switches = df[(df["handover_executed"] == True) & (df["rel_time_s"] >= 9.9)]
            detect_lag = (step_switches["rel_time_s"].iloc[0] - 10.0) * 1000.0 if len(step_switches) > 0 else None
            sla_ticks = len(df[df["rtt_sample"] > 65.0])
            sla_viols = sla_ticks * 100.0

            burst_str = "False Alarm" if false_trig else "Filtered"
            t_str = f"{t_first:.3f}\\,s" if t_first else "---"
            sw_str = f"{sw_lat:.2f}" if sw_lat else "---"
            lag_str = f"{detect_lag:.1f}" if detect_lag else "N/A"
            viol_str = f"{sla_viols:.0f}"

            if pol == 2:
                burst_str = f"\\textbf{{{burst_str}}}"
                t_str = f"\\textbf{{{t_str}}}"
                sw_str = f"\\textbf{{{sw_str}}}"
                lag_str = f"\\textbf{{{lag_str}}}"
                viol_str = f"\\textbf{{{viol_str}}}"

            print(f"{p_names[pol]:<24} & {burst_str:<20} & {t_str:<18} & {sw_str:<10} & {lag_str:<10} & {viol_str} \\\\")

    print(r"""\bottomrule
\end{tabular}
\end{table}""")

    json_file = os.path.join(results_dir, "monte_carlo_summary.json")
    if not os.path.exists(json_file):
        return

    with open(json_file, "r") as f:
        summary = json.load(f)

    print("\n" + "=" * 80)
    print("CONFERENCE PAPER TABLE VI: MONTE CARLO AGGREGATES (LaTeX Ready)")
    print("=" * 80)
    print(r"""\begin{table}[htbp]
\caption{Randomized Stress-Testing: Monte Carlo Aggregates ($N = 30$ Runs per Policy)}
\label{tab:random_comparison}
\centering
\begin{tabular}{lcccc}
\toprule
\textbf{Evaluated} & \textbf{False Handover} & \textbf{Detection Delay} & \textbf{Handovers} & \textbf{Mean SLA Viol.} \\
\textbf{Policy} & \textbf{Ratio (\%)} & \textbf{$T_{\text{detect}}$ (ms)} & \textbf{per Run} & \textbf{Duration (ms)} \\
\midrule""")
    
    mapping = {
        "STRICT_RAW": "Policy 1 (Strict Raw)",
        "RAW_HYSTERESIS": "Policy 2 (Raw + Hyst)",
        "ROLLING_WINDOW": "Policy 3 (Window)",
        "WINDOW_HYSTERESIS": "Policy 4 (Win + Hyst)",
    }

    for key, name in mapping.items():
        if key in summary:
            s = summary[key]
            fa = f"${s['false_alarm_ratio_pct']:.1f} \\pm {s['false_alarm_ratio_std']:.1f}\\%$"
            lag = f"${s['detection_lag_mean_ms']:.0f} \\pm {s['detection_lag_std_ms']:.0f}$"
            ho = f"${s['handovers_per_run_mean']:.1f} \\pm {s['handovers_per_run_std']:.1f}$"
            viol = f"${s['sla_viol_duration_mean_ms']:.0f} \\pm {s['sla_viol_duration_std_ms']:.0f}$"
            if key == "RAW_HYSTERESIS":
                fa = f"\\textbf{{{fa}}}"
                ho = f"\\textbf{{{ho}}}"
                viol = f"\\textbf{{{viol}}}"
            elif key == "WINDOW_HYSTERESIS":
                fa = f"\\textbf{{{fa}}}"
            print(f"{name:<24} & {fa:<24} & {lag:<18} & {ho:<16} & {viol} \\\\")

    print(r"""\bottomrule
\end{tabular}
\end{table}""")
    print("=" * 80)


def generate_phase3_publication_plots():
    plot_hero_trace()
    plot_monte_carlo_pareto()
    plot_monte_carlo_boxplots()
    print_paper_tables()


def main():
    generate_phase3_publication_plots()


if __name__ == "__main__":
    main()
