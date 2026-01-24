import pandas as pd
import ast
import glob
import os
import numpy as np

# ================= CONFIG =================
INPUT_DIR = "collecting"
OUTPUT_DIR = "combined"

TIME_MARGIN_MS = 50
WINDOW_SIZE = 10
STEP_SIZE = 3
TARGET_CSI_LEN = 128

os.makedirs(OUTPUT_DIR, exist_ok=True)

LABEL_MAP = {
    "No_person":      0,
    "point_1":        1,
    "point_2":        1,
    "point_3":        1,
    "point_1_2":      2,
    "point_1_3":      2,
    "point_2_3":      2,
    "point_1_2_3":    3,
}

# ================= CSI UTILS =================
def parse_csi(x):
    try:
        return ast.literal_eval(x) if isinstance(x, str) else x
    except:
        return None

def fix_csi_length(csi):
    csi = list(csi)
    if len(csi) > TARGET_CSI_LEN:
        return csi[:TARGET_CSI_LEN]
    elif len(csi) < TARGET_CSI_LEN:
        return csi + [0.0] * (TARGET_CSI_LEN - len(csi))
    return csi

# ================= PREPROCESS =================
def preprocess_csv(path):
    df = pd.read_csv(path)
    df["csi_data"] = df["csi"].apply(parse_csi)
    df = df.dropna(subset=["csi_data"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df[["esp_id", "timestamp", "rssi", "csi_data"]]

def merge_rx(df):
    rx1 = df[df["esp_id"] == "rx1"].sort_values("timestamp")
    rx2 = df[df["esp_id"] == "rx2"].sort_values("timestamp")

    merged = pd.merge_asof(
        rx1, rx2,
        on="timestamp",
        direction="nearest",
        tolerance=pd.Timedelta(milliseconds=TIME_MARGIN_MS),
        suffixes=("_RX1", "_RX2")
    )

    return merged.dropna(subset=["rssi_RX2"])

# ================= FEATURE EXTRACTION =================
def extract_features(chunk):
    csi1 = np.vstack(chunk["csi_data_RX1"])
    csi2 = np.vstack(chunk["csi_data_RX2"])

    return {
        "rssi_RX1": chunk["rssi_RX1"].mean(),
        "rssi_RX2": chunk["rssi_RX2"].mean(),

        "RX1_mean": csi1.mean(),
        "RX1_std": csi1.std(),
        "RX1_energy": np.sum(csi1 ** 2),

        "RX2_mean": csi2.mean(),
        "RX2_std": csi2.std(),
        "RX2_energy": np.sum(csi2 ** 2),

        "RX_diff_mean": np.mean(csi1 - csi2),
        "RX_diff_std": np.std(csi1 - csi2),

        "RX1_time_var": np.var(csi1, axis=0).mean(),
        "RX2_time_var": np.var(csi2, axis=0).mean(),
    }

def window_aggregate(df):
    rows = []
    for i in range(0, len(df) - WINDOW_SIZE, STEP_SIZE):
        chunk = df.iloc[i:i + WINDOW_SIZE]
        if len(chunk) < WINDOW_SIZE:
            continue

        row = extract_features(chunk)
        row["scenario_id"] = chunk["scenario_id"].iloc[0]
        row["person_count"] = chunk["person_count"].iloc[0]

        rows.append(row)

    return pd.DataFrame(rows)

# ================= DATASET BUILDER =================
def build_dataset(split):
    all_data = []

    for scenario, count in LABEL_MAP.items():
        folder = os.path.join(INPUT_DIR, split, scenario)
        for file in glob.glob(os.path.join(folder, "*.csv")):

            df = preprocess_csv(file)
            merged = merge_rx(df)
            if merged.empty:
                continue

            merged["csi_data_RX1"] = merged["csi_data_RX1"].apply(fix_csi_length)
            merged["csi_data_RX2"] = merged["csi_data_RX2"].apply(fix_csi_length)

            merged["scenario_id"] = os.path.basename(file)
            merged["person_count"] = count

            windows = window_aggregate(merged)
            all_data.append(windows)

    return pd.concat(all_data, ignore_index=True)

# ================= RUN =================
if __name__ == "__main__":
    train_df = build_dataset("train")
    test_df  = build_dataset("test")

    train_df.to_csv("combined/train_dataset.csv", index=False)
    test_df.to_csv("combined/test_dataset.csv", index=False)

    print("Train:", train_df.shape)
    print("Test :", test_df.shape)
