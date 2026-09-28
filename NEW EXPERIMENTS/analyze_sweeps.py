#!/usr/bin/env python3
"""
analyze_sweeps.py - Analysis and Visualization Tool for Parametric Sweeps & Profiles

Dedicated to:
- Experiment 3 (Parametric Sweeps: Latency, Packet Loss, and Jitter under TCP CUBIC)
- Future Scenario Profiles (6G Ideal, 5G Congested, LTE Poor)
- Multi-dimensional analysis grouped by impairment type (Latency, Loss, Jitter)
"""

import os
import sys
import glob
import csv
import re
import statistics

# Set headless backend for matplotlib before importing pyplot
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ==============================================================================
# 1. PARSE HELPER FUNCTIONS
# ==============================================================================

def parse_latency_ms(val_str):
    """Extracts numeric millisecond value from strings like '20ms', '0ms'."""
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(val_str))
    return float(m.group(1)) if m else 0.0

def parse_loss_pct(val_str):
    """Extracts numeric percentage value from strings like '0.5%', '1%', '0'."""
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(val_str))
    return float(m.group(1)) if m else 0.0

def parse_jitter_ms(val_str):
    """Extracts numeric millisecond value from strings like '5ms', '0ms'."""
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(val_str))
    return float(m.group(1)) if m else 0.0

# ==============================================================================
# 2. READ CSV FILE & EXTRACT DATA
# ==============================================================================

