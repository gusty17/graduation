import os
from google.cloud import bigquery

CREDENTIALS_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
DATASET_ID = "occupancy_analytics"
TABLE_ID = "occupancy_predictions"
MODEL_VERSION = "rf_v1"


def _get_client() -> bigquery.Client:
    if CREDENTIALS_PATH and os.path.exists(CREDENTIALS_PATH):
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
        return bigquery.Client(credentials=creds, project=creds.project_id)
    return bigquery.Client()  # falls back to Application Default Credentials


def _table_ref(client: bigquery.Client) -> str:
    return f"{client.project}.{DATASET_ID}.{TABLE_ID}"


def insert_prediction(record: dict):
    """Insert one prediction row into BigQuery."""
    try:
        client = _get_client()
        row = {
            "timestamp": str(record["timestamp"]),
            "person_count": int(record["person_count"]),
            "confidence": float(record["confidence"]),
            "model_version": MODEL_VERSION,
        }
        errors = client.insert_rows_json(_table_ref(client), [row])
        if errors:
            print(f"[BigQuery ERROR] Insert failed: {errors}")
        else:
            print(f"[BigQuery] ✅ Prediction saved → {row}")
    except Exception as e:
        print(f"[BigQuery ERROR] insert_prediction failed: {e}")


def query_predictions() -> list:
    """Return all predictions from BigQuery ordered by timestamp (ascending)."""
    try:
        client = _get_client()
        query = f"""
            SELECT timestamp, person_count, confidence, model_version
            FROM `{_table_ref(client)}`
            ORDER BY timestamp ASC
        """
        rows = []
        for row in client.query(query).result():
            rows.append({
                "timestamp": str(row.timestamp),
                "person_count": row.person_count,
                "confidence": float(row.confidence),
                "model_version": row.model_version,
            })
        print(f"[BigQuery] ✅ Fetched {len(rows)} predictions")
        return rows
    except Exception as e:
        print(f"[BigQuery ERROR] query_predictions failed: {e}")
        return []
