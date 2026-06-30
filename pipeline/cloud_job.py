"""
Cloud Run Job — CSI Pipeline (preprocessing.py edition)
Runs on a schedule (Cloud Scheduler every 10 min).

Uses the SAME feature pipeline as local inference (preprocessing.py): the model
is trained on baseline-normalized window features, so the cloud MUST run
clean_dataframe → build_windows → apply_baseline with the same valid_mask and
the deployment empty-room baseline.

Flow:
  1. List unprocessed raw CSVs in GCS raw/
  2. Download + concatenate all into one DataFrame
  3. clean_dataframe → build_windows → apply_baseline   (preprocessing.py)
  4. Load model artifacts from GCS models/
       rf_person_count_model.pkl, scaler.pkl, feature_columns.pkl,
       valid_mask.pkl (required), deployment_baseline.pkl (empty-room baseline)
  5. Predict on all windows
  6. Batch insert all predictions into BigQuery
  7. Move processed raw CSVs to raw/done/
"""

import os
import io
import joblib
import tempfile
import pandas as pd
import numpy as np
from google.cloud import storage, bigquery
from google.oauth2 import service_account
from datetime import datetime, timezone

from preprocessing import WINDOW_SEC, clean_dataframe, build_windows, apply_baseline

# ── Config ────────────────────────────────────────────────────────────────────
BUCKET_NAME        = os.environ["GCS_BUCKET_NAME"]
PROJECT_ID         = os.environ["GOOGLE_CLOUD_PROJECT"]
DATASET_ID         = "occupancy_analytics"
TABLE_ID           = "occupancy_predictions"
MODEL_VERSION      = "rf_v1"
RAW_PREFIX         = "raw"
DONE_PREFIX        = "raw/done"
MODELS_PREFIX      = "models"
CREDENTIALS_PATH   = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")


# ── GCP Clients ───────────────────────────────────────────────────────────────
def _get_gcs_client():
    if CREDENTIALS_PATH and os.path.exists(CREDENTIALS_PATH):
        return storage.Client.from_service_account_json(CREDENTIALS_PATH)
    return storage.Client()


def _get_bq_client():
    if CREDENTIALS_PATH and os.path.exists(CREDENTIALS_PATH):
        creds = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
        return bigquery.Client(credentials=creds, project=creds.project_id)
    return bigquery.Client()


# ── Load model artifacts from GCS ─────────────────────────────────────────────
def load_artifacts(gcs_client):
    """Download every model artifact from GCS models/. valid_mask is required by
    the cleaning step; deployment_baseline is required for valid predictions but
    handled gracefully (warn) so the job at least runs before it's uploaded."""
    bucket = gcs_client.bucket(BUCKET_NAME)

    def _load(name, required=True):
        blob = bucket.blob(f"{MODELS_PREFIX}/{name}")
        if not blob.exists():
            if required:
                raise FileNotFoundError(
                    f"Required model artifact missing: gs://{BUCKET_NAME}/{MODELS_PREFIX}/{name}"
                )
            print(f"[MODEL] ⚠️  Optional artifact not found: {name}")
            return None
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            blob.download_to_filename(f.name)
            obj = joblib.load(f.name)
        print(f"[MODEL] Loaded {name} from GCS")
        return obj

    model           = _load("rf_person_count_model.pkl")
    scaler          = _load("scaler.pkl")
    feature_columns = _load("feature_columns.pkl")
    valid_mask      = _load("valid_mask.pkl")
    baseline        = _load("deployment_baseline.pkl", required=False)
    if baseline is None:
        print("[MODEL] ⚠️  No deployment_baseline.pkl — predictions will NOT be "
              "baseline-normalized and will be unreliable. Upload the empty-room "
              "baseline produced by the backend calibration.")
    return model, scaler, feature_columns, valid_mask, baseline


# ── Read unprocessed raw CSVs from GCS ────────────────────────────────────────
def fetch_raw_blobs(gcs_client):
    bucket = gcs_client.bucket(BUCKET_NAME)
    all_blobs = list(bucket.list_blobs(prefix=f"{RAW_PREFIX}/"))
    # Exclude anything already in raw/done/
    blobs = [b for b in all_blobs if not b.name.startswith(f"{DONE_PREFIX}/") and b.name.endswith(".csv")]
    print(f"[GCS] Found {len(blobs)} unprocessed raw CSV(s)")
    return blobs


