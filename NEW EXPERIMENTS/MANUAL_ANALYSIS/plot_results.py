#!/usr/bin/env python3
"""
plot_results.py

Comprehensive publication visualization suite for experiment results.
Reads statistical CSV tables from the ./RESULTS directory and generates
high-resolution publication-quality plots comparing TCP CUBIC and TCP Reno.

Generated figures:
  --- Baseline Scaling (50 MB to 500 MB) ---
  1. plot_transfer_time.png          - Completion time scaling: Direct Baseline vs Migration (CUBIC vs Reno)
  2. plot_handover_overhead.png      - Handover Invariance Law: Overhead (Delta T) vs Payload Size
  3. plot_relative_decay.png         - Hyperbolic relative penalty decay (rho = Delta T / T_base)
  4. plot_baseline_throughput.png    - Effective throughput (Mbit/s) asymptoting to bottleneck capacity

  --- Parametric Impairment Sweeps (CUBIC vs Reno) ---
  5. plot_latency_sweep.png          - Latency Sweep: Completion time & overhead vs Latency (10ms to 160ms)
  6. plot_loss_sweep.png             - Loss Sweep: Completion time & goodput collapse vs Loss (0.1% to 5%)
  7. plot_jitter_sweep.png           - Jitter Sweep: Completion time & overhead stability vs Jitter (0ms to 20ms)

  --- Advanced Comparative & Analytical Models ---
  8. plot_impairments_overview.png   - Consolidated 1x3 paper overview (Latency, Loss, Jitter)
  9. plot_protocol_advantage.png     - CUBIC vs Reno relative speedup (%) across Latency & Loss
  10. plot_latency_linear_model.png  - Empirical linear regression fit: Delta T = m * Latency + c
  11. plot_loss_goodput_parity.png   - Handover Overhead Negligibility under Loss: Baseline vs Migration Goodput Parity
"""

import os
import re
import csv
import glob
import argparse
import numpy as np
import matplotlib
# Headless backend for remote server environments without display
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ==============================================================================
# CSV LOADING HELPERS
# ==============================================================================

def load_baseline_results(csv_path):
    """
    Loads baseline summary metrics from a combined CSV table
    (e.g., baseline_cubic_all_results.csv or reno_all_results.csv).

    Returns:
        dict: Mapping file_size_mb (int) -> dict of metrics
    """
    if not os.path.exists(csv_path):
        return None

    data = {}
    with open(csv_path, mode="r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                fs = int(float(row["file_size_mb"]))
                data[fs] = {
                    "direct_mean": float(row.get("direct_transfer_mean", 0)),
                    "direct_std": float(row.get("direct_transfer_std", 0)),
                    "direct_median": float(row.get("direct_transfer_median", 0)),
                    "migrate_mean": float(row.get("migration_transfer_mean", 0)),
                    "migrate_std": float(row.get("migration_transfer_std", 0)),
                    "migrate_median": float(row.get("migration_transfer_median", 0)),
                    "diff_mean": float(row.get("diff_mean", 0)),
                    "diff_std": float(row.get("diff_std", 0)),
                    "diff_median": float(row.get("diff_median", 0)),
                }
            except (ValueError, KeyError):
                continue
    return data


def parse_parameter_val(val_str):
    """Extracts floating point value from strings like '10ms', '0.1%', '2ms'."""
    clean = re.sub(r"[^\d.]", "", val_str)
    return float(clean) if clean else 0.0


def load_sweep_series(results_dir, sweep_type, cca="cubic"):
    """
    Finds and parses all '{cca}_{sweep_type}_*_all_results.csv' files in results_dir.

    Parameters:
        results_dir (str): Directory containing the CSV tables.
        sweep_type (str): 'latency', 'loss', or 'jitter'.
        cca (str): 'cubic' or 'reno'.

    Returns:
        dict: Mapping file_size_mb (e.g., 100, 200) -> list of dicts:
              [{'param_str': '10ms', 'param_val': 10.0, 'metrics': {...}}, ...]
              sorted by param_val ascending.
    """
    pattern = os.path.join(results_dir, f"{cca}_{sweep_type}_*_all_results.csv")
    csv_files = glob.glob(pattern)
    if not csv_files:
        return {}

    by_file_size = {}

    for filepath in csv_files:
        filename = os.path.basename(filepath)
        prefix = f"{cca}_{sweep_type}_"
        suffix = "_all_results.csv"
        if not (filename.startswith(prefix) and filename.endswith(suffix)):
            continue

        param_str = filename[len(prefix):-len(suffix)]
        param_val = parse_parameter_val(param_str)

        with open(filepath, mode="r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    fs = int(float(row["file_size_mb"]))
                    metrics = {
                        "direct_mean": float(row.get("direct_transfer_mean", 0)),
                        "direct_std": float(row.get("direct_transfer_std", 0)),
                        "migrate_mean": float(row.get("migration_transfer_mean", 0)),
                        "migrate_std": float(row.get("migration_transfer_std", 0)),
                        "diff_mean": float(row.get("diff_mean", 0)),
                        "diff_std": float(row.get("diff_std", 0)),
                    }
                    by_file_size.setdefault(fs, []).append({
                        "param_str": param_str,
                        "param_val": param_val,
                        "metrics": metrics,
                    })
                except (ValueError, KeyError):
                    continue

    # Sort each file size series by param_val ascending
    for fs in by_file_size:
        by_file_size[fs].sort(key=lambda x: x["param_val"])

    return by_file_size


# ==============================================================================
# BASELINE PLOTTING FUNCTIONS
# ==============================================================================

def plot_transfer_time(cubic_data, reno_data, output_file):
    """
    Plots direct baseline transfer time vs. mid-transfer migration time
    across payload sizes (50 to 500 MB) for TCP CUBIC and TCP Reno.
    """
    if not cubic_data:
        print("Skipping plot_transfer_time: No CUBIC baseline data found.")
        return

    file_sizes = sorted(cubic_data.keys())
    cubic_direct = [cubic_data[s]["direct_mean"] for s in file_sizes]
    cubic_migrate = [cubic_data[s]["migrate_mean"] for s in file_sizes]

    plt.figure(figsize=(9, 5.5), dpi=300)
    plt.plot(file_sizes, cubic_direct, 'o-', color='#1f77b4', label='TCP CUBIC - Direct Baseline', linewidth=2, markersize=6)
    plt.plot(file_sizes, cubic_migrate, 's--', color='#ff7f0e', label='TCP CUBIC - Migration', linewidth=2, markersize=6)

    if reno_data:
        reno_sizes = sorted(reno_data.keys())
        reno_direct = [reno_data[s]["direct_mean"] for s in reno_sizes]
        reno_migrate = [reno_data[s]["migrate_mean"] for s in reno_sizes]
        plt.plot(reno_sizes, reno_direct, '^:', color='#2ca02c', label='TCP Reno - Direct Baseline', linewidth=1.8, markersize=6)
        plt.plot(reno_sizes, reno_migrate, 'x-.', color='#d62728', label='TCP Reno - Migration', linewidth=1.8, markersize=6)

    plt.title("Total Transfer Time: Direct Transfer vs. Mid-Transfer Migration", fontsize=13, fontweight='bold', pad=12)
    plt.xlabel("Payload Size (MB)", fontsize=11, fontweight='semibold')
    plt.ylabel("Completion Time (seconds)", fontsize=11, fontweight='semibold')
    plt.xticks(file_sizes)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=10)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"Saved: {output_file}")


