import time
import joblib
import pandas as pd
import numpy as np

import state.buffers as buffers
from utils import split_and_merge, build_window_features

model = joblib.load("models/rf_person_count_model.pkl")
scaler = joblib.load("models/scaler.pkl")
feature_columns = joblib.load("models/feature_columns.pkl")

PREDICTION_LOG = "realtime_predictions.csv"

if not pd.io.common.file_exists(PREDICTION_LOG):
    pd.DataFrame(columns=[
        "timestamp", "person_count", "confidence"
    ]).to_csv(PREDICTION_LOG, index=False)


def realtime_prediction_worker():
    """
    Real-time prediction worker:
    - consumes MQTT buffer
    - merges RX1/RX2
    - runs ML model
    - updates shared latest_prediction (SSE-safe)
    """
    print("🚀 realtime_prediction_worker started")

    while True:
        time.sleep(1)

        if len(buffers.prediction_buffer) < 50:
            continue

        try:
            df = pd.DataFrame(list(buffers.prediction_buffer))

            required = ["esp_id", "timestamp", "rssi", "csi"]
            if not all(col in df.columns for col in required):
                continue

            df["csi_data"] = df["csi"]
            df = df.drop(columns=["csi"])
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        except Exception as e:
            print("❌ Buffer parsing error:", e)
            continue

        merged = split_and_merge(df)
        if merged.empty or len(merged) < 10:
            continue

        X, timestamps = build_window_features(merged)
        if X.empty:
            continue

        X = X.reindex(columns=feature_columns, fill_value=0)
        X_scaled = scaler.transform(X)

        preds = model.predict(X_scaled)
        probs = model.predict_proba(X_scaled)

        pred = int(
            pd.Series(preds)
            .rolling(5, min_periods=1)
            .median()
            .iloc[-1]
        )

        class_idx = np.where(model.classes_ == pred)[0][0]
        confidence = float(probs[-1][class_idx])

        result = {
            "timestamp": str(timestamps[-1]),
            "person_count": pred,
            "confidence": round(confidence * 100, 2)
        }

        with buffers.prediction_lock:
            buffers.latest_prediction = result

        print(f"✅ Prediction: {pred} person(s) | Confidence: {confidence*100:.1f}%")

        pd.DataFrame([result]).to_csv(
            PREDICTION_LOG, mode="a", header=False, index=False
        )
