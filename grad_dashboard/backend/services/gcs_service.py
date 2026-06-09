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
      2. Upload it to GCS under raw/{YYYY}/{MM}/{DD}/{HH}/ (if non-empty).
      3. Delete the local copy.
      4. Open a fresh CSV.
    Network I/O happens outside the lock so write_row is never blocked by uploads.

    Call shutdown() before process exit to flush and upload whatever is in the
    current (not yet rotated) file so no data is lost on restart/shutdown.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._file = None
        self._path = None
        self._closed = False
        os.makedirs(LOCAL_CSV_DIR, exist_ok=True)
        self._open_new_file()
        self._schedule()

    def write_row(self, row: dict):
        with self._lock:
            if self._closed:
                return
            writer = csv.DictWriter(self._file, fieldnames=CSV_COLUMNS)
            if self._file.tell() == 0:
                writer.writeheader()
            writer.writerow(row)
            self._file.flush()

    def shutdown(self):
        """
        Close the active file and upload every pending CSV in LOCAL_CSV_DIR
        to GCS before the process exits. Safe to call from a signal handler.
        """
        print("[GCS] 🛑 Shutdown: flushing raw data to GCS...")
        with self._lock:
            self._closed = True
            try:
                self._file.close()
            except Exception:
                pass

        # Upload every .csv left in the local staging directory
        for fname in os.listdir(LOCAL_CSV_DIR):
            if not fname.endswith(".csv"):
                continue
            fpath = os.path.join(LOCAL_CSV_DIR, fname)
            if os.path.getsize(fpath) == 0:
                os.remove(fpath)
                continue
            blob_name = self._make_blob_name(fname)
            try:
                upload_file(fpath, blob_name)
                os.remove(fpath)
                print(f"[GCS] ✅ Shutdown upload: {fname} → gs://{BUCKET_NAME}/{blob_name}")
            except Exception as e:
                print(f"[GCS ERROR] Shutdown upload failed for {fname}: {e}")

        print("[GCS] ✅ Shutdown flush complete")

    # ── internals ─────────────────────────────────────────────────────────────

    @staticmethod
    def _make_blob_name(filename: str) -> str:
        """
        Build a GCS object path with time-partitioned folders:
            raw/{YYYY}/{MM}/{DD}/{HH}/{filename}
        Parses the UTC datetime from the filename, converts to local time for
        the folder path so hours match the machine's timezone.
        Falls back to local now if parsing fails.
        """
        try:
            # filename format: raw_20260609T094839.csv  →  ts part = [4:19]
            dt_utc = datetime.strptime(filename[4:19], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
            dt = dt_utc.astimezone()  # convert to local timezone
        except (ValueError, IndexError):
            dt = datetime.now().astimezone()
        return (
            f"{RAW_GCS_PREFIX}/"
            f"year={dt.year}/month={dt.month}/day={dt.day}/hour={dt.hour}/"
            f"{filename}"
        )

    def _open_new_file(self):
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        self._path = os.path.join(LOCAL_CSV_DIR, f"raw_{ts}.csv")
        self._file = open(self._path, "w", newline="")

    def _schedule(self):
        t = threading.Timer(ROTATION_INTERVAL, self._rotate)
        t.daemon = True
        t.start()

    def _rotate(self):
        if self._closed:
            return
        # Swap files under the lock so write_row is blocked for the minimum time
        with self._lock:
            self._file.close()
            old_path = self._path
            self._open_new_file()

        # Upload and clean up outside the lock
        if os.path.getsize(old_path) > 0:
            blob_name = self._make_blob_name(os.path.basename(old_path))
            try:
                upload_file(old_path, blob_name)
                os.remove(old_path)
            except Exception as e:
                print(f"[GCS ERROR] Upload failed for {old_path}: {e}")
        else:
            os.remove(old_path)  # discard empty rotation files

        self._schedule()


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
csv_writer = _CSVRotatingWriter()   # used by udp_service.py