def plot_handover_overhead(cubic_data, reno_data, output_file):
    """
    Plots absolute handover overhead time (Delta T = T_migration - T_baseline) in milliseconds
    across payload sizes (50 to 500 MB) demonstrating the Handover Invariance Law.
    """
    if not cubic_data:
        print("Skipping plot_handover_overhead: No CUBIC baseline data found.")
        return

    file_sizes = sorted(cubic_data.keys())
    cubic_means_ms = [cubic_data[s]["diff_mean"] * 1000 for s in file_sizes]
    cubic_stds_ms = [cubic_data[s]["diff_std"] * 1000 for s in file_sizes]

    plt.figure(figsize=(9, 5.5), dpi=300)
    plt.errorbar(
        file_sizes, cubic_means_ms, yerr=cubic_stds_ms,
        fmt='o-', color='#1f77b4', ecolor='#aec7e8', elinewidth=2, capsize=4,
        label='TCP CUBIC Overhead (Mean ± Std)', linewidth=2, markersize=6
    )

    overall_cubic_mean = sum(cubic_means_ms) / len(cubic_means_ms)
    plt.axhline(overall_cubic_mean, color='#1f77b4', linestyle=':', alpha=0.7,
                label=f'CUBIC Invariant Mean ({overall_cubic_mean:.1f} ms)')

    if reno_data:
        reno_sizes = sorted(reno_data.keys())
        reno_means_ms = [reno_data[s]["diff_mean"] * 1000 for s in reno_sizes]
        reno_stds_ms = [reno_data[s]["diff_std"] * 1000 for s in reno_sizes]
        plt.errorbar(
            reno_sizes, reno_means_ms, yerr=reno_stds_ms,
            fmt='s--', color='#ff7f0e', ecolor='#ffbb78', elinewidth=2, capsize=4,
            label='TCP Reno Overhead (Mean ± Std)', linewidth=2, markersize=6
        )
        overall_reno_mean = sum(reno_means_ms) / len(reno_means_ms)
        plt.axhline(overall_reno_mean, color='#ff7f0e', linestyle='-.', alpha=0.7,
                    label=f'Reno Invariant Mean ({overall_reno_mean:.1f} ms)')

    plt.title("Handover Overhead vs. Payload Size (Handover Invariance Law)", fontsize=13, fontweight='bold', pad=12)
    plt.xlabel("Payload Size (MB)", fontsize=11, fontweight='semibold')
    plt.ylabel("Handover Overhead ΔT (milliseconds)", fontsize=11, fontweight='semibold')
    plt.xticks(file_sizes)
    plt.ylim(bottom=0)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=10)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"Saved: {output_file}")


