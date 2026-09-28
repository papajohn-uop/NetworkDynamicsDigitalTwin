import os
import matplotlib
# Use headless Agg backend for remote/server environments without a display
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def plot_transfer_time_comparison(cubic_all, reno_all=None, output_file="plot_transfer_time.png"):
    """
    Plots direct baseline transfer time vs mid-transfer migration time
    across payload sizes (50 MB to 500 MB) for TCP CUBIC (and optionally TCP Reno).

    Demonstrates linear scaling: Completion time is proportional to payload size.

    Parameters:
        cubic_all (dict): Combined dictionary for TCP CUBIC.
        reno_all (dict, optional): Combined dictionary for TCP Reno.
        output_file (str): Output file path for the generated PNG chart.
    """
    file_sizes = sorted([int(k) for k in cubic_all.keys()])
    cubic_direct_means = [cubic_all[str(s)]["direct_transfer"]["mean"] for s in file_sizes]
    cubic_migrate_means = [cubic_all[str(s)]["migration_transfer"]["mean"] for s in file_sizes]

    plt.figure(figsize=(9, 5.5), dpi=300)
    plt.plot(file_sizes, cubic_direct_means, 'o-', color='#1f77b4', label='TCP CUBIC - Direct Baseline', linewidth=2, markersize=6)
    plt.plot(file_sizes, cubic_migrate_means, 's--', color='#ff7f0e', label='TCP CUBIC - Migration', linewidth=2, markersize=6)

    if reno_all:
        reno_direct_means = [reno_all[str(s)]["direct_transfer"]["mean"] for s in file_sizes]
        reno_migrate_means = [reno_all[str(s)]["migration_transfer"]["mean"] for s in file_sizes]
        plt.plot(file_sizes, reno_direct_means, '^:', color='#2ca02c', label='TCP Reno - Direct Baseline', linewidth=1.8, markersize=6)
        plt.plot(file_sizes, reno_migrate_means, 'x-.', color='#d62728', label='TCP Reno - Migration', linewidth=1.8, markersize=6)

    plt.title("Total Transfer Time: Direct Transfer vs. Mid-Transfer Migration", fontsize=13, fontweight='bold', pad=12)
    plt.xlabel("Payload Size (MB)", fontsize=11, fontweight='semibold')
    plt.ylabel("Completion Time (seconds)", fontsize=11, fontweight='semibold')
    plt.xticks(file_sizes)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=10)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"Saved plot: {output_file}")


