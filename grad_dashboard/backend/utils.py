import pandas as pd
import ast
import numpy as np

# ================= CONFIG =================
TIME_MARGIN_MS = 50
WINDOW_SIZE = 10
STEP_SIZE = 3
TARGET_CSI_LEN = 128

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
def preprocess_raw_csv(path):
    df = pd.read_csv(path)

    df["csi_data"] = df["csi"].apply(parse_csi)
    df = df.dropna(subset=["csi_data"])

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df[["esp_id", "timestamp", "rssi", "csi_data"]]

# ================= SPLIT & MERGE =================
def split_and_merge(df):
    rx1 = df[df["esp_id"] == "rx1"].sort_values("timestamp")
    rx2 = df[df["esp_id"] == "rx2"].sort_values("timestamp")

    merged = pd.merge_asof(
        rx1,
        rx2,
        on="timestamp",
        direction="nearest",
        tolerance=pd.Timedelta(milliseconds=TIME_MARGIN_MS),
        suffixes=("_RX1", "_RX2")
    )

    merged = merged.dropna(subset=["rssi_RX2"])

    merged["csi_data_RX1"] = merged["csi_data_RX1"].apply(fix_csi_length)
    merged["csi_data_RX2"] = merged["csi_data_RX2"].apply(fix_csi_length)

    return merged.reset_index(drop=True)

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

# ================= WINDOW AGGREGATION (BACKEND) =================
def build_window_features(merged_df):
    rows = []
    timestamps = []

    for i in range(0, len(merged_df) - WINDOW_SIZE, STEP_SIZE):
        chunk = merged_df.iloc[i:i + WINDOW_SIZE]
        if len(chunk) < WINDOW_SIZE:
            continue

        features = extract_features(chunk)
        rows.append(features)

        # representative timestamp for slider (center of window)
        timestamps.append(chunk["timestamp"].iloc[len(chunk) // 2])

    X = pd.DataFrame(rows)
    return X, timestamps
