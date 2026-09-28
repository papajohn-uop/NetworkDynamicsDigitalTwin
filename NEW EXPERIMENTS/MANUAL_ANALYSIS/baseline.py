from csv_handler import (
    read_single_csv,
    get_all_csv_files,
    save_stats_dict_to_csv,
    save_all_results_to_csv,
)
from analysis import analyse_single_csv_file
import json
#lets define some folders where we have the results

BASE_DIR = "./"
BASELINE_CUBIC_PATH = BASE_DIR + "EXPERIMENT1/"
BASELINE_RENO_PATH = BASE_DIR + "EXPERIMENT2/"

def print_analysis_results(res):
    print(res[0])
    print(res[1])
    print(res[2])
    print(res[3])

def analyse_baseline(target_path):
    target_csv_files = get_all_csv_files(target_path)

    all_results={}
    all_results_baseline={}
    all_results_migrate={}
    all_results_diff={}
    
    for csv_file in target_csv_files:
        # print(csv_file)
        analysis_results=analyse_single_csv_file(csv_file)
        # print_analysis_results(analysis_results)
        #create key for dict
        column_names=analysis_results[0]
        # key_name="rate_"+column_names["configured_rate"]
        # key_name=key_name+ "_latency_"+column_names["configured_latency"]
        # key_name=key_name+ "_jitter_"+column_names["configured_jitter"]
        # key_name=key_name+ "_loss_"+column_names["configured_loss"]
        # key_name=key_name+ "_mode_"+column_names["cwnd_mode"]
        # key_name=key_name+ "_filesize_"+column_names["file_size_mb"]
        # print(key_name)
        # all_results[key_name]=[column_names["file_size_mb"],analysis_results[1],analysis_results[2],analysis_results[3]]
        all_results[column_names["file_size_mb"]]={"direct_transfer":analysis_results[1],"migration_transfer":analysis_results[2],"diff":analysis_results[3]}
        all_results_baseline[column_names["file_size_mb"]]=analysis_results[1]
        all_results_migrate[column_names["file_size_mb"]]=analysis_results[2]
        all_results_diff[column_names["file_size_mb"]]=analysis_results[3]
    # Sort results by file size numerically (50 to 500 MB)
    all_results = dict(sorted(all_results.items(), key=lambda item: int(item[0])))
    all_results_baseline = dict(sorted(all_results_baseline.items(), key=lambda item: int(item[0])))
    all_results_migrate = dict(sorted(all_results_migrate.items(), key=lambda item: int(item[0])))
    all_results_diff = dict(sorted(all_results_diff.items(), key=lambda item: int(item[0])))

    return [all_results,all_results_baseline, all_results_migrate, all_results_diff]


def baseline_analysis():

    #analyse cubic
    all_results, all_results_baseline, all_results_migrate, all_results_diff = analyse_baseline(BASELINE_CUBIC_PATH)

    # Save the 4 CSV tables for cubic
    save_all_results_to_csv(all_results, "cubic_all_results.csv")
    save_stats_dict_to_csv(all_results_baseline, "cubic_baseline.csv")
    save_stats_dict_to_csv(all_results_migrate, "cubic_migrate.csv")
    save_stats_dict_to_csv(all_results_diff, "cubic_diff.csv")

    # #analyse reno
    # all_results_r, baseline_r, migrate_r, diff_r = analyse_baseline(BASELINE_RENO_PATH)
    # save_all_results_to_csv(all_results_r, "reno_all_results.csv")
    # save_stats_dict_to_csv(baseline_r, "reno_baseline.csv")
    # save_stats_dict_to_csv(migrate_r, "reno_migrate.csv")
    # save_stats_dict_to_csv(diff_r, "reno_diff.csv")