from flask import Blueprint, jsonify
from services.gcs_service import read_all, RAW_GCS_PREFIX, PREDICTIONS_PREFIX

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics", methods=["GET"])
def analytics():
    df = read_all(PREDICTIONS_PREFIX)

    if df.empty:
        print("⚠️  No predictions found in GCS")
        return jsonify([])

    predictions = df.to_dict("records")

    grouped = {}
    for p in predictions:
        day = str(p["timestamp"])[:10]
        grouped.setdefault(day, []).append(p)

    print(f"✅ Loaded {len(predictions)} predictions across {len(grouped)} days")
    return jsonify([{"filename": "realtime_predictions", "days": grouped}])


@analytics_bp.route("/analytics/raw", methods=["GET"])
def get_raw_data():
    df = read_all(RAW_GCS_PREFIX)

    if df.empty:
        return jsonify({"message": "No raw data available yet", "data": []}), 200

    records = df.to_dict("records")
    print(f"📊 Retrieved {len(records)} raw data records from GCS")
    return jsonify({"count": len(records), "data": records}), 200