def plot_relative_decay(cubic_data, reno_data, output_file):
    """
    Plots relative overhead penalty [rho = (Delta T / T_baseline) * 100%]
    decaying hyperbolically (proportional to 1/S) as file size increases.
    """
    if not cubic_data:
        print("Skipping plot_relative_decay: No CUBIC baseline data found.")
        return

    file_sizes = sorted(cubic_data.keys())
    cubic_rel_pct = [
        (cubic_data[s]["diff_mean"] / cubic_data[s]["direct_mean"]) * 100
        for s in file_sizes
    ]

    plt.figure(figsize=(9, 5.5), dpi=300)
    plt.plot(file_sizes, cubic_rel_pct, 'o-', color='#1f77b4', linewidth=2.2, markersize=7, label='TCP CUBIC Relative Overhead (%)')

    plt.annotate(f"{cubic_rel_pct[0]:.2f}%", (file_sizes[0], cubic_rel_pct[0]),
                 textcoords="offset points", xytext=(10, 5), fontweight='semibold', color='#1f77b4')
    plt.annotate(f"{cubic_rel_pct[-1]:.2f}%", (file_sizes[-1], cubic_rel_pct[-1]),
                 textcoords="offset points", xytext=(-25, 10), fontweight='semibold', color='#1f77b4')

    if reno_data:
        reno_sizes = sorted(reno_data.keys())
        reno_rel_pct = [
            (reno_data[s]["diff_mean"] / reno_data[s]["direct_mean"]) * 100
            for s in reno_sizes
        ]
        plt.plot(reno_sizes, reno_rel_pct, 's--', color='#ff7f0e', linewidth=2, markersize=6, label='TCP Reno Relative Overhead (%)')
        plt.annotate(f"{reno_rel_pct[0]:.2f}%", (reno_sizes[0], reno_rel_pct[0]),
                     textcoords="offset points", xytext=(10, -15), fontweight='semibold', color='#ff7f0e')
        plt.annotate(f"{reno_rel_pct[-1]:.2f}%", (reno_sizes[-1], reno_rel_pct[-1]),
                     textcoords="offset points", xytext=(-25, -15), fontweight='semibold', color='#ff7f0e')

    plt.title("Hyperbolic Decay of Relative Handover Penalty (ρ ∝ 1/S)", fontsize=13, fontweight='bold', pad=12)
    plt.xlabel("Payload Size (MB)", fontsize=11, fontweight='semibold')
    plt.ylabel("Relative Overhead Penalty (%)", fontsize=11, fontweight='semibold')
    plt.xticks(file_sizes)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=10)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"Saved: {output_file}")


def plot_baseline_throughput(cubic_data, reno_data, output_file):
    """
    Plots effective data throughput (Mbit/s = (Size * 8) / Time) across payload sizes (50 to 500 MB),
    illustrating slow-start amortization and asymptotic convergence to bottleneck link rate (50 Mbit/s).
    """
    if not cubic_data:
        return

    file_sizes = sorted(cubic_data.keys())
    c_base_tp = [(s * 8.0) / cubic_data[s]["direct_mean"] for s in file_sizes]
    c_migr_tp = [(s * 8.0) / cubic_data[s]["migrate_mean"] for s in file_sizes]

    plt.figure(figsize=(9, 5.5), dpi=300)
    plt.plot(file_sizes, c_base_tp, 'o-', color='#1f77b4', linewidth=2, markersize=6, label='TCP CUBIC - Direct Baseline')
    plt.plot(file_sizes, c_migr_tp, 's--', color='#ff7f0e', linewidth=2, markersize=6, label='TCP CUBIC - Migration')

    if reno_data:
        r_sizes = sorted(reno_data.keys())
        r_base_tp = [(s * 8.0) / reno_data[s]["direct_mean"] for s in r_sizes]
        r_migr_tp = [(s * 8.0) / reno_data[s]["migrate_mean"] for s in r_sizes]
        plt.plot(r_sizes, r_base_tp, '^:', color='#2ca02c', linewidth=1.8, markersize=6, label='TCP Reno - Direct Baseline')
        plt.plot(r_sizes, r_migr_tp, 'x-.', color='#d62728', linewidth=1.8, markersize=6, label='TCP Reno - Migration')

    # Reference bottleneck line
    plt.axhline(50.0, color='gray', linestyle='--', linewidth=1.2, alpha=0.7, label='Bottleneck Link Capacity (50 Mbit/s)')

    plt.title("Effective Transfer Throughput Scaling vs. Payload Size", fontsize=13, fontweight='bold', pad=12)
    plt.xlabel("Payload Size (MB)", fontsize=11, fontweight='semibold')
    plt.ylabel("Effective Throughput (Mbit/s)", fontsize=11, fontweight='semibold')
    plt.xticks(file_sizes)
    plt.ylim(30, 52)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=9.5)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"Saved: {output_file}")


# ==============================================================================
# PARAMETRIC SWEEPS PLOTTING FUNCTIONS (CUBIC vs RENO)
# ==============================================================================

