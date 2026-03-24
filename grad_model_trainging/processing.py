import pandas as pd
import ast
import glob
import os
import numpy as np
import json

# ================= CONFIG =================
INPUT_DIR = "collecting"
OUTPUT_DIR = "combined"

TIME_MARGIN_MS = 500
WINDOW_SIZE = 10
STEP_SIZE = 3
TARGET_CSI_LEN = 128

# 🔥 INITIAL: use full range (temporary for training)

with open("../grad_dashboard/backend/models/selected_idx.json") as f:
    SELECTED_IDX = json.load(f)

os.makedirs(OUTPUT_DIR, exist_ok=True)

LABEL_MAP = {
    "No_person": 0,
    "point_1": 1,
    "point_2": 1,
    "point_3": 1,
    "point_1_2": 2,
    "point_1_3": 2,
    "point_2_3": 2,
    "point_1_2_3": 3,
}

def parse_csi(x):
    try:
        return ast.literal_eval(x)
    except:
        return None

def fix_csi_length(csi):
    csi = list(csi)
    if len(csi) > TARGET_CSI_LEN:
        return csi[:TARGET_CSI_LEN]
    if len(csi) < TARGET_CSI_LEN:
        return csi + [0]*(TARGET_CSI_LEN-len(csi))
    return csi

def preprocess_csv(path):
    df = pd.read_csv(path)
    df["csi_data"] = df["csi"].apply(parse_csi)
    df = df.dropna()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df[["esp_id","timestamp","rssi","csi_data"]]

def merge_rx(df):
    rx1 = df[df["esp_id"]=="rx1"].sort_values("timestamp")
    rx2 = df[df["esp_id"]=="rx2"].sort_values("timestamp")

    merged = pd.merge_asof(
        rx1, rx2,
        on="timestamp",
        direction="nearest",
        tolerance=pd.Timedelta(milliseconds=TIME_MARGIN_MS),
        suffixes=("_RX1","_RX2")
    )

    return merged.dropna()

def extract_features(chunk):
    csi1 = np.vstack(chunk["csi_data_RX1"])
    csi2 = np.vstack(chunk["csi_data_RX2"])

    csi1 = csi1[:, SELECTED_IDX]
    csi2 = csi2[:, SELECTED_IDX]

    feat = {
        "rssi_RX1": chunk["rssi_RX1"].mean(),
        "rssi_RX2": chunk["rssi_RX2"].mean(),
    }

    c1m = np.mean(csi1, axis=0)
    c1s = np.std(csi1, axis=0)
    c2m = np.mean(csi2, axis=0)
    c2s = np.std(csi2, axis=0)

    for i in range(len(SELECTED_IDX)):
        feat[f"RX1_mean_{i}"] = c1m[i]
        feat[f"RX1_std_{i}"] = c1s[i]
        feat[f"RX2_mean_{i}"] = c2m[i]
        feat[f"RX2_std_{i}"] = c2s[i]

    diff = c1m - c2m
    for i in range(len(diff)):
        feat[f"diff_{i}"] = diff[i]

    return feat

def window_aggregate(df):
    rows = []
    for i in range(0, len(df)-WINDOW_SIZE, STEP_SIZE):
        chunk = df.iloc[i:i+WINDOW_SIZE]
        row = extract_features(chunk)
        row["person_count"] = chunk["person_count"].mode()[0]
        row["scenario_id"] = chunk["scenario_id"].iloc[0]
        rows.append(row)
    return pd.DataFrame(rows)

def build_dataset(split):
    all_data = []
    for scenario, count in LABEL_MAP.items():
        folder = os.path.join(INPUT_DIR, split, scenario)

        for file in glob.glob(folder+"/*.csv"):
            df = preprocess_csv(file)
            merged = merge_rx(df)

            merged["csi_data_RX1"] = merged["csi_data_RX1"].apply(fix_csi_length)
            merged["csi_data_RX2"] = merged["csi_data_RX2"].apply(fix_csi_length)

            merged["scenario_id"] = scenario
            merged["person_count"] = count

            all_data.append(window_aggregate(merged))

    return pd.concat(all_data, ignore_index=True)

if __name__ == "__main__":
    train_df = build_dataset("train")
    test_df = build_dataset("test")

    train_df.to_csv("combined/train_dataset.csv", index=False)
    test_df.to_csv("combined/test_dataset.csv", index=False)

    print("Train:", train_df.shape)