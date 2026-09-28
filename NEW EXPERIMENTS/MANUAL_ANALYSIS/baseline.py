from csv_handler import (
    read_single_csv,
    get_all_csv_files,
    save_stats_dict_to_csv,
    save_all_results_to_csv,
)
from analysis import analyse_single_csv_file
from plotting import generate_all_plots
import json
#lets define some folders where we have the results

BASE_DIR = "./"
BASELINE_CUBIC_PATH = BASE_DIR + "EXPERIMENT1/"
BASELINE_RENO_PATH = BASE_DIR + "EXPERIMENT2/"

def print_analysis_results(res):
    """
    Helper function to print the 4 elements returned by single CSV analysis:
    res[0]: metadata dictionary
    res[1]: baseline timing statistics
    res[2]: migration timing statistics
    res[3]: overhead / difference statistics
    """
    print("Metadata:", res[0])
    print("Baseline Stats:", res[1])
    print("Migration Stats:", res[2])
    print("Diff Stats:", res[3])

def analyse_baseline(target_path):
    """
    Iterates over all CSV files in target_path (e.g. EXPERIMENT1 for CUBIC, EXPERIMENT2 for Reno),
    computes summary statistics for each payload size, sorts them numerically (50 to 500 MB),
    and aggregates them into 4 dictionaries.

    Parameters:
        target_path (str): Directory containing the raw experiment CSV files.

    Returns:
        list: [
            all_results: dict mapping file_size -> {direct_transfer, migration_transfer, diff},
            all_results_baseline: dict mapping file_size -> direct_transfer stats,
            all_results_migrate: dict mapping file_size -> migration_transfer stats,
            all_results_diff: dict mapping file_size -> overhead/diff stats
        ]
    """
    target_csv_files = get_all_csv_files(target_path)

    all_results = {}
    all_results_baseline = {}
    all_results_migrate = {}
    all_results_diff = {}
    
    # Process each CSV file (one file per payload size)
    for csv_file in target_csv_files:
        # print(csv_file)
        analysis_results = analyse_single_csv_file(csv_file)
        # print_analysis_results(analysis_results)
        # create key for dict
        column_names = analysis_results[0]
        # key_name="rate_"+column_names["configured_rate"]
        # key_name=key_name+ "_latency_"+column_names["configured_latency"]
        # key_name=key_name+ "_jitter_"+column_names["configured_jitter"]
        # key_name=key_name+ "_loss_"+column_names["configured_loss"]
        # key_name=key_name+ "_mode_"+column_names["cwnd_mode"]
        # key_name=key_name+ "_filesize_"+column_names["file_size_mb"]
        # print(key_name)
        # all_results[key_name]=[column_names["file_size_mb"],analysis_results[1],analysis_results[2],analysis_results[3]]
        file_size = column_names["file_size_mb"]
        all_results[file_size] = {
            "direct_transfer": analysis_results[1],
            "migration_transfer": analysis_results[2],
            "diff": analysis_results[3]
        }
        all_results_baseline[file_size] = analysis_results[1]
        all_results_migrate[file_size] = analysis_results[2]
        all_results_diff[file_size] = analysis_results[3]

    # Sort results by file size numerically (50 to 500 MB)
    all_results = dict(sorted(all_results.items(), key=lambda item: int(item[0])))
    all_results_baseline = dict(sorted(all_results_baseline.items(), key=lambda item: int(item[0])))
    all_results_migrate = dict(sorted(all_results_migrate.items(), key=lambda item: int(item[0])))
    all_results_diff = dict(sorted(all_results_diff.items(), key=lambda item: int(item[0])))

    return [all_results, all_results_baseline, all_results_migrate, all_results_diff]


def baseline_analysis():
    """
    Coordinates baseline analysis workflow:
    1. Analyzes TCP CUBIC (EXPERIMENT1) across all payload sizes.
    2. Exports four CSV tables (combined all_results, baseline, migrate, diff).
    3. (Optionally) Analyzes and exports TCP Reno (EXPERIMENT2).
    """
    # analyse cubic
    all_results, all_results_baseline, all_results_migrate, all_results_diff = analyse_baseline(BASELINE_CUBIC_PATH)

    # Save the 4 CSV tables for cubic
    save_all_results_to_csv(all_results, "cubic_all_results.csv")
    save_stats_dict_to_csv(all_results_baseline, "cubic_baseline.csv")
    save_stats_dict_to_csv(all_results_migrate, "cubic_migrate.csv")
    save_stats_dict_to_csv(all_results_diff, "cubic_diff.csv")

    #analyse reno
    all_results_r, baseline_r, migrate_r, diff_r = analyse_baseline(BASELINE_RENO_PATH)
    save_all_results_to_csv(all_results_r, "reno_all_results.csv")
    save_stats_dict_to_csv(baseline_r, "reno_baseline.csv")
    save_stats_dict_to_csv(migrate_r, "reno_migrate.csv")
    save_stats_dict_to_csv(diff_r, "reno_diff.csv")

    # Generate visualization figures comparing CUBIC and Reno
    generate_all_plots(
        cubic_results=[all_results, all_results_baseline, all_results_migrate, all_results_diff],
        reno_results=[all_results_r, baseline_r, migrate_r, diff_r]
    )