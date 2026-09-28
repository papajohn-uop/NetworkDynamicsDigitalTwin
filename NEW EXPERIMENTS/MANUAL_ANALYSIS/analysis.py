

from csv_handler import read_single_csv, get_all_csv_files

def analyse_single_csv_file(target_csv_file):
    """
    Analyzes a single CSV file: reads metadata and timing lists, then calculates
    statistical summaries (mean, median, std, min, max, count) for:
    - baseline transfer times
    - migration transfer times
    - overhead (difference) times

    Parameters:
        target_csv_file (str): Path to the CSV file to analyze.

    Returns:
        list: [test_metadata (dict), baseline_stats (dict), migration_stats (dict), overhead_stats (dict)]
    """
    # print("*****************************************")
    # print("Analysing csv file-->",target_csv_file)
    # data[0] are the metadata
    # data[1] are the baseline times
    # data[2] are the migration times
    # data[3] are the overhead times
    data = read_single_csv(target_csv_file)

    # lets do some analysis on the data
    # get the stats of the data 
    test_metadata = data[0]
    baseline_stats = compute_stats(data[1])
    migration_stats = compute_stats(data[2])
    overhead_stats = compute_stats(data[3])
    
    return [test_metadata, baseline_stats, migration_stats, overhead_stats]
    # print the results (unreachable debug code)
    # print(test_metadata)
    # print(baseline_stats)
    # print(migration_stats)
    # print(overhead_stats)
    # print(data)


def compute_stats(data_list):
    """
    Computes basic descriptive statistics for a list of numerical values.

    Calculated metrics:
        - mean: Arithmetic average
        - median: Middle value (or average of two middle values)
        - std: Population standard deviation
        - min: Minimum recorded value
        - max: Maximum recorded value
        - count: Total number of samples

    Parameters:
        data_list (list[float]): List of numbers to compute statistics for.

    Returns:
        dict: Statistical summary with values rounded to NUMBER_OF_DECIMALS.
    """
    # lets define here the number of decimal points to be used on the calculation
    NUMBER_OF_DECIMALS = 4
    if not data_list:
        return {"mean": 0, "median": 0, "std": 0, "min": 0, "max": 0, "count": 0}
    
    sorted_data = sorted(data_list)
    n = len(data_list)
    mean_val = sum(data_list) / n

    # Median calculation for odd vs even length
    if n % 2 == 1:
        median_val = sorted_data[n // 2]
    else:
        median_val = (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2    

    # Standard deviation calculation
    variance = sum((x - mean_val) ** 2 for x in data_list) / n
    std_dev = variance ** 0.5
    min_val = min(data_list)
    max_val = max(data_list)
    
    return {
        "mean": round(mean_val, NUMBER_OF_DECIMALS),
        "median": round(median_val, NUMBER_OF_DECIMALS),
        "std": round(std_dev, NUMBER_OF_DECIMALS),
        "min": round(min_val, NUMBER_OF_DECIMALS),
        "max": round(max_val, NUMBER_OF_DECIMALS),
        "count": n
    }
        