def plot_latency_sweep(cubic_data, reno_data, output_file):
    """
    Plots Latency Sweep (CUBIC vs Reno):
    - Panel 1: Completion Time vs. Network Latency for 100 MB and 200 MB.
    - Panel 2: Handover Overhead (Delta T) vs. Network Latency.
    """
    if not cubic_data and not reno_data:
        print("Skipping plot_latency_sweep: No latency sweep data found.")
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5), dpi=300)

    colors_cubic = {100: "#1f77b4", 200: "#02818a"}
    colors_reno = {100: "#d62728", 200: "#990000"}
    markers_cubic = {100: "o", 200: "s"}
    markers_reno = {100: "^", 200: "v"}

    all_sizes = sorted(set(list(cubic_data.keys()) + list(reno_data.keys() if reno_data else [])))

    for fs in all_sizes:
        if cubic_data and fs in cubic_data:
            series_c = cubic_data[fs]
            lats_c = [x["param_val"] for x in series_c]
            b_c = [x["metrics"]["direct_mean"] for x in series_c]
            o_c = [x["metrics"]["diff_mean"] for x in series_c]
            o_c_std = [x["metrics"]["diff_std"] for x in series_c]

            c_color = colors_cubic.get(fs, "#1f77b4")
            m_c = markers_cubic.get(fs, "o")

            ax1.plot(lats_c, b_c, f"-{m_c}", color=c_color, linewidth=2, label=f"CUBIC ({fs} MB)")
            ax2.errorbar(lats_c, o_c, yerr=o_c_std, fmt=f"-{m_c}", color=c_color, linewidth=2, capsize=4, label=f"CUBIC ΔT ({fs} MB)")

        if reno_data and fs in reno_data:
            series_r = reno_data[fs]
            lats_r = [x["param_val"] for x in series_r]
            b_r = [x["metrics"]["direct_mean"] for x in series_r]
            o_r = [x["metrics"]["diff_mean"] for x in series_r]
            o_r_std = [x["metrics"]["diff_std"] for x in series_r]

            r_color = colors_reno.get(fs, "#d62728")
            m_r = markers_reno.get(fs, "^")

            ax1.plot(lats_r, b_r, f"--{m_r}", color=r_color, linewidth=2, label=f"Reno ({fs} MB)")
            ax2.errorbar(lats_r, o_r, yerr=o_r_std, fmt=f"--{m_r}", color=r_color, linewidth=2, capsize=4, label=f"Reno ΔT ({fs} MB)")

    ax1.set_title("Completion Time: CUBIC vs. Reno Scaling", fontsize=12, fontweight="bold")
    ax1.set_xlabel("One-Way Latency (ms)", fontsize=11, fontweight="semibold")
    ax1.set_ylabel("Completion Time (seconds)", fontsize=11, fontweight="semibold")
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(frameon=True, fontsize=9)

    ax2.set_title("Handover Overhead Scaling with Latency", fontsize=12, fontweight="bold")
    ax2.set_xlabel("One-Way Latency (ms)", fontsize=11, fontweight="semibold")
    ax2.set_ylabel("Handover Overhead ΔT (seconds)", fontsize=11, fontweight="semibold")
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(frameon=True, fontsize=9)

    title_suffix = " (CUBIC vs. Reno)" if reno_data else " (TCP CUBIC)"
    plt.suptitle(f"Latency Sweep Impact on Migration Performance{title_suffix}", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"Saved: {output_file}")


