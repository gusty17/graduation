from flask import Blueprint, request, jsonify
import os
from services.csv_predictor import run_prediction_on_csv

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

predict_bp = Blueprint("predict", __name__)

@predict_bp.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "CSV file required"}), 400

    file = request.files["file"]
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    results = run_prediction_on_csv(path)
    if not results:
        return jsonify({"error": "Not enough valid data"}), 400

    return jsonify(results)
