# lets do analysis of the results
# automatic analuysis creation seems to work
# manual programmin will allow us to better understand flows and results



from csv_handler import read_single_csv, get_all_csv_files


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
    

        
def compute_stats(data_list):
    """
    Computes basic statistics for a list of numbers.
    """
    #lets define here the number of devi,al point to be used on the calculation
    NUMBER_OF_DECIMALS=4
    if not data_list:
        return {"mean": 0, "median": 0, "std": 0, "min": 0, "max": 0, "count": 0}
    
    sorted_data = sorted(data_list)
    n = len(data_list)
    mean_val = sum(data_list) / n
    if n % 2 == 1:
        median_val = sorted_data[n // 2]
    else:
        median_val = (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2    
    variance = sum((x - mean_val) ** 2 for x in data_list) / n
    std_dev = variance ** 0.5
    min_val = min(data_list)
    max_val = max(data_list)
    
    return {
        "mean": round(mean_val,NUMBER_OF_DECIMALS),
        "median": round(median_val,NUMBER_OF_DECIMALS),
        "std": round(std_dev,NUMBER_OF_DECIMALS),
        "min": round(min_val,NUMBER_OF_DECIMALS),
        "max": round(max_val,NUMBER_OF_DECIMALS),
        "count": n
    }

def compute_improvement(baseline_list, migration_list):
    """
    Computes the improvement percentage between two lists of numbers.
    """
    if not baseline_list or not migration_list:
        return 0.0
    
    baseline_mean = sum(baseline_list) / len(baseline_list)
    migration_mean = sum(migration_list) / len(migration_list)
    
    if baseline_mean == 0:
        return 0.0
    
    improvement = ((baseline_mean - migration_mean) / baseline_mean) * 100
    return improvement

def analyse_single_csv_file(target_csv_file):
    print("Analysing csv file-->",target_csv_file)
    # data[0] are the metadata
    # data[1] are the baseline times
    # data[2] are the migration times
    # data[3] are the overhead times
    data = read_single_csv(target_csv_file)
    #lets do some analysis on the data
    # get the stats of the data 

    baseline_stats=compute_stats(data[1])
    migration_stats=compute_stats(data[2])
    overhead_stats=compute_stats(data[3])
    
    # get the improvement
    improvement=compute_improvement(data[1],data[2])
    
    # print the results
    print(baseline_stats)
    print(migration_stats)
    print(overhead_stats)
    print(improvement)

    # print(data)
    
  
    
    


def analyze_baseline():

    #analyse cubic
    analyse_baseline(BASELINE_CUBIC_PATH)

    # #analyse reno
    # analyse_baseline(BASELINE_RENO_PATH)
    

    
    


if __name__ == "__main__":
    analyze_baseline()