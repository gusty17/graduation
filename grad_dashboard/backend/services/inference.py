import time
import joblib
import pandas as pd
import numpy as np
import state.buffers as buffers
from common.feature_engineering import STEP_SIZE, WINDOW_SIZE, parse_csi, split_and_merge, build_window_features
#from common.all_csi_data  import STEP_SIZE, WINDOW_SIZE, parse_csi, split_and_merge, build_window_features
#from common.selected_index  import STEP_SIZE, WINDOW_SIZE, parse_csi, split_and_merge, build_window_features
from services.bigquery_service import insert_prediction

# Load model
model = joblib.load("models/rf_person_count_model.pkl")
scaler = joblib.load("models/scaler.pkl")
feature_columns = joblib.load("models/feature_columns.pkl")


def realtime_prediction_worker(socketio):
    print("🚀 realtime_prediction_worker started")

    while True:
        time.sleep(1)  # Adjust as needed for responsiveness

        print(f"[WORKER] Buffer size: {len(buffers.prediction_buffer)}")

        if len(buffers.prediction_buffer) < WINDOW_SIZE * 3: # Need enough data for both RX1 & RX2 & RX3 
            continue

        print("\n🚀 Enough data collected → starting prediction...\n")

        try:
            df = pd.DataFrame(list(buffers.prediction_buffer))

            required = ["esp_id", "timestamp", "rssi", "csi"]
            if not all(col in df.columns for col in required):
                print("❌ Missing required columns")
                continue

            df["csi_data"] = df["csi"].apply(parse_csi)
            df = df.drop(columns=["csi"])
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        except Exception as e:
            print("❌ Buffer parsing error:", e)
            continue

        #  Merge RX1 & RX2
        merged = split_and_merge(df)

        if merged.empty or len(merged) < WINDOW_SIZE:
            print(f"❌ Not enough merged samples: {len(merged)}")
            continue

        print(f"[MERGED] Rows={len(merged)} | Columns={len(merged.columns)}")

        if merged.empty or len(merged) < 10:
            print("❌ ERROR: Missing one ESP (need at least 2 devices)")
            continue
        #debugging logs
        print(f"[DEBUG] RX1: {len(df[df['esp_id']=='rx1'])}, RX2: {len(df[df['esp_id']=='rx2'])}, RX3: {len(df[df['esp_id']=='rx3'])}")
        print(f"[DEBUG] Merged rows: {len(merged)}")
        # Feature extraction
        X, timestamps = build_window_features(merged)

        print(f"[FEATURES] Shape={X.shape}")

        if X.empty:
            print("❌ ERROR: Feature extraction failed")
            continue

        # Align features
        X = X.reindex(columns=feature_columns, fill_value=0)
        X_scaled = scaler.transform(X)

        # Predict
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
            "confidence": round(confidence * 100, 2),
            "model_version": "rf_v1",
        }

        # Save latest prediction
        with buffers.prediction_lock:
            buffers.latest_prediction = result

        # PRINT RESULT
        print("\n===========inference.py===================")
        print("🧠 NEW PREDICTION")
        print(f"👥 Persons Detected: {pred}")
        print(f"📊 Confidence: {confidence*100:.2f}%")
        print(f"🕒 Time: {timestamps[-1]}")
        print("==============================\n")

        #  Send to frontend via socketio if available
        if socketio:
            socketio.emit("new_prediction", result)
            print("📡 Emitted to frontend:", result)
        else:
            print("📡 SSE stream will handle delivery")

        # Save to BigQuery
        insert_prediction(result)


       # ================= SLIDING WINDOW =================
        remove_count = STEP_SIZE * 3  # 3 ESPs
        for _ in range(remove_count):
            if buffers.prediction_buffer:
                buffers.prediction_buffer.popleft()
                print(f"🧹 Removed {remove_count} samples, buffer size now: {len(buffers.prediction_buffer)}")