def download_and_concat(blobs):
    frames = []
    for blob in blobs:
        content = blob.download_as_bytes()
        try:
            df = pd.read_csv(io.BytesIO(content))
            if not df.empty:
                frames.append(df)
        except Exception as e:
            print(f"[WARN] Could not read {blob.name}: {e}")
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    print(f"[DATA] Combined {len(combined)} rows from {len(frames)} file(s)")
    return combined


# ── Run predictions ────────────────────────────────────────────────────────────
def run_predictions(df, model, scaler, feature_columns, valid_mask, baseline):
    required = ["esp_id", "timestamp", "rssi", "csi"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"[WARN] Missing columns {missing} — skipping")
        return []

    # Wall-clock origin to recover each window's timestamp (build_windows works
    # in elapsed seconds relative to the earliest row).
    t0 = pd.to_datetime(df["timestamp"], errors="coerce").min()

    # Clean + calibrate CSI (subcarrier nulls, Hampel, phase) using valid_mask.
    cleaned, _ = clean_dataframe(df, valid_mask)
    if cleaned.empty:
        print("[WARN] No valid rows after cleaning — skipping")
        return []

    X = build_windows(cleaned)
    if X.empty:
        print("[WARN] Feature extraction returned empty — skipping")
        return []

    # Normalize against the empty-room baseline so features match training
    # (deviation from empty, not absolute magnitude).
    if baseline is not None:
        X = apply_baseline(X, baseline)

    timestamps = [t0 + pd.Timedelta(seconds=ws + WINDOW_SEC / 2) for ws in X["window_start_t"]]
    X = X.drop(columns=["window_start_t"])

    X = X.reindex(columns=feature_columns, fill_value=0)
    X_scaled = scaler.transform(X)

    preds = model.predict(X_scaled)
    probs = model.predict_proba(X_scaled)

    preds_smoothed = (
        pd.Series(preds)
        .rolling(window=5, center=True, min_periods=1)
        .median()
        .round()
        .astype(int)
    )

    results = []
    for i, ts in enumerate(timestamps):
        count = int(preds_smoothed.iloc[i])
        class_idx = np.where(model.classes_ == count)[0]
        if len(class_idx) == 0:
            continue
        start = max(0, i - 4)
        confidence = float(np.mean(probs[start:i + 1, class_idx[0]]))
        results.append({
            "timestamp": str(ts),
            "person_count": count,
            "confidence": round(confidence * 100, 2),
        })

    print(f"[PREDICT] Generated {len(results)} predictions")
    return results


# ── Batch insert into BigQuery ─────────────────────────────────────────────────
def insert_predictions_batch(bq_client, records):
    if not records:
        return
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    rows = [
        {
            "timestamp":    r["timestamp"],
            "person_count": int(r["person_count"]),
            "confidence":   float(r["confidence"]),
            "model_version": MODEL_VERSION,
        }
        for r in records
    ]
    errors = bq_client.insert_rows_json(table_ref, rows)
    if errors:
        print(f"[BigQuery ERROR] {errors}")
    else:
        print(f"[BigQuery] ✅ Inserted {len(rows)} predictions")


# ── Move processed blobs to raw/done/ ─────────────────────────────────────────
def mark_done(gcs_client, blobs):
    bucket = gcs_client.bucket(BUCKET_NAME)
    for blob in blobs:
        filename = blob.name.split("/")[-1]
        dest_name = f"{DONE_PREFIX}/{filename}"
        bucket.copy_blob(blob, bucket, dest_name)
        blob.delete()
        print(f"[GCS] Moved {blob.name} → {dest_name}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*50}")
    print(f"[JOB] CSI Pipeline started at {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*50}\n")

    gcs_client = _get_gcs_client()
    bq_client  = _get_bq_client()

    blobs = fetch_raw_blobs(gcs_client)
    if not blobs:
        print("[JOB] No new data — exiting")
        return

    df = download_and_concat(blobs)
    if df.empty:
        print("[JOB] All files were empty — exiting")
        return

    model, scaler, feature_columns, valid_mask, baseline = load_artifacts(gcs_client)

    results = run_predictions(df, model, scaler, feature_columns, valid_mask, baseline)

    insert_predictions_batch(bq_client, results)

    mark_done(gcs_client, blobs)

    print(f"\n[JOB] Done — {len(results)} predictions saved to BigQuery\n")


if __name__ == "__main__":
    main()
