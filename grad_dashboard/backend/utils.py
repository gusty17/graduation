import pandas as pd
import ast
import numpy as np

# ================= CONFIG =================
TIME_MARGIN_MS = 50        # max allowed RX1–RX2 timestamp difference
WINDOW_SIZE = 10           # samples per window
STEP_SIZE = 3              # sliding window step
TARGET_CSI_LEN = 128       # fixed CSI length

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
    """
    Load raw CSI CSV from disk
    """
    df = pd.read_csv(path)

    df["csi_data"] = df["csi"].apply(parse_csi)
    df = df.dropna(subset=["csi_data"])

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df[["esp_id", "timestamp", "rssi", "csi_data"]]

# ================= SPLIT & MERGE RX1 / RX2 =================
def split_and_merge(df):
    """
    Merge RX1 and RX2 packets by nearest timestamp.
    
    Pairs RX1 and RX2 samples within TIME_MARGIN_MS of each other.
    Returns merged DataFrame with RX1 and RX2 samples side-by-side.
    """
    rx1 = df[df["esp_id"] == "rx1"].sort_values("timestamp")
    rx2 = df[df["esp_id"] == "rx2"].sort_values("timestamp")

    if rx1.empty or rx2.empty:
        print(f"⚠️  split_and_merge: rx1={len(rx1)} rows, rx2={len(rx2)} rows")
        return pd.DataFrame()

    merged = pd.merge_asof(
        rx1,
        rx2,
        on="timestamp",
        direction="nearest",
        tolerance=pd.Timedelta(milliseconds=TIME_MARGIN_MS),
        suffixes=("_RX1", "_RX2")
    )

    # Remove rows where RX2 is missing
    merged = merged.dropna(subset=["rssi_RX2"])

    # Ensure CSI data is fixed length
    merged["csi_data_RX1"] = merged["csi_data_RX1"].apply(fix_csi_length)
    merged["csi_data_RX2"] = merged["csi_data_RX2"].apply(fix_csi_length)

    return merged.reset_index(drop=True)

# ================= FEATURE EXTRACTION =================
def extract_features(chunk):
    """
    Extract statistical CSI + RSSI features from one window
    """
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

# ================= WINDOW AGGREGATION =================
def build_window_features(merged_df):
    """
    Build sliding-window features for ML
    """
    rows = []
    timestamps = []

    for i in range(0, len(merged_df) - WINDOW_SIZE, STEP_SIZE):
        chunk = merged_df.iloc[i:i + WINDOW_SIZE]

        if len(chunk) < WINDOW_SIZE:
            continue

        features = extract_features(chunk)
        rows.append(features)

        # center timestamp for visualization
        timestamps.append(chunk["timestamp"].iloc[len(chunk) // 2])

    X = pd.DataFrame(rows)
    return X, timestamps
