#!/usr/bin/env python3
"""
plot_results.py

Standalone visualization script for experiment results.
Reads statistical CSV tables from the ./RESULTS directory and generates
high-resolution publication-quality plots comparing TCP CUBIC and TCP Reno.

Generated figures:
  1. plot_transfer_time.png       - Baseline: Completion time scaling (CUBIC vs Reno)
  2. plot_handover_overhead.png   - Baseline: Invariant handover overhead (Delta T)
  3. plot_relative_decay.png      - Baseline: Hyperbolic relative overhead penalty decay (rho)
  4. plot_latency_sweep.png       - Latency Sweep: Completion time & overhead vs RTT latency (CUBIC vs Reno)
  5. plot_loss_sweep.png          - Loss Sweep: Completion time & effective goodput vs packet loss (CUBIC vs Reno)
  6. plot_jitter_sweep.png        - Jitter Sweep: Completion time & overhead vs delay jitter (CUBIC vs Reno)
"""

import os
import re
import csv
import glob
import argparse
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

    # Visual palettes
    # CUBIC: Blue/Teal tones | Reno: Red/Crimson tones
    colors_cubic = {100: "#1f77b4", 200: "#02818a"}
    colors_reno = {100: "#d62728", 200: "#990000"}
    markers_cubic = {100: "o", 200: "s"}
    markers_reno = {100: "^", 200: "v"}

    # Common payload sizes
    all_sizes = sorted(set(list(cubic_data.keys()) + list(reno_data.keys() if reno_data else [])))

    for fs in all_sizes:
        # Plot CUBIC series
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

        # Plot Reno series
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

    print("--- Generating Baseline Figures (CUBIC vs Reno) ---")
    plot_transfer_time(cubic_data, reno_data, os.path.join(output_dir, "plot_transfer_time.png"))
    plot_handover_overhead(cubic_data, reno_data, os.path.join(output_dir, "plot_handover_overhead.png"))
    plot_relative_decay(cubic_data, reno_data, os.path.join(output_dir, "plot_relative_decay.png"))

    # 2. Parametric sweeps data (CUBIC and Reno)
    print("\n--- Generating Parametric Sweep Figures (CUBIC vs Reno) ---")
    cubic_latency = load_sweep_series(results_dir, "latency", "cubic")
    reno_latency = load_sweep_series(results_dir, "latency", "reno")

    cubic_loss = load_sweep_series(results_dir, "loss", "cubic")
    reno_loss = load_sweep_series(results_dir, "loss", "reno")

    cubic_jitter = load_sweep_series(results_dir, "jitter", "cubic")
    reno_jitter = load_sweep_series(results_dir, "jitter", "reno")

    plot_latency_sweep(cubic_latency, reno_latency, os.path.join(output_dir, "plot_latency_sweep.png"))
    plot_loss_sweep(cubic_loss, reno_loss, os.path.join(output_dir, "plot_loss_sweep.png"))
    plot_jitter_sweep(cubic_jitter, reno_jitter, os.path.join(output_dir, "plot_jitter_sweep.png"))

    print("\nAll plots generated successfully!")


def main():
    parser = argparse.ArgumentParser(description="Generate publication-quality experiment plots from CSV results.")
    parser.add_argument("--results-dir", default="./RESULTS", help="Path to RESULTS directory containing CSV files")
    parser.add_argument("--output-dir", default="./PLOTS", help="Directory where generated plots will be saved")
    args = parser.parse_args()

    create_all_plots(results_dir=args.results_dir, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
