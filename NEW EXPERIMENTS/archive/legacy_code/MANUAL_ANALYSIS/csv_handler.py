import csv
import os



def get_all_csv_files(folder_path):
    """
    Scans a folder and returns absolute/relative paths for all .csv files found within it.

    Parameters:
        folder_path (str): Path to the directory containing experiment CSV files.

    Returns:
        list[str]: List of file paths ending with '.csv'.
    """
    all_csv_files = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            all_csv_files.append(os.path.join(folder_path, filename))
    return all_csv_files

def read_single_csv(target_csv_file):
    """
    Parses a single experiment CSV file to extract metadata and measurement time series.

    Parameters:
        target_csv_file (str): Path to the target CSV file.

    Returns:
        list: [csv_metadata (dict), baseline_times (list[float]), migration_times (list[float]), overhead_times (list[float])]
    """
    # basic test info
    csv_metadata = {
        "configured_rate": "",
        "configured_latency": "0ms",
        "configured_jitter": "0ms",
        "configured_loss": "0%",
        "cwnd_mode": "cubic",
        "file_size_mb": 0,
    }
    # test results
    baseline_times = []
    migration_times = []
    overhead_times = []

    all_data = []
    # Read the first data row to populate metadata parameters
    with open(target_csv_file, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        row_1 = next(reader)
        # lets populate the csv_metadata with values from the header
        csv_metadata["configured_rate"] = row_1[1]
        csv_metadata["configured_latency"] = row_1[2]
        csv_metadata["configured_jitter"] = row_1[3]
        csv_metadata["configured_loss"] = row_1[4]
        csv_metadata["cwnd_mode"] = row_1[5]
        csv_metadata["file_size_mb"] = row_1[6]
        
        # print(target_csv_file)
        # print(csv_metadata)

    # Read all measurement iterations (baseline time, migration time, and overhead)
    with open(target_csv_file, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            # print(row)
            # get the data we are interested in
            # store them in a list of tuples
            baseline_times.append(float(row[7]))
            migration_times.append(float(row[8]))
            overhead_times.append(float(row[9]))

    return [csv_metadata, baseline_times, migration_times, overhead_times]


def save_stats_dict_to_csv(data_dict, output_csv_file):
    """
    Exports a single statistical metrics dictionary to a CSV table.
    
    Structure of data_dict:
        {
            file_size_mb: {"mean": float, "median": float, "std": float, "min": float, "max": float, "count": int},
            ...
        }

    Output CSV columns:
        file_size_mb, mean, median, std, min, max, count

    Parameters:
        data_dict (dict): Dictionary mapping file sizes to statistical metrics.
        output_csv_file (str): Output CSV filename/path.
    """
    if not data_dict:
        return
    first_key = next(iter(data_dict))
    stat_keys = list(data_dict[first_key].keys())
    fieldnames = ["file_size_mb"] + stat_keys

    #lets put all the csvs into antoher folder
    output_csv_file="./RESULTS/"+output_csv_file

    with open(output_csv_file, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for file_size, stats in data_dict.items():
            row = {"file_size_mb": file_size, **stats}
            writer.writerow(row)
    print(f"Saved: {output_csv_file}")


def save_all_results_to_csv(all_results_dict, output_csv_file):
    """
    Exports the combined results dictionary into a side-by-side comparison CSV table.

    Structure of all_results_dict:
        {
            file_size_mb: {
                "direct_transfer": {stats},
                "migration_transfer": {stats},
                "diff": {stats}
            },
            ...
        }

    Output CSV columns:
        file_size_mb, direct_transfer_mean, ..., migration_transfer_mean, ..., diff_mean, ...

    Parameters:
        all_results_dict (dict): Nested dictionary with direct, migration, and diff stats.
        output_csv_file (str): Output CSV filename/path.
    """
    #lets put all the csvs into antoher folder
    output_csv_file="./RESULTS/"+output_csv_file

    if not all_results_dict:
        return
    sub_keys = ["direct_transfer", "migration_transfer", "diff"]
    first_file_size = next(iter(all_results_dict))
    stat_keys = list(all_results_dict[first_file_size][sub_keys[0]].keys())

    # Build flattened CSV column names (e.g., direct_transfer_mean, diff_std)
    fieldnames = ["file_size_mb"]
    for sub in sub_keys:
        for sk in stat_keys:
            fieldnames.append(f"{sub}_{sk}")

    with open(output_csv_file, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for file_size, transfers in all_results_dict.items():
            row = {"file_size_mb": file_size}
            for sub in sub_keys:
                for sk in stat_keys:
                    row[f"{sub}_{sk}"] = transfers.get(sub, {}).get(sk, "")
            writer.writerow(row)
    print(f"Saved: {output_csv_file}")