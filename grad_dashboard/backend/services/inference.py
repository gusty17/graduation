import time
import joblib
import pandas as pd
import numpy as np

import state.buffers as buffers
from utils import split_and_merge, build_window_features, parse_csi

# ================= LOAD MODEL =================
model = joblib.load("models/rf_person_count_model.pkl")
scaler = joblib.load("models/scaler.pkl")
feature_columns = joblib.load("models/feature_columns.pkl")

PREDICTION_LOG = "realtime_predictions.csv"

if not pd.io.common.file_exists(PREDICTION_LOG):
    pd.DataFrame(columns=[
        "timestamp", "person_count", "confidence"
    ]).to_csv(PREDICTION_LOG, index=False)


def realtime_prediction_worker(socketio):
    print("🚀 realtime_prediction_worker started")

    STEP_SIZE = 3
    MIN_REQUIRED = 50  # minimum buffer before starting

    while True:
        time.sleep(1)

        buffer_size = len(buffers.prediction_buffer)
        print(f"[WORKER] Buffer size: {buffer_size}")

        if buffer_size < MIN_REQUIRED:
            continue

        print("\n🚀 Enough data collected → starting prediction...\n")

        try:
            df = pd.DataFrame(list(buffers.prediction_buffer))

            required = ["esp_id", "timestamp", "rssi", "csi"]
            if not all(col in df.columns for col in required):
                print("❌ Missing required columns")
                continue

            # ================= CSI PARSING =================
            df["csi_data"] = df["csi"].apply(parse_csi)
            df = df.dropna(subset=["csi_data"])

            df = df.drop(columns=["csi"])
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        except Exception as e:
            print("❌ Buffer parsing error:", e)
            continue

        # ================= MERGE RX1 & RX2 =================
        merged = split_and_merge(df)

        print(f"[MERGED] Rows={len(merged)}")

        if merged.empty or len(merged) < 10:
            print("❌ ERROR: Missing RX1 or RX2")
            continue

        # ================= FEATURE EXTRACTION =================
        X, timestamps = build_window_features(merged)

        print(f"[FEATURES] Shape={X.shape}")

        if X.empty:
            print("❌ ERROR: Feature extraction failed")
            continue

        try:
            # ================= ALIGN + SCALE =================
            X = X.reindex(columns=feature_columns, fill_value=0)
            X_scaled = scaler.transform(X)

        except Exception as e:
            print("❌ Scaling error:", e)
            continue

        # ================= PREDICTION =================
        preds = model.predict(X_scaled)
        probs = model.predict_proba(X_scaled)

        # Smooth prediction
        pred_series = pd.Series(preds)
        pred = int(
            pred_series
            .rolling(5, min_periods=1)
            .median()
            .iloc[-1]
        )

        # Smooth confidence
        class_idx = np.where(model.classes_ == pred)[0][0]
        confidence = float(np.mean(probs[-5:, class_idx]))

        result = {
            "timestamp": str(timestamps[-1]),
            "person_count": pred,
            "confidence": round(confidence * 100, 2)
        }

        # ================= SAVE =================
        with buffers.prediction_lock:
            buffers.latest_prediction = result

        print("\n==============================")
        print("🧠 NEW PREDICTION")
        print(f"👥 Persons Detected: {pred}")
        print(f"📊 Confidence: {confidence*100:.2f}%")
        print(f"🕒 Time: {timestamps[-1]}")
        print("==============================\n")

        socketio.emit("new_prediction", result)

        pd.DataFrame([result]).to_csv(
            PREDICTION_LOG,
            mode="a",
            header=False,
            index=False
        )

        # ================= 🔥 SMART POP =================
        remove_count = min(STEP_SIZE, len(buffers.prediction_buffer))
        buffers.prediction_buffer = buffers.prediction_buffer[remove_count:]

        print(f"🧹 Removed {remove_count} processed samples")