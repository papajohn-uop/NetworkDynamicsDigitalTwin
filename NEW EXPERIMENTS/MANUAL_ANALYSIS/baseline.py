from csv_handler import read_single_csv, get_all_csv_files
from analysis import analyse_single_csv_file
#lets define some folders where we have the results

BASE_DIR = "./"
BASELINE_CUBIC_PATH = BASE_DIR + "EXPERIMENT1/"
BASELINE_RENO_PATH = BASE_DIR + "EXPERIMENT2/"


def analyse_baseline(target_path):
    target_csv_files = get_all_csv_files(target_path)
    
    for csv_file in target_csv_files:
        # print(csv_file)
        analyse_single_csv_file(csv_file)
        #lets work on first file to make sure it works and then we can move to the next
        break

def baseline_analysis():

    #analyse cubic
    analyse_baseline(BASELINE_CUBIC_PATH)

    # #analyse reno
    # analyse_baseline(BASELINE_RENO_PATH)