def plot_loss_sweep(cubic_data, reno_data, output_file):
    """
    Plots Packet Loss Sweep (CUBIC vs Reno):
    - Panel 1: Completion Time vs. Packet Loss Rate (Log scale for explosion).
    - Panel 2: Effective Goodput (Mbit/s) vs. Packet Loss Rate (Goodput collapse).
    """
    if not cubic_data and not reno_data:
        print("Skipping plot_loss_sweep: No loss sweep data found.")
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5), dpi=300)

    colors_cubic = {100: "#1f77b4", 200: "#02818a"}
    colors_reno = {100: "#d62728", 200: "#990000"}
    markers_cubic = {100: "o", 200: "s"}
    markers_reno = {100: "^", 200: "v"}

    all_sizes = sorted(set(list(cubic_data.keys()) + list(reno_data.keys() if reno_data else [])))

    for fs in all_sizes:
        file_bits = fs * 8.0

        if cubic_data and fs in cubic_data:
            series_c = cubic_data[fs]
            losses_c = [x["param_val"] for x in series_c]
            b_c = [x["metrics"]["direct_mean"] for x in series_c]
            gp_c = [(file_bits / t) if t > 0 else 0 for t in b_c]

            c_color = colors_cubic.get(fs, "#1f77b4")
            m_c = markers_cubic.get(fs, "o")

            ax1.plot(losses_c, b_c, f"-{m_c}", color=c_color, linewidth=2, label=f"CUBIC ({fs} MB)")
            ax2.plot(losses_c, gp_c, f"-{m_c}", color=c_color, linewidth=2, label=f"CUBIC Goodput ({fs} MB)")

        if reno_data and fs in reno_data:
            series_r = reno_data[fs]
            losses_r = [x["param_val"] for x in series_r]
            b_r = [x["metrics"]["direct_mean"] for x in series_r]
            gp_r = [(file_bits / t) if t > 0 else 0 for t in b_r]

            r_color = colors_reno.get(fs, "#d62728")
            m_r = markers_reno.get(fs, "^")

            ax1.plot(losses_r, b_r, f"--{m_r}", color=r_color, linewidth=2, label=f"Reno ({fs} MB)")
            ax2.plot(losses_r, gp_r, f"--{m_r}", color=r_color, linewidth=2, label=f"Reno Goodput ({fs} MB)")

    ax1.set_title("Completion Time Explosion under Packet Loss", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Packet Loss Rate (%)", fontsize=11, fontweight="semibold")
    ax1.set_ylabel("Completion Time (seconds) [Log Scale]", fontsize=11, fontweight="semibold")
    ax1.set_yscale("log")
    ax1.grid(True, which="both", linestyle="--", alpha=0.5)
    ax1.legend(frameon=True, fontsize=9)

    ax2.set_title("Effective Goodput Collapse under Loss", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Packet Loss Rate (%)", fontsize=11, fontweight="semibold")
    ax2.set_ylabel("Effective Goodput (Mbit/s)", fontsize=11, fontweight="semibold")
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(frameon=True, fontsize=9)

    title_suffix = " (CUBIC vs. Reno)" if reno_data else " (TCP CUBIC)"
    plt.suptitle(f"Packet Loss Sweep Impact on Migration Performance{title_suffix}", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"Saved: {output_file}")


def plot_jitter_sweep(cubic_data, reno_data, output_file):
    """
    Plots Latency Jitter Sweep (CUBIC vs Reno):
    - Panel 1: Completion Time vs. Latency Jitter for 100 MB and 200 MB.
    - Panel 2: Handover Overhead (Delta T) vs. Latency Jitter.
    """
    if not cubic_data and not reno_data:
        print("Skipping plot_jitter_sweep: No jitter sweep data found.")
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5), dpi=300)

    colors_cubic = {100: "#1f77b4", 200: "#02818a"}
    colors_reno = {100: "#d62728", 200: "#990000"}
    markers_cubic = {100: "o", 200: "s"}
    markers_reno = {100: "^", 200: "v"}

    all_sizes = sorted(set(list(cubic_data.keys()) + list(reno_data.keys() if reno_data else [])))

    for fs in all_sizes:
        if cubic_data and fs in cubic_data:
            series_c = cubic_data[fs]
            jits_c = [x["param_val"] for x in series_c]
            b_c = [x["metrics"]["direct_mean"] for x in series_c]
            o_c = [x["metrics"]["diff_mean"] for x in series_c]
            o_c_std = [x["metrics"]["diff_std"] for x in series_c]

            c_color = colors_cubic.get(fs, "#1f77b4")
            m_c = markers_cubic.get(fs, "o")

            ax1.plot(jits_c, b_c, f"-{m_c}", color=c_color, linewidth=2, label=f"CUBIC ({fs} MB)")
            ax2.errorbar(jits_c, o_c, yerr=o_c_std, fmt=f"-{m_c}", color=c_color, linewidth=2, capsize=4, label=f"CUBIC ΔT ({fs} MB)")

        if reno_data and fs in reno_data:
            series_r = reno_data[fs]
            jits_r = [x["param_val"] for x in series_r]
            b_r = [x["metrics"]["direct_mean"] for x in series_r]
            o_r = [x["metrics"]["diff_mean"] for x in series_r]
            o_r_std = [x["metrics"]["diff_std"] for x in series_r]

            r_color = colors_reno.get(fs, "#d62728")
            m_r = markers_reno.get(fs, "^")

            ax1.plot(jits_r, b_r, f"--{m_r}", color=r_color, linewidth=2, label=f"Reno ({fs} MB)")
            ax2.errorbar(jits_r, o_r, yerr=o_r_std, fmt=f"--{m_r}", color=r_color, linewidth=2, capsize=4, label=f"Reno ΔT ({fs} MB)")

    ax1.set_title("Completion Time Sensitivity to Jitter", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Latency Jitter (± ms around 40ms)", fontsize=11, fontweight="semibold")
    ax1.set_ylabel("Completion Time (seconds)", fontsize=11, fontweight="semibold")
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(frameon=True, fontsize=9)

    ax2.set_title("Handover Overhead vs. Latency Jitter", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Latency Jitter (± ms around 40ms)", fontsize=11, fontweight="semibold")
    ax2.set_ylabel("Handover Overhead ΔT (seconds)", fontsize=11, fontweight="semibold")
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(frameon=True, fontsize=9)

    title_suffix = " (CUBIC vs. Reno)" if reno_data else " (TCP CUBIC)"
    plt.suptitle(f"Latency Jitter Sweep Impact on Migration Performance{title_suffix}", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"Saved: {output_file}")


# ==============================================================================
# ADVANCED ANALYTICAL PLOTS
# ==============================================================================

def plot_impairments_overview(cubic_latency, reno_latency, cubic_loss, reno_loss, cubic_jitter, reno_jitter, output_file):
    """
    Consolidated 1x3 publication panel figure:
    - Subplot 1: Latency Sweep Completion Times (CUBIC vs Reno, 100MB & 200MB)
    - Subplot 2: Loss Sweep Goodput Collapse (Mbit/s vs Loss Rate, Log scale)
    - Subplot 3: Jitter Sweep Overhead Stability (Delta T vs Jitter)
    """
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5.2), dpi=300)

    # 1. Latency Sweep Completion Times
    for fs in [100, 200]:
        c_col = "#1f77b4" if fs == 100 else "#02818a"
        r_col = "#d62728" if fs == 100 else "#990000"
        m_c = "o" if fs == 100 else "s"
        m_r = "^" if fs == 100 else "v"

        if cubic_latency and fs in cubic_latency:
            s_c = cubic_latency[fs]
            ax1.plot([x["param_val"] for x in s_c], [x["metrics"]["direct_mean"] for x in s_c],
                     f"-{m_c}", color=c_col, linewidth=2, label=f"CUBIC ({fs}MB)")

        if reno_latency and fs in reno_latency:
            s_r = reno_latency[fs]
            ax1.plot([x["param_val"] for x in s_r], [x["metrics"]["direct_mean"] for x in s_r],
                     f"--{m_r}", color=r_col, linewidth=2, label=f"Reno ({fs}MB)")

    ax1.set_title("(a) Latency: RTT Growth Divergence", fontsize=11.5, fontweight="bold")
    ax1.set_xlabel("One-Way Latency (ms)", fontsize=10.5, fontweight="semibold")
    ax1.set_ylabel("Transfer Time (seconds)", fontsize=10.5, fontweight="semibold")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(frameon=True, fontsize=8.5)

    # 2. Loss Sweep Goodput Collapse
    for fs in [100, 200]:
        c_col = "#1f77b4" if fs == 100 else "#02818a"
        r_col = "#d62728" if fs == 100 else "#990000"
        m_c = "o" if fs == 100 else "s"
        m_r = "^" if fs == 100 else "v"
        bits = fs * 8.0

        if cubic_loss and fs in cubic_loss:
            s_c = cubic_loss[fs]
            losses = [x["param_val"] for x in s_c]
            gps = [(bits / x["metrics"]["direct_mean"]) for x in s_c]
            ax2.plot(losses, gps, f"-{m_c}", color=c_col, linewidth=2, label=f"CUBIC ({fs}MB)")

        if reno_loss and fs in reno_loss:
            s_r = reno_loss[fs]
            losses = [x["param_val"] for x in s_r]
            gps = [(bits / x["metrics"]["direct_mean"]) for x in s_r]
            ax2.plot(losses, gps, f"--{m_r}", color=r_col, linewidth=2, label=f"Reno ({fs}MB)")

    ax2.set_title("(b) Packet Loss: Goodput Collapse", fontsize=11.5, fontweight="bold")
    ax2.set_xlabel("Packet Loss Rate (%)", fontsize=10.5, fontweight="semibold")
    ax2.set_ylabel("Effective Goodput (Mbit/s)", fontsize=10.5, fontweight="semibold")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(frameon=True, fontsize=8.5)

    # 3. Jitter Sweep Overhead Stability
    for fs in [100, 200]:
        c_col = "#1f77b4" if fs == 100 else "#02818a"
        r_col = "#d62728" if fs == 100 else "#990000"
        m_c = "o" if fs == 100 else "s"
        m_r = "^" if fs == 100 else "v"

        if cubic_jitter and fs in cubic_jitter:
            s_c = cubic_jitter[fs]
            ax3.errorbar([x["param_val"] for x in s_c], [x["metrics"]["diff_mean"] for x in s_c],
                         yerr=[x["metrics"]["diff_std"] for x in s_c], fmt=f"-{m_c}", color=c_col,
                         linewidth=2, capsize=3, label=f"CUBIC ΔT ({fs}MB)")

        if reno_jitter and fs in reno_jitter:
            s_r = reno_jitter[fs]
            ax3.errorbar([x["param_val"] for x in s_r], [x["metrics"]["diff_mean"] for x in s_r],
                         yerr=[x["metrics"]["diff_std"] for x in s_r], fmt=f"--{m_r}", color=r_col,
                         linewidth=2, capsize=3, label=f"Reno ΔT ({fs}MB)")

    ax3.set_title("(c) Jitter: Overhead Invariance", fontsize=11.5, fontweight="bold")
    ax3.set_xlabel("Delay Jitter (± ms)", fontsize=10.5, fontweight="semibold")
    ax3.set_ylabel("Handover Overhead ΔT (seconds)", fontsize=10.5, fontweight="semibold")
    ax3.grid(True, linestyle="--", alpha=0.5)
    ax3.legend(frameon=True, fontsize=8.5)

    plt.suptitle("Consolidated Empirical Evaluation Across Impairment Sweeps (TCP CUBIC vs. TCP Reno)", fontsize=13.5, fontweight="bold", y=0.98)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"Saved: {output_file}")


