import joblib
import pandas as pd
import numpy as np
from utils import preprocess_raw_csv, split_and_merge, build_window_features

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
    5. Smooth predictions with 5-sample median
    6. Return results with confidence scores
    
    Returns: List of predictions with timestamps, person_count, and confidence
    """
    try:
        # Load and preprocess
        df = preprocess_raw_csv(path)
        
        if df.empty:
            print(f"⚠️  No valid data in {path}")
            return []
        
        print(f"✅ Loaded {len(df)} rows from {path}")
        
        # Merge RX1 + RX2
        merged = split_and_merge(df)

        if merged.empty or len(merged) < 10:
            print(f"⚠️  Not enough merged data: {len(merged)} rows")
            return []

        print(f"✅ Merged: {len(merged)} paired RX1/RX2 samples")

        # Extract features
        X, timestamps = build_window_features(merged)
        if X.empty:
            print(f"⚠️  No features extracted")
            return []

        print(f"✅ Extracted features: {len(X)} windows")

        # Prepare for model
        X = X.reindex(columns=feature_columns, fill_value=0)
        X_scaled = scaler.transform(X)

        # Run predictions
        preds = model.predict(X_scaled)
        probs = model.predict_proba(X_scaled)

        # Smooth with 5-sample rolling median
        preds_smoothed = (
            pd.Series(preds)
            .rolling(window=5, center=True, min_periods=1)
            .median()
            .round()
            .astype(int)
        )

        # Build results
        results = []
        for i in range(len(preds_smoothed)):
            count = int(preds_smoothed.iloc[i])
            
            # Get confidence for this prediction
            class_index = np.where(model.classes_ == count)[0]
            if len(class_index) == 0:
                print(f"⚠️  Unknown class {count}, skipping")
                continue
            
            class_index = class_index[0]
            confidence = float(probs[i][class_index])

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

