#!/usr/bin/env python3
"""
plot_results.py

Standalone visualization script for experiment results.
Reads statistical CSV tables from the ./RESULTS directory and generates
high-resolution publication-quality plots.

Generated figures:
  1. plot_transfer_time.png       - Baseline: Completion time scaling (CUBIC vs Reno)
  2. plot_handover_overhead.png   - Baseline: Invariant handover overhead (Delta T)
  3. plot_relative_decay.png      - Baseline: Hyperbolic relative overhead penalty decay (rho)
  4. plot_latency_sweep.png       - Latency Sweep: Completion time & overhead vs RTT latency
  5. plot_loss_sweep.png          - Loss Sweep: Completion time & effective goodput vs packet loss
  6. plot_jitter_sweep.png        - Jitter Sweep: Completion time & overhead vs delay jitter
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


def load_sweep_series(results_dir, sweep_type):
    """
    Finds and parses all 'cubic_{sweep_type}_*_all_results.csv' files in results_dir.

    Parameters:
        results_dir (str): Directory containing the CSV tables.
        sweep_type (str): 'latency', 'loss', or 'jitter'.

    Returns:
        dict: Mapping file_size_mb (e.g., 100, 200) -> list of dicts:
              [{'param_str': '10ms', 'param_val': 10.0, 'metrics': {...}}, ...]
              sorted by param_val ascending.
    """
    pattern = os.path.join(results_dir, f"cubic_{sweep_type}_*_all_results.csv")
    csv_files = glob.glob(pattern)
    if not csv_files:
        return {}

    by_file_size = {}

    for filepath in csv_files:
        filename = os.path.basename(filepath)
        # Match pattern: cubic_{sweep_type}_{param_str}_all_results.csv
        prefix = f"cubic_{sweep_type}_"
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
# PARAMETRIC SWEEPS PLOTTING FUNCTIONS
# ==============================================================================

def plot_latency_sweep(sweep_data, output_file):
    """
    Plots Latency Sweep:
    - Panel 1: Transfer Completion Time vs. One-Way Latency for 100 MB and 200 MB.
    - Panel 2: Handover Overhead vs. One-Way Latency (Mean ± Std).
    """
    if not sweep_data:
        print("Skipping plot_latency_sweep: No latency sweep data found.")
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)
    colors = {100: "#1f77b4", 200: "#ff7f0e", 50: "#2ca02c"}
    markers = {100: "o", 200: "s", 50: "^"}

    for fs in sorted(sweep_data.keys()):
        series = sweep_data[fs]
        lats = [x["param_val"] for x in series]
        b_means = [x["metrics"]["direct_mean"] for x in series]
        m_means = [x["metrics"]["migrate_mean"] for x in series]
        o_means = [x["metrics"]["diff_mean"] for x in series]
        o_stds = [x["metrics"]["diff_std"] for x in series]

        c = colors.get(fs, "#333333")
        m = markers.get(fs, "o")

        # Panel 1: Completion Time
        ax1.plot(lats, b_means, f"-{m}", color=c, linewidth=2, label=f"Baseline ({fs} MB)")
        ax1.plot(lats, m_means, f"--{m}", color=c, linewidth=2, alpha=0.7, label=f"Migration ({fs} MB)")

        # Panel 2: Overhead
        ax2.errorbar(lats, o_means, yerr=o_stds, fmt=f"-{m}", color=c, linewidth=2, capsize=4, label=f"Overhead ({fs} MB)")

    ax1.set_title("Completion Time vs. Latency", fontsize=12, fontweight="bold")
    ax1.set_xlabel("One-Way Latency (ms)", fontsize=11, fontweight="semibold")
    ax1.set_ylabel("Completion Time (seconds)", fontsize=11, fontweight="semibold")
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(frameon=True, fontsize=9)

    ax2.set_title("Handover Overhead vs. Latency", fontsize=12, fontweight="bold")
    ax2.set_xlabel("One-Way Latency (ms)", fontsize=11, fontweight="semibold")
    ax2.set_ylabel("Handover Overhead ΔT (seconds)", fontsize=11, fontweight="semibold")
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(frameon=True, fontsize=9)

    plt.suptitle("Latency Sweep Impact on Migration Performance (TCP CUBIC)", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"Saved: {output_file}")


def plot_loss_sweep(sweep_data, output_file):
    """
    Plots Packet Loss Sweep:
    - Panel 1: Transfer Completion Time vs. Packet Loss Rate.
    - Panel 2: Effective Goodput (Mbit/s = File_Size_bits / Time_sec) vs. Packet Loss Rate.
    """
    if not sweep_data:
        print("Skipping plot_loss_sweep: No loss sweep data found.")
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)
    colors = {100: "#1f77b4", 200: "#ff7f0e", 50: "#2ca02c"}
    markers = {100: "o", 200: "s", 50: "^"}

    for fs in sorted(sweep_data.keys()):
        series = sweep_data[fs]
        losses = [x["param_val"] for x in series]
        b_means = [x["metrics"]["direct_mean"] for x in series]
        m_means = [x["metrics"]["migrate_mean"] for x in series]

        # Calculate effective goodput in Mbit/s
        file_bits = fs * 8.0
        gp_base = [(file_bits / t) if t > 0 else 0 for t in b_means]
        gp_migr = [(file_bits / t) if t > 0 else 0 for t in m_means]

        c = colors.get(fs, "#333333")
        m = markers.get(fs, "o")

        # Panel 1: Completion Time
        ax1.plot(losses, b_means, f"-{m}", color=c, linewidth=2, label=f"Baseline ({fs} MB)")
        ax1.plot(losses, m_means, f"--{m}", color=c, linewidth=2, alpha=0.7, label=f"Migration ({fs} MB)")

        # Panel 2: Goodput
        ax2.plot(losses, gp_base, f"-{m}", color=c, linewidth=2, label=f"Baseline Goodput ({fs} MB)")
        ax2.plot(losses, gp_migr, f"--{m}", color=c, linewidth=2, alpha=0.7, label=f"Migration Goodput ({fs} MB)")

    ax1.set_title("Completion Time vs. Packet Loss", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Packet Loss Rate (%)", fontsize=11, fontweight="semibold")
    ax1.set_ylabel("Completion Time (seconds)", fontsize=11, fontweight="semibold")
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(frameon=True, fontsize=9)

    ax2.set_title("Effective Goodput Degradation", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Packet Loss Rate (%)", fontsize=11, fontweight="semibold")
    ax2.set_ylabel("Effective Goodput (Mbit/s)", fontsize=11, fontweight="semibold")
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(frameon=True, fontsize=9)

    plt.suptitle("Packet Loss Sweep Impact on Migration Performance (TCP CUBIC)", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"Saved: {output_file}")


def plot_jitter_sweep(sweep_data, output_file):
    """
    Plots Latency Jitter Sweep:
    - Panel 1: Completion Time vs. Latency Jitter for 100 MB and 200 MB.
    - Panel 2: Handover Overhead vs. Latency Jitter (Mean ± Std).
    """
    if not sweep_data:
        print("Skipping plot_jitter_sweep: No jitter sweep data found.")
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)
    colors = {100: "#1f77b4", 200: "#ff7f0e", 50: "#2ca02c"}
    markers = {100: "o", 200: "s", 50: "^"}

    for fs in sorted(sweep_data.keys()):
        series = sweep_data[fs]
        jitters = [x["param_val"] for x in series]
        b_means = [x["metrics"]["direct_mean"] for x in series]
        m_means = [x["metrics"]["migrate_mean"] for x in series]
        o_means = [x["metrics"]["diff_mean"] for x in series]
        o_stds = [x["metrics"]["diff_std"] for x in series]

        c = colors.get(fs, "#333333")
        m = markers.get(fs, "o")

        # Panel 1: Completion Time
        ax1.plot(jitters, b_means, f"-{m}", color=c, linewidth=2, label=f"Baseline ({fs} MB)")
        ax1.plot(jitters, m_means, f"--{m}", color=c, linewidth=2, alpha=0.7, label=f"Migration ({fs} MB)")

        # Panel 2: Overhead
        ax2.errorbar(jitters, o_means, yerr=o_stds, fmt=f"-{m}", color=c, linewidth=2, capsize=4, label=f"Overhead ({fs} MB)")

    ax1.set_title("Completion Time vs. Jitter", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Latency Jitter (± ms)", fontsize=11, fontweight="semibold")
    ax1.set_ylabel("Completion Time (seconds)", fontsize=11, fontweight="semibold")
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(frameon=True, fontsize=9)

    ax2.set_title("Handover Overhead vs. Jitter", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Latency Jitter (± ms)", fontsize=11, fontweight="semibold")
    ax2.set_ylabel("Handover Overhead ΔT (seconds)", fontsize=11, fontweight="semibold")
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(frameon=True, fontsize=9)

    plt.suptitle("Latency Jitter Sweep Impact on Migration Performance (Base Latency: 40ms)", fontsize=14, fontweight="bold", y=0.98)
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

    print("--- Generating Baseline Figures ---")
    plot_transfer_time(cubic_data, reno_data, os.path.join(output_dir, "plot_transfer_time.png"))
    plot_handover_overhead(cubic_data, reno_data, os.path.join(output_dir, "plot_handover_overhead.png"))
    plot_relative_decay(cubic_data, reno_data, os.path.join(output_dir, "plot_relative_decay.png"))

    # 2. Parametric sweeps data
    print("\n--- Generating Parametric Sweep Figures ---")
    latency_data = load_sweep_series(results_dir, "latency")
    loss_data = load_sweep_series(results_dir, "loss")
    jitter_data = load_sweep_series(results_dir, "jitter")

    plot_latency_sweep(latency_data, os.path.join(output_dir, "plot_latency_sweep.png"))
    plot_loss_sweep(loss_data, os.path.join(output_dir, "plot_loss_sweep.png"))
    plot_jitter_sweep(jitter_data, os.path.join(output_dir, "plot_jitter_sweep.png"))

    print("\nAll plots generated successfully!")


def main():
    parser = argparse.ArgumentParser(description="Generate publication-quality experiment plots from CSV results.")
    parser.add_argument("--results-dir", default="./RESULTS", help="Path to RESULTS directory containing CSV files")
    parser.add_argument("--output-dir", default="./PLOTS", help="Directory where generated plots will be saved")
    args = parser.parse_args()

    create_all_plots(results_dir=args.results_dir, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