def plot_protocol_advantage(cubic_latency, reno_latency, cubic_loss, reno_loss, output_file):
    """
    Plots the relative performance advantage of CUBIC over Reno:
    Advantage (%) = [(T_reno - T_cubic) / T_cubic] * 100%
    across Latency and Packet Loss rates.
    """
    if not (cubic_latency and reno_latency):
        print("Skipping plot_protocol_advantage: Latency comparison data incomplete.")
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    # Panel 1: CUBIC Advantage across Latencies
    for fs in [100, 200]:
        color = "#1f77b4" if fs == 100 else "#ff7f0e"
        marker = "o" if fs == 100 else "s"

        c_times = {x["param_val"]: x["metrics"]["direct_mean"] for x in cubic_latency.get(fs, [])}
        r_times = {x["param_val"]: x["metrics"]["direct_mean"] for x in reno_latency.get(fs, [])}

        common_lats = sorted(set(c_times.keys()) & set(r_times.keys()))
        adv_pct = [((r_times[l] - c_times[l]) / c_times[l]) * 100.0 for l in common_lats]

        ax1.plot(common_lats, adv_pct, f"-{marker}", color=color, linewidth=2.2, markersize=7, label=f"{fs} MB Payload")

        for l, adv in zip(common_lats, adv_pct):
            offset = 7 if fs == 100 else -14
            ax1.annotate(f"+{adv:.1f}%", (l, adv), textcoords="offset points", xytext=(0, offset),
                         ha='center', fontsize=8, fontweight='bold', color=color)

    ax1.set_title("CUBIC Speedup Advantage over Reno vs. Latency", fontsize=12, fontweight="bold")
    ax1.set_xlabel("One-Way Latency (ms)", fontsize=11, fontweight="semibold")
    ax1.set_ylabel("CUBIC Advantage [% Faster than Reno]", fontsize=11, fontweight="semibold")
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(frameon=True, fontsize=10)

    # Panel 2: Completion Time Ratio under Packet Loss
    if cubic_loss and reno_loss:
        for fs in [100, 200]:
            color = "#1f77b4" if fs == 100 else "#ff7f0e"
            marker = "o" if fs == 100 else "s"

            c_times = {x["param_val"]: x["metrics"]["direct_mean"] for x in cubic_loss.get(fs, [])}
            r_times = {x["param_val"]: x["metrics"]["direct_mean"] for x in reno_loss.get(fs, [])}

            common_losses = sorted(set(c_times.keys()) & set(r_times.keys()))
            ratio = [r_times[ls] / c_times[ls] for ls in common_losses]

            ax2.plot(common_losses, ratio, f"-{marker}", color=color, linewidth=2.2, markersize=7, label=f"{fs} MB Payload")

        ax2.axhline(1.0, color='gray', linestyle='--', linewidth=1.2, label='Parity (Ratio = 1.0)')
        ax2.set_title("Transfer Time Ratio (T_Reno / T_CUBIC) under Packet Loss", fontsize=12, fontweight="bold")
        ax2.set_xlabel("Packet Loss Rate (%)", fontsize=11, fontweight="semibold")
        ax2.set_ylabel("Time Ratio (T_Reno / T_CUBIC)", fontsize=11, fontweight="semibold")
        ax2.grid(True, linestyle="--", alpha=0.6)
        ax2.legend(frameon=True, fontsize=10)

    plt.suptitle("Protocol Divergence Analysis: TCP CUBIC vs. TCP Reno", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"Saved: {output_file}")


