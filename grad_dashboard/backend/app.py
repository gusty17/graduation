from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import os
import pandas as pd
import numpy as np

from utils import (
    preprocess_raw_csv,
    split_and_merge,
    build_window_features
)

# ================= APP SETUP =================
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= LOAD MODEL & TOOLS =================
model = joblib.load("rf_person_count_model.pkl")
scaler = joblib.load("scaler.pkl")
feature_columns = joblib.load("feature_columns.pkl")

# ================= SHARED PREDICTION LOGIC =================
def run_prediction_on_csv(path):
    # -------- Preprocess raw CSI --------
    df = preprocess_raw_csv(path)

    # -------- Split RX1 / RX2 and merge by time --------
    merged = split_and_merge(df)

    if merged.empty or len(merged) < 10:
        return []

    # -------- Build WINDOW-BASED features --------
    X, timestamps = build_window_features(merged)

    if X.empty:
        return []

    # -------- Align features --------
    X = X.reindex(columns=feature_columns, fill_value=0)

    # -------- Scale --------
    X_scaled = scaler.transform(X)

    # -------- Predict --------
    preds = model.predict(X_scaled)
    probs = model.predict_proba(X_scaled)

    # -------- Temporal smoothing --------
    preds_smoothed = (
        pd.Series(preds)
        .rolling(window=5, center=True, min_periods=1)
        .median()
        .round()
        .astype(int)
    )

    results = []
    for i in range(len(preds_smoothed)):
        count = int(preds_smoothed.iloc[i])

        class_index = int(np.where(model.classes_ == count)[0][0])
        confidence = float(probs[i][class_index])

        results.append({
            "timestamp": str(timestamps[i]),
            "person_count": count,
            "confidence": round(confidence * 100, 2)
        })

    return results


# ================= API: SINGLE FILE PREDICTION =================
@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "CSV file required"}), 400

    file = request.files["file"]
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    results = run_prediction_on_csv(path)

    if not results:
        return jsonify({
            "error": "Not enough valid data for prediction"
        }), 400

    return jsonify(results)


# ================= API: ANALYTICS (ALL FILES) =================
@app.route("/analytics", methods=["GET"])
def analytics():
    analytics_data = []

    for filename in os.listdir(UPLOAD_FOLDER):
        if not filename.endswith(".csv"):
            continue

        path = os.path.join(UPLOAD_FOLDER, filename)
        predictions = run_prediction_on_csv(path)

        if not predictions:
            continue

        # -------- Group by day --------
        grouped_by_day = {}
        for p in predictions:
            day = p["timestamp"][:10]  # YYYY-MM-DD
            grouped_by_day.setdefault(day, []).append(p)

        analytics_data.append({
            "filename": filename,
            "days": grouped_by_day
        })

    return jsonify(analytics_data)


# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
