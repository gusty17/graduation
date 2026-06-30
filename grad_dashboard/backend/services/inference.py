import time
import os
import joblib
import pandas as pd
import numpy as np
import state.buffers as buffers
from common.preprocessing import (
    WINDOW_SEC, MIN_SAMPLES_PER_WINDOW,
    clean_dataframe, build_windows, apply_baseline, compute_baseline,
)
# Load model artifacts (trained by grad_model_trainging on preprocessing.py features).
model = joblib.load("models/rf_person_count_model.pkl")
scaler = joblib.load("models/scaler.pkl")
feature_columns = joblib.load("models/feature_columns.pkl")

# valid_mask is written to backend/models/ by grad_model_trainging/processing.py.
# Without it live CSI can't be aligned to the trained subcarriers, so fail loudly
# instead of with a bare FileNotFoundError deep in joblib.
VALID_MASK_PATH = "models/valid_mask.pkl"
if not os.path.exists(VALID_MASK_PATH):
    raise FileNotFoundError(
        f"{VALID_MASK_PATH} not found — run grad_model_trainging/processing.py to "
        "regenerate it before starting inference."
    )
valid_mask = joblib.load(VALID_MASK_PATH)

# Deployment empty-room baseline (per-feature mean of an empty capture). The
# model is trained on baseline-normalized features, so live windows MUST be
# normalized the same way. Generate it with calibrate_baseline.py while the
# room is empty. Without it, predictions are not valid.
BASELINE_PATH = "models/deployment_baseline.pkl"
# GCS object the cloud job (pipeline/cloud_job.py) loads the baseline from.
BASELINE_GCS_BLOB = "models/deployment_baseline.pkl"
deployment_baseline = joblib.load(BASELINE_PATH) if os.path.exists(BASELINE_PATH) else None
if deployment_baseline is None:
    print("⚠️  No deployment_baseline.pkl found - run calibrate_baseline.py on an "
          "EMPTY room first. Predictions are unreliable until then.")


def _upload_baseline_to_gcs(local_path):
    """Push the freshly computed empty-room baseline to GCS models/ so the cloud
    job normalizes its windows the same way live inference does. Best-effort: a
    failure (e.g. no GCS credentials on a local-only test machine) is logged, not
    fatal — the baseline is already saved locally for live prediction."""
    try:
        from services.gcs_service import upload_file
        upload_file(local_path, BASELINE_GCS_BLOB)
        print(f"☁️  Baseline uploaded to gs://.../{BASELINE_GCS_BLOB} for the cloud job")
    except Exception as e:
        print(f"⚠️  Could not upload baseline to GCS ({e}). It is saved locally; "
              f"upload {local_path} to models/{os.path.basename(local_path)} "
              f"manually before running the cloud job.")


def _run_calibration_phase(socketio):
    """Empty-room calibration. For the first CALIBRATION_SECONDS the room must
    be empty; we accumulate that CSI (via udp_service) and then compute the
    deployment baseline from it. Emits a per-second countdown the UI can show.
    """
    global deployment_baseline

    duration = buffers.CALIBRATION_SECONDS

    if os.environ.get("SKIP_CALIBRATION") == "1":
        buffers.calibration_status.update(phase="predicting", remaining=0, duration=duration)
        print("⏭️  Calibration skipped (SKIP_CALIBRATION=1). Using existing baseline if present.")
        return

    print(f"🧪 CALIBRATION: keep the room EMPTY for {duration}s...")
    start = time.time()
    while True:
        remaining = max(0, int(round(duration - (time.time() - start))))
        buffers.calibration_status.update(phase="calibrating", remaining=remaining, duration=duration)
        if socketio:
            socketio.emit("calibration_status", dict(buffers.calibration_status))
        if remaining <= 0:
            break
        time.sleep(1)

    # Build the baseline from everything captured while empty.
    with buffers.calibration_lock:
        rows = list(buffers.calibration_buffer)
        buffers.calibration_buffer.clear()

    try:
        if not rows:
            print("❌ Calibration: no data captured (are all 3 ESPs running?). "
                  "Predictions will be unreliable.")
        else:
            df = pd.DataFrame(rows)
            cleaned, _ = clean_dataframe(df, valid_mask)
            X = build_windows(cleaned)
            if X.empty:
                print("❌ Calibration: no windows extracted - check receiver coverage. "
                      "Predictions will be unreliable.")
            else:
                baseline = compute_baseline(X)
                joblib.dump(baseline, BASELINE_PATH)
                deployment_baseline = baseline
                print(f"✅ Calibration complete: baseline from {len(X)} empty-room windows "
                      f"saved to {BASELINE_PATH}")
                _upload_baseline_to_gcs(BASELINE_PATH)
    except Exception as e:
        print("❌ Calibration error:", e)

    buffers.calibration_status.update(phase="predicting", remaining=0, duration=duration)
    if socketio:
        socketio.emit("calibration_status", dict(buffers.calibration_status))


def realtime_prediction_worker(socketio):
    print("🚀 realtime_prediction_worker started")

    # Empty-room calibration must finish before any prediction is emitted.
    _run_calibration_phase(socketio)

    while True:
        time.sleep(5)  # one prediction per 5-second window (WINDOW_SEC)

        print(f"[WORKER] Buffer size: {len(buffers.prediction_buffer)}")

        if len(buffers.prediction_buffer) < MIN_SAMPLES_PER_WINDOW * 3:  # Need enough data for RX1 & RX2 & RX3
            continue

        print("\n🚀 Enough data collected → starting prediction...\n")

        try:
            df = pd.DataFrame(list(buffers.prediction_buffer))

            required = ["esp_id", "timestamp", "rssi", "csi"]
            if not all(col in df.columns for col in required):
                print("❌ Missing required columns")
                continue

            t0 = pd.to_datetime(df["timestamp"], errors="coerce").min()

        except Exception as e:
            print("❌ Buffer parsing error:", e)
            continue

        #  Clean + calibrate CSI (subcarrier nulls, Hampel filtering, phase sanitization)
        try:
            cleaned, _ = clean_dataframe(df, valid_mask)
        except Exception as e:
            print("❌ Cleaning error:", e)
            continue

        if cleaned.empty:
            print("❌ ERROR: No valid rows after cleaning")
            continue

        #debugging logs
        print(f"[DEBUG] RX1: {len(df[df['esp_id']=='rx1'])}, RX2: {len(df[df['esp_id']=='rx2'])}, RX3: {len(df[df['esp_id']=='rx3'])}")
        print(f"[DEBUG] Cleaned rows: {len(cleaned)}")

        # Feature extraction
        X = build_windows(cleaned)

        print(f"[FEATURES] Shape={X.shape}")

        if X.empty:
            print("❌ ERROR: Feature extraction failed")
            continue

        # Normalize against the empty-room baseline so features match how the
        # model was trained (deviation from empty, not absolute magnitude).
        if deployment_baseline is not None:
            X = apply_baseline(X, deployment_baseline)

        # window_start_t is elapsed seconds, not a model feature - use it to
        # recover each window's wall-clock timestamp, then drop it from X.
        timestamps = [t0 + pd.Timedelta(seconds=ws + WINDOW_SEC / 2) for ws in X["window_start_t"]]
        X = X.drop(columns=["window_start_t"])

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

        # Local-only test harness: predictions are shown here / streamed to the
        # UI, never written to the cloud (BigQuery). Cloud predictions come from
        # pipeline/cloud_job.py instead.
