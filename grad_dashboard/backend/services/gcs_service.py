import os
import io
import csv
import threading
import pandas as pd
from datetime import datetime, timezone
from google.cloud import storage

# ── Config ───────────────────────────────────────────────────────────────────
BUCKET_NAME = os.environ["GCS_BUCKET_NAME"]
CREDENTIALS_PATH = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

RAW_GCS_PREFIX = "raw"           # gs://bucket/raw/raw_<ts>.csv
PREDICTIONS_PREFIX = "predictions"
LOCAL_CSV_DIR = "raw_data"
ROTATION_INTERVAL = int(os.environ.get("GCS_ROTATION_INTERVAL_SECONDS", 300))

CSV_COLUMNS = ["esp_id", "timestamp", "rssi", "csi"]


# ── GCS Auth & Upload ─────────────────────────────────────────────────────────
def _get_client() -> storage.Client:
    if os.path.exists(CREDENTIALS_PATH):
        return storage.Client.from_service_account_json(CREDENTIALS_PATH)
    return storage.Client()  # falls back to Application Default Credentials


def upload_file(local_path: str, blob_name: str):
    client = _get_client()
    bucket = client.bucket(BUCKET_NAME)
    bucket.blob(blob_name).upload_from_filename(local_path)
    print(f"[GCS] ✅ {local_path} → gs://{BUCKET_NAME}/{blob_name}")


# ── CSV Rotating Writer (raw ESP32 data) ──────────────────────────────────────
class _CSVRotatingWriter:
    """
    Parallel to the prediction pipeline — writes every UDP row to a local CSV.
    Every ROTATION_INTERVAL seconds:
      1. Close the current file.
      2. Upload it to GCS under RAW_GCS_PREFIX/ (if non-empty).
      3. Delete the local copy.
      4. Open a fresh CSV.
    Network I/O happens outside the lock so write_row is never blocked by uploads.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._file = None
        self._path = None
        os.makedirs(LOCAL_CSV_DIR, exist_ok=True)
        self._open_new_file()
        self._schedule()

    def write_row(self, row: dict):
        with self._lock:
            writer = csv.DictWriter(self._file, fieldnames=CSV_COLUMNS)
            if self._file.tell() == 0:
                writer.writeheader()
            writer.writerow(row)
            self._file.flush()

    # ── internals ─────────────────────────────────────────────────────────────

    def _open_new_file(self):
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        self._path = os.path.join(LOCAL_CSV_DIR, f"raw_{ts}.csv")
        self._file = open(self._path, "w", newline="")

    def _schedule(self):
        t = threading.Timer(ROTATION_INTERVAL, self._rotate)
        t.daemon = True
        t.start()

    def _rotate(self):
        # Swap files under the lock so write_row is blocked for the minimum time
        with self._lock:
            self._file.close()
            old_path = self._path
            self._open_new_file()

        # Upload and clean up outside the lock
        if os.path.getsize(old_path) > 0:
            blob_name = f"{RAW_GCS_PREFIX}/{os.path.basename(old_path)}"
            try:
                upload_file(old_path, blob_name)
                os.remove(old_path)
            except Exception as e:
                print(f"[GCS ERROR] Upload failed for {old_path}: {e}")
        else:
            os.remove(old_path)  # discard empty rotation files

        self._schedule()


# ── Batch Uploader (predictions) ──────────────────────────────────────────────
class _BatchUploader:
    """Buffers prediction rows in memory and flushes to GCS every N rows or T seconds."""

    def __init__(self, prefix: str, flush_every_n: int = 10, flush_every_seconds: int = 10):
        self._buffer: list = []
        self._lock = threading.Lock()
        self._prefix = prefix
        self._flush_every_n = flush_every_n
        self._flush_every_seconds = flush_every_seconds
        self._schedule_timer()

    def add(self, record: dict):
        with self._lock:
            self._buffer.append(record)
            if len(self._buffer) >= self._flush_every_n:
                self._flush_locked()

    def _schedule_timer(self):
        t = threading.Timer(self._flush_every_seconds, self._on_timer)
        t.daemon = True
        t.start()

    def _on_timer(self):
        with self._lock:
            self._flush_locked()
        self._schedule_timer()

    def _flush_locked(self):
        if not self._buffer:
            return
        rows = list(self._buffer)
        self._buffer.clear()
        try:
            df = pd.DataFrame(rows)
            blob_name = f"{self._prefix}/{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}.csv"
            client = _get_client()
            bucket = client.bucket(BUCKET_NAME)
            bucket.blob(blob_name).upload_from_string(
                df.to_csv(index=False).encode(), content_type="text/csv"
            )
            print(f"[GCS] ✅ {len(rows)} predictions → gs://{BUCKET_NAME}/{blob_name}")
        except Exception as e:
            print(f"[GCS ERROR] Prediction flush failed: {e}")


# ── Analytics reader ──────────────────────────────────────────────────────────
def read_all(prefix: str) -> pd.DataFrame:
    """Download every CSV under <prefix>/ and return a single sorted DataFrame."""
    try:
        client = _get_client()
        blobs = list(client.bucket(BUCKET_NAME).list_blobs(prefix=f"{prefix}/"))
        if not blobs:
            return pd.DataFrame()
        frames = [pd.read_csv(io.BytesIO(b.download_as_bytes())) for b in blobs]
        df = pd.concat(frames, ignore_index=True)
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp").reset_index(drop=True)
        return df
    except Exception as e:
        print(f"[GCS ERROR] read_all({prefix}) failed: {e}")
        return pd.DataFrame()


# ── Singletons ────────────────────────────────────────────────────────────────
csv_writer = _CSVRotatingWriter()            # used by udp_service.py
predictions_uploader = _BatchUploader(PREDICTIONS_PREFIX)  # used by inference.py