def read_sweep_csv(filepath):
    """
    Reads a single sweep result CSV file, extracts iterations, and classifies
    the sweep category (latency, loss, jitter, or scenario profile).
    """
    if not os.path.exists(filepath):
        return None

    filename = os.path.basename(filepath)
    if filename.startswith("real_kernel_cwnd_"):
        return None

    baseline_times = []
    migration_times = []
    overhead_times = []
    timestamps = []

    metadata = {
        "filename": filename,
        "filepath": filepath,
        "test_name": filename.replace(".csv", ""),
        "configured_rate": "50mbit",
        "configured_latency": "0ms",
        "configured_jitter": "0ms",
        "configured_loss": "0%",
        "cwnd_mode": "cubic",
        "file_size_mb": 0,
        "sweep_type": "unknown"
    }

    # Classify sweep type from filename
    if "latency_sweep" in filename:
        metadata["sweep_type"] = "latency_sweep"
    elif "loss_sweep" in filename:
        metadata["sweep_type"] = "loss_sweep"
    elif "jitter_sweep" in filename:
        metadata["sweep_type"] = "jitter_sweep"
    elif "profile_" in filename:
        metadata["sweep_type"] = "scenario_profile"

    with open(filepath, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamps.append(row.get("timestamp", ""))

            if not metadata["file_size_mb"]:
                metadata["configured_rate"] = row.get("configured_rate", "50mbit")
                metadata["configured_latency"] = row.get("configured_latency", "0ms")
                metadata["configured_jitter"] = row.get("configured_jitter", "0ms")
                metadata["configured_loss"] = row.get("configured_loss", "0%")
                metadata["cwnd_mode"] = row.get("cwnd_mode", "cubic")
                try:
                    metadata["file_size_mb"] = int(row.get("file_size_mb", 0))
                except ValueError:
                    metadata["file_size_mb"] = 0

            try:
                b_time = float(row.get("baseline_time_sec", 0))
                m_time = float(row.get("migration_time_sec", 0))
                ov_time = float(row.get("overhead_sec", 0))

                baseline_times.append(b_time)
                migration_times.append(m_time)
                overhead_times.append(ov_time)
            except (ValueError, TypeError):
                continue

    if not baseline_times:
        return None

    num_runs = len(baseline_times)
    b_mean = statistics.mean(baseline_times)
    m_mean = statistics.mean(migration_times)
    o_mean = statistics.mean(overhead_times)

    b_std = statistics.stdev(baseline_times) if num_runs > 1 else 0.0
    m_std = statistics.stdev(migration_times) if num_runs > 1 else 0.0
    o_std = statistics.stdev(overhead_times) if num_runs > 1 else 0.0

    rel_ovhd_pct = (o_mean / b_mean * 100.0) if b_mean > 0 else 0.0

    # Calculate effective goodput in Mbit/s
    total_bits = metadata["file_size_mb"] * 8 * 1024 * 1024
    goodput_base_mbps = (total_bits / (b_mean * 1e6)) if b_mean > 0 else 0.0
    goodput_migr_mbps = (total_bits / (m_mean * 1e6)) if m_mean > 0 else 0.0

    # Parsed numeric values for clean sorting
    metadata["latency_ms"] = parse_latency_ms(metadata["configured_latency"])
    metadata["loss_pct"] = parse_loss_pct(metadata["configured_loss"])
    metadata["jitter_ms"] = parse_jitter_ms(metadata["configured_jitter"])

    return {
        "metadata": metadata,
        "num_iterations": num_runs,
        "stats": {
            "baseline_mean": b_mean,
            "baseline_std": b_std,
            "migration_mean": m_mean,
            "migration_std": m_std,
            "overhead_mean": o_mean,
            "overhead_std": o_std,
            "relative_overhead_pct": rel_ovhd_pct,
            "goodput_base_mbps": goodput_base_mbps,
            "goodput_migr_mbps": goodput_migr_mbps
        }
    }

# ==============================================================================
# 3. LOAD & GROUP EXPERIMENT RESULTS
# ==============================================================================

def load_sweep_results(exp_dir):
    """
    Scans the results directory and groups items by sweep_type.
    """
    results_dir = os.path.join(exp_dir, "results") if os.path.isdir(os.path.join(exp_dir, "results")) else exp_dir
    if not os.path.exists(results_dir):
        print(f"Error: Results directory does not exist: {results_dir}")
        return {}

    csv_files = sorted(glob.glob(os.path.join(results_dir, "*.csv")))
    grouped = {
        "latency_sweep": [],
        "loss_sweep": [],
        "jitter_sweep": [],
        "scenario_profile": [],
        "other": []
    }

    for filepath in csv_files:
        if os.path.basename(filepath).startswith("real_kernel_cwnd_"):
            continue
        data = read_sweep_csv(filepath)
        if data:
            stype = data["metadata"]["sweep_type"]
            if stype in grouped:
                grouped[stype].append(data)
            else:
                grouped["other"].append(data)

    return grouped

# ==============================================================================
# 4. PRINT FORMATTED CATEGORY TABLES
# ==============================================================================

def print_latency_table(items):
    if not items:
        return
    # Sort by file size, then by latency numeric value
    sorted_items = sorted(items, key=lambda x: (x["metadata"]["file_size_mb"], x["metadata"]["latency_ms"]))

    print("\n" + "=" * 115)
    print("⏱️  LATENCY SWEEP RESULTS (Loss: 0%, Jitter: 0ms, Rate: 50Mbit/s)")
    print("=" * 115)
    header = (
        f"{'One-Way Latency':<16} | {'RTT (approx)':<14} | {'Size':<6} | "
        f"{'Baseline (s)':<16} | {'Migration (s)':<16} | {'Overhead (s)':<16} | {'Rel Ovhd':<8}"
    )
    print(header)
    print("-" * 115)

    for item in sorted_items:
        m = item["metadata"]
        s = item["stats"]
        lat_str = f"{m['latency_ms']:.0f} ms"
        rtt_str = f"~{m['latency_ms']*2:.0f} ms"
        size_str = f"{m['file_size_mb']} MB"
        b_str = f"{s['baseline_mean']:7.3f} ± {s['baseline_std']:5.3f}"
        m_str = f"{s['migration_mean']:7.3f} ± {s['migration_std']:5.3f}"
        o_str = f"{s['overhead_mean']:7.3f} ± {s['overhead_std']:5.3f}"
        rel_str = f"{s['relative_overhead_pct']:6.2f}%"

        print(f"{lat_str:<16} | {rtt_str:<14} | {size_str:<6} | {b_str:<16} | {m_str:<16} | {o_str:<16} | {rel_str:<8}")

    print("=" * 115)

def print_loss_table(items):
    if not items:
        return
    sorted_items = sorted(items, key=lambda x: (x["metadata"]["file_size_mb"], x["metadata"]["loss_pct"]))

    print("\n" + "=" * 115)
    print("📉 PACKET LOSS SWEEP RESULTS (Latency: 20ms, Jitter: 0ms, Rate: 50Mbit/s)")
    print("=" * 115)
    header = (
        f"{'Packet Loss':<14} | {'Size':<6} | {'Goodput Base':<14} | "
        f"{'Baseline (s)':<16} | {'Migration (s)':<16} | {'Overhead (s)':<16} | {'Rel Ovhd':<8}"
    )
    print(header)
    print("-" * 115)

    for item in sorted_items:
        m = item["metadata"]
        s = item["stats"]
        loss_str = f"{m['loss_pct']}%"
        size_str = f"{m['file_size_mb']} MB"
        gp_str = f"{s['goodput_base_mbps']:5.2f} Mbps"
        b_str = f"{s['baseline_mean']:7.3f} ± {s['baseline_std']:5.3f}"
        m_str = f"{s['migration_mean']:7.3f} ± {s['migration_std']:5.3f}"
        o_str = f"{s['overhead_mean']:7.3f} ± {s['overhead_std']:5.3f}"
        rel_str = f"{s['relative_overhead_pct']:6.2f}%"

        print(f"{loss_str:<14} | {size_str:<6} | {gp_str:<14} | {b_str:<16} | {m_str:<16} | {o_str:<16} | {rel_str:<8}")

    print("=" * 115)

def print_jitter_table(items):
    if not items:
        return
    sorted_items = sorted(items, key=lambda x: (x["metadata"]["file_size_mb"], x["metadata"]["jitter_ms"]))

    print("\n" + "=" * 115)
    print("🔀 LATENCY JITTER SWEEP RESULTS (Latency: 40ms, Loss: 0%, Rate: 50Mbit/s)")
    print("=" * 115)
    header = (
        f"{'Jitter':<14} | {'Base Latency':<14} | {'Size':<6} | "
        f"{'Baseline (s)':<16} | {'Migration (s)':<16} | {'Overhead (s)':<16} | {'Rel Ovhd':<8}"
    )
    print(header)
    print("-" * 115)

    for item in sorted_items:
        m = item["metadata"]
        s = item["stats"]
        jit_str = f"±{m['jitter_ms']:.0f} ms"
        base_lat = f"{m['latency_ms']:.0f} ms"
        size_str = f"{m['file_size_mb']} MB"
        b_str = f"{s['baseline_mean']:7.3f} ± {s['baseline_std']:5.3f}"
        m_str = f"{s['migration_mean']:7.3f} ± {s['migration_std']:5.3f}"
        o_str = f"{s['overhead_mean']:7.3f} ± {s['overhead_std']:5.3f}"
        rel_str = f"{s['relative_overhead_pct']:6.2f}%"

        print(f"{jit_str:<14} | {base_lat:<14} | {size_str:<6} | {b_str:<16} | {m_str:<16} | {o_str:<16} | {rel_str:<8}")

    print("=" * 115)

# ==============================================================================
# 5. SPECIALIZED SWEEP PLOTTING FUNCTIONS
# ==============================================================================

def plot_latency_sweep(items, output_png_path):
    """
    Plots Latency Sweep:
    - Panel A: Completion Time vs. Latency for all file sizes
    - Panel B: Handover Overhead vs. Latency (Linear Scaling verification)
    """
    if not items:
        return

    # Group by file size
    by_size = {}
    for item in items:
        fs = item["metadata"]["file_size_mb"]
        by_size.setdefault(fs, []).append(item)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    colors = {100: "#2b5c8f", 200: "#d95f02", 50: "#27ae60"}
    markers = {100: "o", 200: "s", 50: "^"}

    for fs, series in sorted(by_size.items()):
        sorted_series = sorted(series, key=lambda x: x["metadata"]["latency_ms"])
        lats = [x["metadata"]["latency_ms"] for x in sorted_series]
        b_means = [x["stats"]["baseline_mean"] for x in sorted_series]
        m_means = [x["stats"]["migration_mean"] for x in sorted_series]
        o_means = [x["stats"]["overhead_mean"] for x in sorted_series]
        o_stds = [x["stats"]["overhead_std"] for x in sorted_series]

        c = colors.get(fs, "#333333")
        m = markers.get(fs, "o")

        # Panel A: Completion Time
        ax1.plot(lats, b_means, f"-{m}", color=c, linewidth=2, label=f"Baseline ({fs}MB)")
        ax1.plot(lats, m_means, f":{m}", color=c, linewidth=2, alpha=0.7, label=f"Migration ({fs}MB)")

        # Panel B: Handover Overhead
        ax2.errorbar(lats, o_means, yerr=o_stds, fmt=f"-{m}", color=c, linewidth=2.2, capsize=4, label=f"Overhead ({fs}MB)")

    ax1.set_xlabel("One-Way Network Latency (ms)", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Transfer Time (seconds)", fontsize=12, fontweight="bold")
    ax1.set_title("Latency Impact on Transfer Times (TCP CUBIC)", fontsize=13, fontweight="bold", pad=12)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(fontsize=10)

    ax2.set_xlabel("One-Way Network Latency (ms)", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Handover Overhead (seconds)", fontsize=12, fontweight="bold")
    ax2.set_title("Handover Overhead Scaling with Latency", fontsize=13, fontweight="bold", pad=12)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(fontsize=10)

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_png_path)), exist_ok=True)
    plt.savefig(output_png_path, dpi=300)
    plt.close(fig)
    print(f"📈 Latency Sweep Analysis Chart saved: {output_png_path}")

