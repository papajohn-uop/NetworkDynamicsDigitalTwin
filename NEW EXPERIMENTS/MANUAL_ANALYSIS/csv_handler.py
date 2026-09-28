import csv
import os



def get_all_csv_files(folder_path):
    all_csv_files = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            all_csv_files.append(os.path.join(folder_path, filename))
    return all_csv_files

def read_single_csv(target_csv_file):
    #basic test info
    csv_metadata = {
        "configured_rate": "",
        "configured_latency": "0ms",
        "configured_jitter": "0ms",
        "configured_loss": "0%",
        "cwnd_mode": "cubic",
        "file_size_mb": 0,
    }
    #test retuls
    baseline_times = []
    migration_times = []
    overhead_times = []

    all_data=[]
    with open(target_csv_file, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        row_1=next(reader)
        #lets populate the csv_metadata with values from the header
        csv_metadata["configured_rate"] = row_1[1]
        csv_metadata["configured_latency"] = row_1[2]
        csv_metadata["configured_jitter"] = row_1[3]
        csv_metadata["configured_loss"] = row_1[4]
        csv_metadata["cwnd_mode"] = row_1[5]
        csv_metadata["file_size_mb"] = row_1[6]
        
        # print(target_csv_file)
        # print(csv_metadata)
    with open(target_csv_file, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            # print(row)
            #get the data we are interested in
            # store them in a list of tuples
            baseline_times.append(float(row[7]))
            migration_times.append(float(row[8]))
            overhead_times.append(float(row[9]))

    return [csv_metadata,baseline_times,migration_times,overhead_times]


def save_stats_dict_to_csv(data_dict, output_csv_file):
    """
    Saves a dictionary of {file_size: {mean, median, std, min, max, count}} to CSV format.
    """
    if not data_dict:
        return
    first_key = next(iter(data_dict))
    stat_keys = list(data_dict[first_key].keys())
    fieldnames = ["file_size_mb"] + stat_keys

    with open(output_csv_file, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for file_size, stats in data_dict.items():
            row = {"file_size_mb": file_size, **stats}
            writer.writerow(row)
    print(f"Saved: {output_csv_file}")


def save_all_results_to_csv(all_results_dict, output_csv_file):
    """
    Saves the combined all_results dictionary {file_size: {direct, migrate, diff}} to CSV.
    """
    if not all_results_dict:
        return
    sub_keys = ["direct_transfer", "migration_transfer", "diff"]
    first_file_size = next(iter(all_results_dict))
    stat_keys = list(all_results_dict[first_file_size][sub_keys[0]].keys())

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