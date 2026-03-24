import joblib 
import pandas as pd
import numpy as np
from utils import preprocess_raw_csv, split_and_merge, build_window_features

# ================= LOAD MODEL =================
model = joblib.load("models/rf_person_count_model.pkl")
scaler = joblib.load("models/scaler.pkl")
feature_columns = joblib.load("models/feature_columns.pkl")


def run_prediction_on_csv(path):
    """
    Run batch prediction on an uploaded CSV file.

    Process:
    1. Load and preprocess raw CSV
    2. Merge RX1 + RX2 packets
    3. Extract sliding-window features
    4. Apply ML model
    5. Smooth predictions with rolling median (same as realtime)
    6. Return results with confidence scores

    Returns: List of predictions with timestamps, person_count, and confidence
    """
    try:
        # ================= LOAD & PREPROCESS =================
        df = preprocess_raw_csv(path)
        
        if df.empty:
            print(f"⚠️ No valid data in {path}")
            return []
        
        print(f"✅ Loaded {len(df)} rows from {path}")
        
        # ================= MERGE RX1 + RX2 =================
        merged = split_and_merge(df)

        if merged.empty or len(merged) < 10:
            print(f"⚠️ Not enough merged data: {len(merged)} rows")
            return []

        print(f"✅ Merged: {len(merged)} paired RX1/RX2 samples")

        # ================= FEATURE EXTRACTION =================
        X, timestamps = build_window_features(merged)

        if X.empty:
            print("⚠️ No features extracted")
            return []

        print(f"✅ Extracted features: {len(X)} windows")

        # ================= ALIGN + SCALE =================
        X = X.reindex(columns=feature_columns, fill_value=0)
        X_scaled = scaler.transform(X)

        # ================= PREDICTION =================
        preds = model.predict(X_scaled)
        probs = model.predict_proba(X_scaled)

        # ================= SMOOTH PREDICTIONS =================
        preds_smoothed = (
            pd.Series(preds)
            .rolling(5, min_periods=1)
            .median()
            .round()
            .astype(int)
        )

        # ================= BUILD RESULTS =================
        results = []

        for i in range(len(preds_smoothed)):
            count = int(preds_smoothed.iloc[i])

            # Find class index
            class_index = np.where(model.classes_ == count)[0]

            if len(class_index) == 0:
                print(f"⚠️ Unknown class {count}, skipping")
                confidence = 0.0
            else:
                class_index = class_index[0]

                # 🔥 Smooth confidence (last 5 steps like realtime)
                start = max(0, i - 4)
                confidence = float(
                    np.mean(probs[start:i+1, class_index])
                )

            results.append({
                "timestamp": str(timestamps[i]),
                "person_count": count,
                "confidence": round(confidence * 100, 2)
            })

        print(f"✅ Predictions complete: {len(results)} results")
        return results

    except Exception as e:
        print(f"❌ Error running prediction on {path}: {e}")
        import traceback
        traceback.print_exc()
        return []