def plot_handover_overhead(cubic_diff, reno_diff=None, output_file="plot_handover_overhead.png"):
    """
    Plots absolute handover overhead time (Delta T = T_migration - T_baseline) in milliseconds
    across payload sizes (50 MB to 500 MB).

    Demonstrates the Handover Invariance Law: Handover overhead is constant and independent
    of payload volume.

    Parameters:
        cubic_diff (dict): Overhead statistics dictionary for TCP CUBIC.
        reno_diff (dict, optional): Overhead statistics dictionary for TCP Reno.
        output_file (str): Output file path for the generated PNG chart.
    """
    file_sizes = sorted([int(k) for k in cubic_diff.keys()])
    # Convert seconds to milliseconds (mean and std)
    cubic_means_ms = [cubic_diff[str(s)]["mean"] * 1000 for s in file_sizes]
    cubic_stds_ms = [cubic_diff[str(s)]["std"] * 1000 for s in file_sizes]

    plt.figure(figsize=(9, 5.5), dpi=300)

    # Plot CUBIC with error bars
    plt.errorbar(
        file_sizes, cubic_means_ms, yerr=cubic_stds_ms,
        fmt='o-', color='#1f77b4', ecolor='#aec7e8', elinewidth=2, capsize=4,
        label='TCP CUBIC Overhead (Mean ± Std)', linewidth=2, markersize=6
    )

    # Calculate and display global mean for CUBIC
    overall_cubic_mean = sum(cubic_means_ms) / len(cubic_means_ms)
    plt.axhline(overall_cubic_mean, color='#1f77b4', linestyle=':', alpha=0.7,
                label=f'CUBIC Invariant Mean ({overall_cubic_mean:.1f} ms)')

    if reno_diff:
        reno_means_ms = [reno_diff[str(s)]["mean"] * 1000 for s in file_sizes]
        reno_stds_ms = [reno_diff[str(s)]["std"] * 1000 for s in file_sizes]
        plt.errorbar(
            file_sizes, reno_means_ms, yerr=reno_stds_ms,
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
    print(f"Saved plot: {output_file}")


def plot_relative_overhead_decay(cubic_baseline, cubic_diff, reno_baseline=None, reno_diff=None, output_file="plot_relative_decay.png"):
    """
    Plots relative overhead percentage [rho = (Delta T / T_baseline) * 100%]
    decaying hyperbolically (proportional to 1/S) as file size increases.

    Demonstrates that handover cost is amortized and negligible (< 0.1%) for large transfers.

    Parameters:
        cubic_baseline (dict): Baseline statistics dictionary for TCP CUBIC.
        cubic_diff (dict): Overhead statistics dictionary for TCP CUBIC.
        reno_baseline (dict, optional): Baseline statistics dictionary for TCP Reno.
        reno_diff (dict, optional): Overhead statistics dictionary for TCP Reno.
        output_file (str): Output file path for the generated PNG chart.
    """
    file_sizes = sorted([int(k) for k in cubic_baseline.keys()])
    cubic_rel_pct = [
        (cubic_diff[str(s)]["mean"] / cubic_baseline[str(s)]["mean"]) * 100
        for s in file_sizes
    ]

    plt.figure(figsize=(9, 5.5), dpi=300)
    plt.plot(file_sizes, cubic_rel_pct, 'o-', color='#1f77b4', linewidth=2.2, markersize=7, label='TCP CUBIC Relative Overhead (%)')

    # Annotate key decay endpoints
    plt.annotate(f"{cubic_rel_pct[0]:.2f}%", (file_sizes[0], cubic_rel_pct[0]),
                 textcoords="offset points", xytext=(10, 5), fontweight='semibold', color='#1f77b4')
    plt.annotate(f"{cubic_rel_pct[-1]:.2f}%", (file_sizes[-1], cubic_rel_pct[-1]),
                 textcoords="offset points", xytext=(-25, 10), fontweight='semibold', color='#1f77b4')

    if reno_baseline and reno_diff:
        reno_rel_pct = [
            (reno_diff[str(s)]["mean"] / reno_baseline[str(s)]["mean"]) * 100
            for s in file_sizes
        ]
        plt.plot(file_sizes, reno_rel_pct, 's--', color='#ff7f0e', linewidth=2, markersize=6, label='TCP Reno Relative Overhead (%)')
        plt.annotate(f"{reno_rel_pct[0]:.2f}%", (file_sizes[0], reno_rel_pct[0]),
                     textcoords="offset points", xytext=(10, -15), fontweight='semibold', color='#ff7f0e')
        plt.annotate(f"{reno_rel_pct[-1]:.2f}%", (file_sizes[-1], reno_rel_pct[-1]),
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
    print(f"Saved plot: {output_file}")


def generate_all_plots(cubic_results, reno_results=None, output_dir="."):
    """
    Convenience function to generate all core baseline visualization figures.

    Parameters:
        cubic_results (list): [all_results, baseline_stats, migrate_stats, diff_stats] for CUBIC.
        reno_results (list, optional): [all_results, baseline_stats, migrate_stats, diff_stats] for Reno.
        output_dir (str): Directory where the PNG plots will be saved.
    """
    cubic_all, cubic_baseline, cubic_migrate, cubic_diff = cubic_results

    reno_all = reno_results[0] if reno_results else None
    reno_baseline = reno_results[1] if reno_results else None
    reno_migrate = reno_results[2] if reno_results else None
    reno_diff = reno_results[3] if reno_results else None

    transfer_time_path = os.path.join(output_dir, "plot_transfer_time.png")
    overhead_path = os.path.join(output_dir, "plot_handover_overhead.png")
    decay_path = os.path.join(output_dir, "plot_relative_decay.png")

    plot_transfer_time_comparison(cubic_all, reno_all, transfer_time_path)
    plot_handover_overhead(cubic_diff, reno_diff, overhead_path)
    plot_relative_overhead_decay(cubic_baseline, cubic_diff, reno_baseline, reno_diff, decay_path)