def plot_loss_sweep(items, output_png_path):
    """
    Plots Packet Loss Sweep:
    - Panel A: Completion Time vs. Loss Rate
    - Panel B: Effective Goodput (Mbps) vs. Loss Rate
    """
    if not items:
        return

    by_size = {}
    for item in items:
        fs = item["metadata"]["file_size_mb"]
        by_size.setdefault(fs, []).append(item)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    colors = {100: "#2b5c8f", 200: "#d95f02", 50: "#27ae60"}
    markers = {100: "o", 200: "s", 50: "^"}

    for fs, series in sorted(by_size.items()):
        sorted_series = sorted(series, key=lambda x: x["metadata"]["loss_pct"])
        losses = [x["metadata"]["loss_pct"] for x in sorted_series]
        b_means = [x["stats"]["baseline_mean"] for x in sorted_series]
        m_means = [x["stats"]["migration_mean"] for x in sorted_series]
        gp_base = [x["stats"]["goodput_base_mbps"] for x in sorted_series]
        gp_migr = [x["stats"]["goodput_migr_mbps"] for x in sorted_series]

        c = colors.get(fs, "#333333")
        m = markers.get(fs, "o")

        # Panel A: Completion Time
        ax1.plot(losses, b_means, f"-{m}", color=c, linewidth=2, label=f"Baseline ({fs}MB)")
        ax1.plot(losses, m_means, f":{m}", color=c, linewidth=2, alpha=0.7, label=f"Migration ({fs}MB)")

        # Panel B: Goodput Collapse
        ax2.plot(losses, gp_base, f"-{m}", color=c, linewidth=2, label=f"Goodput Baseline ({fs}MB)")
        ax2.plot(losses, gp_migr, f":{m}", color=c, linewidth=2, alpha=0.7, label=f"Goodput Migration ({fs}MB)")

    ax1.set_xlabel("Packet Loss Rate (%)", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Completion Time (seconds)", fontsize=12, fontweight="bold")
    ax1.set_title("Packet Loss Impact on Transfer Completion", fontsize=13, fontweight="bold", pad=12)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(fontsize=10)

    ax2.set_xlabel("Packet Loss Rate (%)", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Effective Goodput (Mbit/s)", fontsize=12, fontweight="bold")
    ax2.set_title("Goodput Degradation under Loss", fontsize=13, fontweight="bold", pad=12)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(fontsize=10)

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_png_path)), exist_ok=True)
    plt.savefig(output_png_path, dpi=300)
    plt.close(fig)
    print(f"📈 Loss Sweep Analysis Chart saved: {output_png_path}")

