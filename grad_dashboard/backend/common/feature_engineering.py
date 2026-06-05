import pandas as pd
import numpy as np
import ast

# ================= CONFIG =================
TIME_MARGIN_MS = 1000   # increased for real-time stability
WINDOW_SIZE = 30
STEP_SIZE = 10
TARGET_CSI_LEN = 128

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

# ================= FEATURE EXTRACTION =================
def extract_features(chunk):
    csi1 = np.vstack(chunk["csi_data_RX1"])
    csi2 = np.vstack(chunk["csi_data_RX2"])
    csi3 = np.vstack(chunk["csi_data_RX3"])

    features = {}

    rssi1 = chunk["rssi_RX1"].mean()
    rssi2 = chunk["rssi_RX2"].mean()
    rssi3 = chunk["rssi_RX3"].mean()

    features.update({
        "rssi_RX1": rssi1,
        "rssi_RX2": rssi2,
        "rssi_RX3": rssi3,
        "rssi_diff_12": rssi1 - rssi2,
        "rssi_diff_13": rssi1 - rssi3,
        "rssi_diff_23": rssi2 - rssi3,
    })

    def csi_stats(prefix, csi):
        return {
            f"{prefix}_mean": csi.mean(),
            f"{prefix}_std": csi.std(),
            f"{prefix}_energy": np.sum(csi ** 2),
            f"{prefix}_max": csi.max(),
            f"{prefix}_min": csi.min(),
            f"{prefix}_range": csi.max() - csi.min(),
            f"{prefix}_median": np.median(csi),
            f"{prefix}_time_var": np.var(csi, axis=0).mean(),
            f"{prefix}_subcarrier_var": np.var(csi, axis=1).mean(),
        }

    features.update(csi_stats("RX1", csi1))
    features.update(csi_stats("RX2", csi2))
    features.update(csi_stats("RX3", csi3))

    features.update({
        "RX1_RX2_diff_mean": np.mean(csi1 - csi2),
        "RX1_RX2_diff_std": np.std(csi1 - csi2),
        "RX1_RX3_diff_mean": np.mean(csi1 - csi3),
        "RX1_RX3_diff_std": np.std(csi1 - csi3),
        "RX2_RX3_diff_mean": np.mean(csi2 - csi3),
        "RX2_RX3_diff_std": np.std(csi2 - csi3),
    })

    features.update({
        "RX1_RX2_corr": np.corrcoef(csi1.flatten(), csi2.flatten())[0,1],
        "RX1_RX3_corr": np.corrcoef(csi1.flatten(), csi3.flatten())[0,1],
        "RX2_RX3_corr": np.corrcoef(csi2.flatten(), csi3.flatten())[0,1],
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