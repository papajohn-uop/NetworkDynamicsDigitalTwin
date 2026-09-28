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
LATENCY_SWEEP_PATH = BASE_DIR + "EXPERIMENT3/latency_sweep/"
LOSS_SWEEP_PATH = BASE_DIR + "EXPERIMENT3/loss_sweep/"
JITTER_SWEEP_PATH = BASE_DIR + "EXPERIMENT3/jitter_sweep/"


def latency_sweep_analysis():
    files = get_all_csv_files(LATENCY_SWEEP_PATH)
    all_results = {}
    all_results_baseline = {}
    all_results_migrate = {}
    all_results_diff = {}
    for csv_file in files:
        analysis_results = analyse_single_csv_file(csv_file)
        # print_analysis_results(analy  sis_results)
        # create key for dict
        column_names = analysis_results[0]
        latency=column_names["configured_latency"]
        file_size = float(column_names["file_size_mb"])
     
        if latency not in all_results:
            all_results[latency] = {}
            all_results_baseline[latency] = {}
            all_results_migrate[latency] = {}
            all_results_diff[latency] = {}

        all_results[latency][file_size] = {
            "direct_transfer": analysis_results[1],
            "migration_transfer": analysis_results[2],
            "diff": analysis_results[3]
        }
        all_results_baseline[latency][file_size] = analysis_results[1]
        all_results_migrate[latency][file_size] = analysis_results[2]
        all_results_diff[latency][file_size] = analysis_results[3]

    # Sort results by latency numerically (e.g. '10ms', '20ms', '40ms', '80ms', '160ms')
    parse_latency = lambda item: float(item[0].replace("ms", ""))
    all_results = dict(sorted(all_results.items(), key=parse_latency))
    all_results_baseline = dict(sorted(all_results_baseline.items(), key=parse_latency))
    all_results_migrate = dict(sorted(all_results_migrate.items(), key=parse_latency))
    all_results_diff = dict(sorted(all_results_diff.items(), key=parse_latency))

    # Sort inner dictionaries by file size numerically
    for d in (all_results, all_results_baseline, all_results_migrate, all_results_diff):
        for lat in d:
            d[lat] = dict(sorted(d[lat].items(), key=lambda item: float(item[0])))

    print(json.dumps(all_results_baseline, indent=4))
    return [all_results, all_results_baseline, all_results_migrate, all_results_diff]


        


def loss_sweep_analysis():
   ... 

def jitter_sweep_analysis():
    ...

def sweep_analysis():
    results_latency =latency_sweep_analysis()
    all_results=results_latency[0]
    all_results_baseline=results_latency[1]
    all_results_migrate=results_latency[2]
    all_results_diff=results_latency[3]
    # Dynamically iterate over all latency keys from the results
    for latency in all_results.keys():
        save_all_results_to_csv(all_results[latency], f"./{latency}_all_results.csv")
        save_stats_dict_to_csv(all_results_baseline[latency], f"./{latency}_baseline.csv")
        save_stats_dict_to_csv(all_results_migrate[latency], f"./{latency}_migrate.csv")
        save_stats_dict_to_csv(all_results_diff[latency], f"./{latency}_diff.csv")
    


    

