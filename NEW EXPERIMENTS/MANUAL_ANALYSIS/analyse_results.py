# lets do analysis of the results
# automatic analuysis creation seems to work
# manual programmin will allow us to better understand flows and results


import os
import sys

#lets define some folders where we have the results
BASE_DIR = "./"
BASELINE_CUBIC_PATH = BASE_DIR + "EXPERIMENT1/"
BASELINE_RENO_PATH = BASE_DIR + "EXPERIMENT2/"

 


def get_all_csv_files(folder_path):
    all_csv_files = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            all_csv_files.append(os.path.join(folder_path, filename))
    return all_csv_files

def analyse_baseline(target_path):
    target_csv_files = get_all_csv_files(target_path)
    
    for csv_file in target_csv_files:
        print(csv_file)
    
    


def analyze_baseline():

    #analyse cubic
    analyse_baseline(BASELINE_CUBIC_PATH)

    #analyse reno
    analyse_baseline(BASELINE_RENO_PATH)
    

    
    


if __name__ == "__main__":
    analyze_baseline()