def plot_latency_linear_model(cubic_latency, reno_latency, output_file):
    """
    Plots the empirical Handover Scaling Law:
    Delta T = m * Latency + c
    with least-squares linear regression fit and R^2 score.
    """
    if not cubic_latency:
        return

    plt.figure(figsize=(9, 5.5), dpi=300)

    # 1. CUBIC linear fit across all payload sizes
    all_lats_c = []
    all_ovhd_c = []
    for fs in [100, 200]:
        if fs in cubic_latency:
            for item in cubic_latency[fs]:
                all_lats_c.append(item["param_val"])
                all_ovhd_c.append(item["metrics"]["diff_mean"])

    if all_lats_c:
        x_c = np.array(all_lats_c)
        y_c = np.array(all_ovhd_c)
        m_c, c_c = np.polyfit(x_c, y_c, 1)
        r2_c = 1.0 - (np.sum((y_c - (m_c * x_c + c_c))**2) / np.sum((y_c - np.mean(y_c))**2))

        # Scatter points for CUBIC
        plt.scatter(all_lats_c[:len(all_lats_c)//2], all_ovhd_c[:len(all_ovhd_c)//2],
                    color='#1f77b4', s=60, marker='o', label='CUBIC (100 MB Observed)', zorder=4)
        plt.scatter(all_lats_c[len(all_lats_c)//2:], all_ovhd_c[len(all_ovhd_c)//2:],
                    color='#02818a', s=60, marker='s', label='CUBIC (200 MB Observed)', zorder=4)

        # Regression line for CUBIC
        x_line = np.linspace(min(all_lats_c), max(all_lats_c), 100)
        plt.plot(x_line, m_c * x_line + c_c, '-', color='#1f77b4', linewidth=2.2,
                 label=f'CUBIC Fit: ΔT = {m_c:.3f}·L + {c_c:.2f} s (R²={r2_c:.3f})')

    # 2. Reno linear fit if available
    all_lats_r = []
    all_ovhd_r = []
    if reno_latency:
        for fs in [100, 200]:
            if fs in reno_latency:
                for item in reno_latency[fs]:
                    all_lats_r.append(item["param_val"])
                    all_ovhd_r.append(item["metrics"]["diff_mean"])

        if all_lats_r:
            x_r = np.array(all_lats_r)
            y_r = np.array(all_ovhd_r)
            m_r, c_r = np.polyfit(x_r, y_r, 1)
            r2_r = 1.0 - (np.sum((y_r - (m_r * x_r + c_r))**2) / np.sum((y_r - np.mean(y_r))**2))

            plt.scatter(all_lats_r[:len(all_lats_r)//2], all_ovhd_r[:len(all_ovhd_r)//2],
                        color='#d62728', s=55, marker='^', label='Reno (100 MB Observed)', zorder=4)
            plt.scatter(all_lats_r[len(all_lats_r)//2:], all_ovhd_r[len(all_ovhd_r)//2:],
                        color='#990000', s=55, marker='v', label='Reno (200 MB Observed)', zorder=4)

            plt.plot(x_line, m_r * x_line + c_r, '--', color='#d62728', linewidth=2.0,
                     label=f'Reno Fit: ΔT = {m_r:.3f}·L + {c_r:.2f} s (R²={r2_r:.3f})')

    plt.title("Empirical Handover Scaling Law: Linear RTT Dependency Model", fontsize=13, fontweight='bold', pad=12)
    plt.xlabel("One-Way Propagation Delay (Latency L in ms)", fontsize=11, fontweight='semibold')
    plt.ylabel("Handover Overhead ΔT (seconds)", fontsize=11, fontweight='semibold')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=9.5)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"Saved: {output_file}")


def plot_loss_goodput_parity(cubic_loss, reno_loss, output_file):
    """
    Plots Baseline Goodput vs. Migration Goodput across packet loss rates (0.1% to 5.0%),
    demonstrating handover overhead negligibility under loss:
    retrying dropped packets completely dwarfs IP-layer handover overhead.
    """
    if not cubic_loss and not reno_loss:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    # Panel 1: TCP CUBIC Goodput Parity
    if cubic_loss:
        for fs in [100, 200]:
            color = "#1f77b4" if fs == 100 else "#02818a"
            m = "o" if fs == 100 else "s"
            bits = fs * 8.0

            series = cubic_loss.get(fs, [])
            losses = [x["param_val"] for x in series]
            gp_base = [(bits / x["metrics"]["direct_mean"]) for x in series]
            gp_migr = [(bits / x["metrics"]["migrate_mean"]) for x in series]

            ax1.plot(losses, gp_base, f"-{m}", color=color, linewidth=2.2, label=f"Baseline ({fs} MB)")
            ax1.plot(losses, gp_migr, f":{m}", color=color, linewidth=2.2, alpha=0.8, label=f"Migration ({fs} MB)")

    ax1.set_title("TCP CUBIC: Baseline vs. Migration Goodput Parity", fontsize=11.5, fontweight="bold")
    ax1.set_xlabel("Packet Loss Rate (%)", fontsize=10.5, fontweight="semibold")
    ax1.set_ylabel("Effective Goodput (Mbit/s)", fontsize=10.5, fontweight="semibold")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(frameon=True, fontsize=9)

    # Panel 2: TCP Reno Goodput Parity
    if reno_loss:
        for fs in [100, 200]:
            color = "#d62728" if fs == 100 else "#990000"
            m = "^" if fs == 100 else "v"
            bits = fs * 8.0

            series = reno_loss.get(fs, [])
            losses = [x["param_val"] for x in series]
            gp_base = [(bits / x["metrics"]["direct_mean"]) for x in series]
            gp_migr = [(bits / x["metrics"]["migrate_mean"]) for x in series]

            ax2.plot(losses, gp_base, f"-{m}", color=color, linewidth=2.2, label=f"Baseline ({fs} MB)")
            ax2.plot(losses, gp_migr, f":{m}", color=color, linewidth=2.2, alpha=0.8, label=f"Migration ({fs} MB)")

    ax2.set_title("TCP Reno: Baseline vs. Migration Goodput Parity", fontsize=11.5, fontweight="bold")
    ax2.set_xlabel("Packet Loss Rate (%)", fontsize=10.5, fontweight="semibold")
    ax2.set_ylabel("Effective Goodput (Mbit/s)", fontsize=10.5, fontweight="semibold")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(frameon=True, fontsize=9)

    plt.suptitle("Handover Overhead Negligibility under Loss: Baseline vs. Migration Goodput Parity", fontsize=13.5, fontweight="bold", y=0.98)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"Saved: {output_file}")


# ==============================================================================
# MAIN DRIVER
# ==============================================================================

def create_all_plots(results_dir="./RESULTS", output_dir="./PLOTS"):
    """
    Coordinates loading all results CSVs from results_dir and generating
    both baseline and sweep figures into output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    print(f"Reading CSV results from : {os.path.abspath(results_dir)}")
    print(f"Saving generated plots to: {os.path.abspath(output_dir)}\n")

    # 1. Baseline analysis data
    cubic_csv = os.path.join(results_dir, "baseline_cubic_all_results.csv")
    reno_csv = os.path.join(results_dir, "reno_all_results.csv")

    cubic_data = load_baseline_results(cubic_csv)
    reno_data = load_baseline_results(reno_csv)

    print("--- [1/4] Generating Baseline Scaling Figures (50 MB - 500 MB) ---")
    plot_transfer_time(cubic_data, reno_data, os.path.join(output_dir, "plot_transfer_time.png"))
    plot_handover_overhead(cubic_data, reno_data, os.path.join(output_dir, "plot_handover_overhead.png"))
    plot_relative_decay(cubic_data, reno_data, os.path.join(output_dir, "plot_relative_decay.png"))
    plot_baseline_throughput(cubic_data, reno_data, os.path.join(output_dir, "plot_baseline_throughput.png"))

    # 2. Parametric sweeps data (CUBIC and Reno)
    print("\n--- [2/4] Generating Parametric Sweep Figures (CUBIC vs Reno) ---")
    cubic_latency = load_sweep_series(results_dir, "latency", "cubic")
    reno_latency = load_sweep_series(results_dir, "latency", "reno")

    cubic_loss = load_sweep_series(results_dir, "loss", "cubic")
    reno_loss = load_sweep_series(results_dir, "loss", "reno")

    cubic_jitter = load_sweep_series(results_dir, "jitter", "cubic")
    reno_jitter = load_sweep_series(results_dir, "jitter", "reno")

    plot_latency_sweep(cubic_latency, reno_latency, os.path.join(output_dir, "plot_latency_sweep.png"))
    plot_loss_sweep(cubic_loss, reno_loss, os.path.join(output_dir, "plot_loss_sweep.png"))
    plot_jitter_sweep(cubic_jitter, reno_jitter, os.path.join(output_dir, "plot_jitter_sweep.png"))

    # 3. Consolidated & Analytical Models
    print("\n--- [3/4] Generating Analytical & Model Figures ---")
    plot_impairments_overview(cubic_latency, reno_latency, cubic_loss, reno_loss, cubic_jitter, reno_jitter,
                              os.path.join(output_dir, "plot_impairments_overview.png"))
    plot_protocol_advantage(cubic_latency, reno_latency, cubic_loss, reno_loss,
                            os.path.join(output_dir, "plot_protocol_advantage.png"))
    plot_latency_linear_model(cubic_latency, reno_latency,
                              os.path.join(output_dir, "plot_latency_linear_model.png"))
    plot_loss_goodput_parity(cubic_loss, reno_loss,
                             os.path.join(output_dir, "plot_loss_goodput_parity.png"))

    print("\n[4/4] All 11 figures generated successfully!")


def main():
    parser = argparse.ArgumentParser(description="Generate publication-quality experiment plots from CSV results.")
    parser.add_argument("--results-dir", default="./RESULTS", help="Path to RESULTS directory containing CSV files")
    parser.add_argument("--output-dir", default="./PLOTS", help="Directory where generated plots will be saved")
    args = parser.parse_args()

    create_all_plots(results_dir=args.results_dir, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
