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
    