def plot_jitter_sweep(items, output_png_path):
    """
    Plots Jitter Sweep:
    - Panel A: Completion Time vs. Jitter
    - Panel B: Overhead vs. Jitter
    """
    if not items:
        return

    by_size = {}
    for item in items:
        fs = item["metadata"]["file_size_mb"]
        by_size.setdefault(fs, []).append(item)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    colors = {100: "#2b5c8f", 200: "#d95f02", 50: "#27ae60"}
    markers = {100: "o", 200: "s", 50: "^"}

    for fs, series in sorted(by_size.items()):
        sorted_series = sorted(series, key=lambda x: x["metadata"]["jitter_ms"])
        jitters = [x["metadata"]["jitter_ms"] for x in sorted_series]
        b_means = [x["stats"]["baseline_mean"] for x in sorted_series]
        m_means = [x["stats"]["migration_mean"] for x in sorted_series]
        o_means = [x["stats"]["overhead_mean"] for x in sorted_series]
        o_stds = [x["stats"]["overhead_std"] for x in sorted_series]

        c = colors.get(fs, "#333333")
        m = markers.get(fs, "o")

        ax1.plot(jitters, b_means, f"-{m}", color=c, linewidth=2, label=f"Baseline ({fs}MB)")
        ax1.plot(jitters, m_means, f":{m}", color=c, linewidth=2, alpha=0.7, label=f"Migration ({fs}MB)")

        ax2.errorbar(jitters, o_means, yerr=o_stds, fmt=f"-{m}", color=c, linewidth=2.2, capsize=4, label=f"Overhead ({fs}MB)")

    ax1.set_xlabel("Latency Jitter (± ms)", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Transfer Time (seconds)", fontsize=12, fontweight="bold")
    ax1.set_title("Jitter Impact on Completion Time (Base Latency: 40ms)", fontsize=13, fontweight="bold", pad=12)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(fontsize=10)

    ax2.set_xlabel("Latency Jitter (± ms)", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Handover Overhead (seconds)", fontsize=12, fontweight="bold")
    ax2.set_title("Handover Overhead Sensitivity to Jitter", fontsize=13, fontweight="bold", pad=12)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(fontsize=10)

    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_png_path)), exist_ok=True)
    plt.savefig(output_png_path, dpi=300)
    plt.close(fig)
    print(f"📈 Jitter Sweep Analysis Chart saved: {output_png_path}")

