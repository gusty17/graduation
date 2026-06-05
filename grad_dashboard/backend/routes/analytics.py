from flask import Blueprint, jsonify
import os
from services.csv_predictor import run_prediction_on_csv

UPLOAD_FOLDER = "uploads"

analytics_bp = Blueprint("analytics", __name__)

#Fetch analytics from all uploaded CSV files.
@analytics_bp.route("/analytics", methods=["GET"])
def analytics():
    analytics_data = []

    # Ensure upload folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        print(f"⚠️  Upload folder not found: {UPLOAD_FOLDER}")
        return jsonify(analytics_data)

    # Process each CSV file
    csv_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(".csv")]
    
    if not csv_files:
        print("⚠️  No CSV files in uploads/")
        return jsonify(analytics_data)

    for filename in csv_files:
        path = os.path.join(UPLOAD_FOLDER, filename)
        
        try:
            print(f"📊 Processing {filename}...")
            predictions = run_prediction_on_csv(path)

            if not predictions:
                print(f"⚠️  No predictions for {filename}")
                continue

            # Group predictions by day (YYYY-MM-DD)
            grouped = {}
            for p in predictions:
                day = p["timestamp"][:10]  # Extract date part
                if day not in grouped:
                    grouped[day] = []
                grouped[day].append(p)

            analytics_data.append({
                "filename": filename,
                "days": grouped
            })
            
            print(f"✅ {filename}: {len(predictions)} predictions across {len(grouped)} days")

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
            continue

    return jsonify(analytics_data)
