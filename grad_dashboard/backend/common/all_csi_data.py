import pandas as pd
import numpy as np
import ast

# ================= CONFIG =================
TIME_MARGIN_MS = 1000   # increased for real-time stability
WINDOW_SIZE = 30
STEP_SIZE = 10
TARGET_CSI_LEN = 128
SELECTED_IDX = list(range(10, 90))  # Select indices 10-90

# ================= CSI PARSING =================
def parse_csi(x):
    try:
        return ast.literal_eval(x) if isinstance(x, str) else x
    except Exception:
        return None


def fix_csi_length(csi):
    csi = list(csi)

    if len(csi) > TARGET_CSI_LEN:
        return csi[:TARGET_CSI_LEN]

    if len(csi) < TARGET_CSI_LEN:
        return csi + [0.0] * (TARGET_CSI_LEN - len(csi))

    return csi


def to_amplitude(csi):
    csi = np.array(csi)
    real = csi[::2]
    imag = csi[1::2]
    return np.sqrt(real**2 + imag**2)

# ================= PREPROCESS =================
def preprocess_raw_csv(path):
    df = pd.read_csv(path)

    df["csi_data"] = df["csi"].apply(parse_csi)
    df = df.dropna(subset=["csi_data"])

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df[["esp_id", "timestamp", "rssi", "csi_data"]]

# ================= MERGING =================
def split_and_merge(df):
    rx1 = df[df["esp_id"] == "rx1"].sort_values("timestamp")
    rx2 = df[df["esp_id"] == "rx2"].sort_values("timestamp")
    rx3 = df[df["esp_id"] == "rx3"].sort_values("timestamp")

    if rx1.empty or rx2.empty or rx3.empty:
        return pd.DataFrame()

    merged = pd.merge_asof(
        rx1, rx2,
        on="timestamp",
        direction="nearest",
        tolerance=pd.Timedelta(milliseconds=TIME_MARGIN_MS),
        suffixes=("_RX1", "_RX2")
    )

    rx3 = rx3.rename(columns={
        "esp_id": "esp_id_RX3",
        "rssi": "rssi_RX3",
        "csi_data": "csi_data_RX3"
    })

    merged = pd.merge_asof(
        merged,
        rx3,
        on="timestamp",
        direction="nearest",
        tolerance=pd.Timedelta(milliseconds=TIME_MARGIN_MS)
    )

    merged = merged.dropna(subset=["rssi_RX2", "rssi_RX3"])

    merged["csi_data_RX1"] = merged["csi_data_RX1"].apply(fix_csi_length).apply(to_amplitude)
    merged["csi_data_RX2"] = merged["csi_data_RX2"].apply(fix_csi_length).apply(to_amplitude)
    merged["csi_data_RX3"] = merged["csi_data_RX3"].apply(fix_csi_length).apply(to_amplitude)

    return merged.reset_index(drop=True)

# ================= FEATURE EXTRACTION (RAW CSI + MIN/MAX ONLY) =================
def extract_features(chunk):
    """
    Extract raw CSI data with selected indices (10-90) and compute min/max
    """
    csi1 = np.vstack(chunk["csi_data_RX1"])
    csi2 = np.vstack(chunk["csi_data_RX2"])
    csi3 = np.vstack(chunk["csi_data_RX3"])

    # Select indices 10-90
    csi1 = csi1[:, SELECTED_IDX]
    csi2 = csi2[:, SELECTED_IDX]
    csi3 = csi3[:, SELECTED_IDX]

    features = {}

    # Add all raw CSI values for selected subcarriers (flattened)
    for i, idx in enumerate(SELECTED_IDX):
        features[f"RX1_subcarrier_{i}"] = csi1[:, i].mean()  # mean value for each subcarrier
        features[f"RX2_subcarrier_{i}"] = csi2[:, i].mean()
        features[f"RX3_subcarrier_{i}"] = csi3[:, i].mean()

    # Min and max statistics
    features.update({
        "RX1_min": csi1.min(),
        "RX1_max": csi1.max(),
        "RX2_min": csi2.min(),
        "RX2_max": csi2.max(),
        "RX3_min": csi3.min(),
        "RX3_max": csi3.max(),
    })

    return features

# ================= WINDOW =================
def build_window_features(merged_df):
    rows = []
    timestamps = []

    for i in range(0, len(merged_df) - WINDOW_SIZE, STEP_SIZE):
        chunk = merged_df.iloc[i:i + WINDOW_SIZE]

        if len(chunk) < WINDOW_SIZE:
            continue

        features = extract_features(chunk)
        rows.append(features)
        timestamps.append(chunk["timestamp"].iloc[len(chunk)//2])

    return pd.DataFrame(rows), timestamps