# ==============================================================================
# 6. CONSOLIDATED SUMMARY CSV EXPORT
# ==============================================================================

def save_sweeps_summary_csv(grouped_items, output_filepath):
    """
    Exports all parsed sweep and scenario metrics to a clean consolidated CSV.
    """
    all_items = []
    for category_items in grouped_items.values():
        all_items.extend(category_items)

    if not all_items:
        return

    os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)

    fieldnames = [
        "sweep_type", "test_name", "file_size_mb", "cwnd_mode",
        "rate", "latency", "jitter", "loss",
        "latency_ms", "jitter_ms", "loss_pct",
        "iterations", "baseline_mean_sec", "baseline_std_sec",
        "migration_mean_sec", "migration_std_sec",
        "overhead_mean_sec", "overhead_std_sec",
        "relative_overhead_pct", "goodput_baseline_mbps", "goodput_migration_mbps"
    ]

    with open(output_filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for item in all_items:
            m = item["metadata"]
            s = item["stats"]
            writer.writerow({
                "sweep_type": m["sweep_type"],
                "test_name": m["test_name"],
                "file_size_mb": m["file_size_mb"],
                "cwnd_mode": m["cwnd_mode"],
                "rate": m["configured_rate"],
                "latency": m["configured_latency"],
                "jitter": m["configured_jitter"],
                "loss": m["configured_loss"],
                "latency_ms": m["latency_ms"],
                "jitter_ms": m["jitter_ms"],
                "loss_pct": m["loss_pct"],
                "iterations": item["num_iterations"],
                "baseline_mean_sec": f"{s['baseline_mean']:.4f}",
                "baseline_std_sec": f"{s['baseline_std']:.4f}",
                "migration_mean_sec": f"{s['migration_mean']:.4f}",
                "migration_std_sec": f"{s['migration_std']:.4f}",
                "overhead_mean_sec": f"{s['overhead_mean']:.4f}",
                "overhead_std_sec": f"{s['overhead_std']:.4f}",
                "relative_overhead_pct": f"{s['relative_overhead_pct']:.2f}",
                "goodput_baseline_mbps": f"{s['goodput_base_mbps']:.2f}",
                "goodput_migration_mbps": f"{s['goodput_migr_mbps']:.2f}"
            })

    print(f" Summary Sweeps CSV saved to: {output_filepath}")

# ==============================================================================
# 7. MAIN CONTROLLER
# ==============================================================================

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target = sys.argv[1] if len(sys.argv) > 1 else "EXPERIMENT3"

    exp_dir = os.path.join(base_dir, target) if not os.path.isabs(target) else target

    print(f"\n🚀 Running Parametric Sweeps & Scenario Analysis on: {os.path.basename(exp_dir)}...")

    grouped = load_sweep_results(exp_dir)

    total_files = sum(len(v) for v in grouped.values())
    if total_files == 0:
        print(f"No sweep result CSV files found in {exp_dir}/results/")
        return

    plots_dir = os.path.join(exp_dir, "plots")

    # 1. Print formatted tables by category
    print_latency_table(grouped["latency_sweep"])
    print_loss_table(grouped["loss_sweep"])
    print_jitter_table(grouped["jitter_sweep"])

    # 2. Export consolidated summary CSV
    save_sweeps_summary_csv(grouped, os.path.join(exp_dir, "summary_sweeps.csv"))

    # 3. Generate specialized plots
    if grouped["latency_sweep"]:
        plot_latency_sweep(grouped["latency_sweep"], os.path.join(plots_dir, "latency_sweep_analysis.png"))

    if grouped["loss_sweep"]:
        plot_loss_sweep(grouped["loss_sweep"], os.path.join(plots_dir, "loss_sweep_analysis.png"))

    if grouped["jitter_sweep"]:
        plot_jitter_sweep(grouped["jitter_sweep"], os.path.join(plots_dir, "jitter_sweep_analysis.png"))

    print("\n Analysis & plotting completed successfully!\n")

if __name__ == "__main__":
    main()
