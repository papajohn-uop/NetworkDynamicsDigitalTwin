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

def generic_sweep_analysis(file_path, parameter):
    if parameter not in ["latency", "loss", "jitter"]:
        raise ValueError("Invalid parameter. Must be 'latency', 'loss', or 'jitter'.")
    
    files = get_all_csv_files(file_path)
    
    all_results = {}
    all_results_baseline = {}
    all_results_migrate = {}
    all_results_diff = {}
    for csv_file in files:
        analysis_results = analyse_single_csv_file(csv_file)
        # print_analysis_results(analy  sis_results)
        # create key for dict
        column_names = analysis_results[0]
        parameter_value=column_names["configured_"+parameter]
        file_size = float(column_names["file_size_mb"])
     
        if parameter_value not in all_results:
            all_results[parameter_value] = {}
            all_results_baseline[parameter_value] = {}
            all_results_migrate[parameter_value] = {}
            all_results_diff[parameter_value] = {}

        all_results[parameter_value][file_size] = {
            "direct_transfer": analysis_results[1],
            "migration_transfer": analysis_results[2],
            "diff": analysis_results[3]
        }
        all_results_baseline[parameter_value][file_size] = analysis_results[1]
        all_results_migrate[parameter_value][file_size] = analysis_results[2]
        all_results_diff[parameter_value][file_size] = analysis_results[3]

    parse_latency = lambda item: float(item[0].replace("ms", ""))
    parse_loss = lambda item: float(item[0].replace("%", ""))
    parse_jitter = lambda item: float(item[0].replace("ms", ""))

    if parameter == "latency":
        parse_parameter = parse_latency
    elif parameter == "loss":
        parse_parameter = parse_loss
    elif parameter == "jitter":
        parse_parameter = parse_jitter
    all_results = dict(sorted(all_results.items(), key=parse_parameter))
    all_results_baseline = dict(sorted(all_results_baseline.items(), key=parse_parameter))
    all_results_migrate = dict(sorted(all_results_migrate.items(), key=parse_parameter))
    all_results_diff = dict(sorted(all_results_diff.items(), key=parse_parameter))

    # Sort inner dictionaries by file size numerically
    for d in (all_results, all_results_baseline, all_results_migrate, all_results_diff):
        for lat in d:
            d[lat] = dict(sorted(d[lat].items(), key=lambda item: float(item[0])))

    print(json.dumps(all_results_baseline, indent=4))
    return [all_results, all_results_baseline, all_results_migrate, all_results_diff]


def export_csvs(results,parameter):
    all_results=results[0]
    all_results_baseline=results[1]
    all_results_migrate=results[2]
    all_results_diff=results[3]
    # Dynamically iterate over all latency keys from the results
    for parameter_value in all_results.keys():  
        save_all_results_to_csv(all_results[parameter_value], f"./{parameter}_{parameter_value}_all_results.csv")
        save_stats_dict_to_csv(all_results_baseline[parameter_value], f"./{parameter}_{parameter_value}_baseline.csv")
        save_stats_dict_to_csv(all_results_migrate[parameter_value], f"./{parameter}_{parameter_value}_migrate.csv")
        save_stats_dict_to_csv(all_results_diff[parameter_value], f"./{parameter}_{parameter_value}_diff.csv")
    

def latency_sweep_analysis():
    return (generic_sweep_analysis(LATENCY_SWEEP_PATH,"latency"))
 


        


def loss_sweep_analysis():
   return (generic_sweep_analysis(LOSS_SWEEP_PATH,"loss")) 

def jitter_sweep_analysis():
    return (generic_sweep_analysis(JITTER_SWEEP_PATH,"jitter"))

def sweep_analysis():
    #latency
    _results =latency_sweep_analysis()
    export_csvs(_results, "cubic_latency")
    #loss
    _results =loss_sweep_analysis() 
    export_csvs(_results, "cubic_loss")
    #jitter
    _results =jitter_sweep_analysis()
    export_csvs(_results, "cubic_jitter") 

    


    

