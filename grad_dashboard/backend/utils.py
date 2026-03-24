import pandas as pd
import ast
import numpy as np
import json
import os

# ================= CONFIG =================
TIME_MARGIN_MS = 500
WINDOW_SIZE = 10
STEP_SIZE = 3
TARGET_CSI_LEN = 128

# ================= LOAD SELECTED INDICES =================
#  Automatically load best subcarriers selected by model
# SELECTED_IDX = list(range(TARGET_CSI_LEN)) # default (use all subcarriers if file not found)
SELECTED_IDX_PATH = "models/selected_idx.json"

if os.path.exists(SELECTED_IDX_PATH):
    with open(SELECTED_IDX_PATH, "r") as f:
        SELECTED_IDX = json.load(f)
    print(f"✅ Loaded {len(SELECTED_IDX)} selected subcarriers")
else:
    # fallback (first run before training)
    SELECTED_IDX = list(range(TARGET_CSI_LEN))
    print("⚠️ selected_idx.json not found → using all subcarriers")

# ================= CSI PARSING =================
def parse_csi(x):
    """
    Convert CSI string "[1,2,3,...]" to Python list
    """
    try:
        return ast.literal_eval(x) if isinstance(x, str) else x
    except Exception:
        return None


def fix_csi_length(csi):
    """
    Pad or truncate CSI to fixed length
    """
    csi = list(csi)

    if len(csi) > TARGET_CSI_LEN:
        return csi[:TARGET_CSI_LEN]

    if len(csi) < TARGET_CSI_LEN:
        return csi + [0.0] * (TARGET_CSI_LEN - len(csi))

    return csi

# ================= PREPROCESS RAW CSV =================
def preprocess_raw_csv(path):
    df = pd.read_csv(path)

    df["csi_data"] = df["csi"].apply(parse_csi)
    df = df.dropna(subset=["csi_data"])

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df[["esp_id", "timestamp", "rssi", "csi_data"]]

# ================= SPLIT & MERGE RX1 / RX2 =================
def split_and_merge(df):
    rx1 = df[df["esp_id"] == "rx1"].sort_values("timestamp")
    rx2 = df[df["esp_id"] == "rx2"].sort_values("timestamp")

    if rx1.empty or rx2.empty:
        print(f"⚠️ split_and_merge: rx1={len(rx1)}, rx2={len(rx2)}")
        return pd.DataFrame()

    merged = pd.merge_asof(
        rx1,
        rx2,
        on="timestamp",
        direction="nearest",
        tolerance=pd.Timedelta(milliseconds=TIME_MARGIN_MS),
        suffixes=("_RX1", "_RX2")
    )

    merged = merged.dropna(subset=["rssi_RX2"])

    # Ensure CSI is fixed length
    merged["csi_data_RX1"] = merged["csi_data_RX1"].apply(fix_csi_length)
    merged["csi_data_RX2"] = merged["csi_data_RX2"].apply(fix_csi_length)

    return merged.reset_index(drop=True)

# ================= FEATURE EXTRACTION =================
def extract_features(chunk):
    """
    Extract features using selected subcarriers (IMPORTANT)
    """
    if len(chunk) < WINDOW_SIZE:
        return {}

    csi1 = np.vstack(chunk["csi_data_RX1"])
    csi2 = np.vstack(chunk["csi_data_RX2"])

    # 🔥 Use selected subcarriers only
    csi1 = csi1[:, SELECTED_IDX]
    csi2 = csi2[:, SELECTED_IDX]

    feat = {}

    # RSSI features
    feat["rssi_RX1"] = chunk["rssi_RX1"].mean()
    feat["rssi_RX2"] = chunk["rssi_RX2"].mean()

    # Statistical features
    csi1_mean = np.mean(csi1, axis=0)
    csi1_std = np.std(csi1, axis=0)

    csi2_mean = np.mean(csi2, axis=0)
    csi2_std = np.std(csi2, axis=0)

    # Add per-subcarrier features
    for i in range(len(SELECTED_IDX)):
        feat[f"RX1_mean_{i}"] = csi1_mean[i]
        feat[f"RX1_std_{i}"] = csi1_std[i]
        feat[f"RX2_mean_{i}"] = csi2_mean[i]
        feat[f"RX2_std_{i}"] = csi2_std[i]

    # Difference between receivers
    diff = csi1_mean - csi2_mean
    for i in range(len(diff)):
        feat[f"diff_{i}"] = diff[i]

    return feat

# ================= WINDOW AGGREGATION =================
def build_window_features(merged_df):
    rows = []
    timestamps = []

    for i in range(0, len(merged_df) - WINDOW_SIZE, STEP_SIZE):
        chunk = merged_df.iloc[i:i + WINDOW_SIZE]

        if len(chunk) < WINDOW_SIZE:
            continue

        features = extract_features(chunk)

        if not features:
            continue

        rows.append(features)

        timestamps.append(
            chunk["timestamp"].iloc[len(chunk) // 2]
        )

    X = pd.DataFrame(rows)

    return X, timestamps