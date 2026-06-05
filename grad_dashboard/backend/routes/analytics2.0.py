from flask import Blueprint, jsonify
import os
import pandas as pd

PREDICTION_LOG = "realtime_predictions.csv"

analytics_bp = Blueprint("analytics", __name__)

# Fetch analytics from realtime predictions only
@analytics_bp.route("/analytics", methods=["GET"])
def analytics():
    analytics_data = []

    # Load realtime predictions
    if os.path.exists(PREDICTION_LOG):
        try:
            print(f"📊 Loading realtime predictions from {PREDICTION_LOG}...")
            df = pd.read_csv(PREDICTION_LOG)
            
            if not df.empty:
                # Convert to list of dictionaries
                predictions = df.to_dict('records')
                
                # Group predictions by day (YYYY-MM-DD)
                grouped = {}
                for p in predictions:
                    day = str(p["timestamp"])[:10]  # Extract date part
                    if day not in grouped:
                        grouped[day] = []
                    grouped[day].append(p)

                analytics_data.append({
                    "filename": "realtime_predictions.csv",
                    "days": grouped
                })
                
                print(f"✅ Loaded {len(predictions)} realtime predictions across {len(grouped)} days")
            else:
                print("⚠️  realtime_predictions.csv is empty")
        except Exception as e:
            print(f"⚠️  Error loading realtime predictions: {e}")
    else:
        print(f"⚠️  {PREDICTION_LOG} not found")

    return jsonify(analytics_data)


# 🔥 Fetch raw WiFi CSI data from raw_data folder
@analytics_bp.route("/analytics/raw", methods=["GET"])
def get_raw_data():
    """
    Fetch raw WiFi CSI data collected from MQTT ingestion.
    Returns the contents of raw_data/raw_data.csv
    """
    RAW_DATA_FOLDER = "raw_data"
    RAW_DATA_CSV = os.path.join(RAW_DATA_FOLDER, "raw_data.csv")
    
    if not os.path.exists(RAW_DATA_CSV):
        return jsonify({
            "message": "No raw data available yet",
            "data": []
        }), 200
    
    try:
        df = pd.read_csv(RAW_DATA_CSV)
        records = df.to_dict('records')
        
        print(f"📊 Retrieved {len(records)} raw data records")
        
        return jsonify({
            "count": len(records),
            "data": records
        }), 200
    
    except Exception as e:
        print(f"❌ Error reading raw data: {e}")
        return jsonify({
            "error": str(e),
            "data": []
        }), 500
