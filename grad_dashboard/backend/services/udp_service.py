import socket
import struct
from datetime import datetime

import state.buffers as buffers

# ================= CONFIG =================
UDP_IP = "0.0.0.0"
UDP_PORT = 5005

HEADER_FORMAT = "<8sIbbH"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

# Raw CSI -> GCS is the cloud ingest path (consumed by pipeline/cloud_job.py).
# The rotating writer in gcs_service.py flushes a CSV to the bucket every
# ROTATION_INTERVAL (5 min). The FIRST window is the empty-room calibration
# period, during which we deliberately write NOTHING here (those rows go to
# calibration_buffer to build deployment_baseline.pkl instead). That leaves the
# first 5-min file empty, so the rotating writer discards it instead of
# uploading it — i.e. the calibration data never reaches GCS.

_csv_writer = None
_csv_writer_resolved = False


def _gcs_writer():
    """Lazily import the GCS rotating writer so a machine without GCS
    credentials can still run local inference (raw upload just no-ops)."""
    global _csv_writer, _csv_writer_resolved
    if not _csv_writer_resolved:
        _csv_writer_resolved = True
        try:
            from services.gcs_service import csv_writer
            _csv_writer = csv_writer
        except Exception as e:
            print(f"[UDP] GCS raw writer unavailable ({e}); raw CSI will not be uploaded.")
            _csv_writer = None
    return _csv_writer


# ================= UDP LISTENER =================
def start_udp_listener():
    """Single UDP socket loop. Parses ESP32 CSI packets and routes each row to
    the correct buffer depending on the calibration phase:

      * "calibrating": rows feed the empty-room baseline ONLY. They stay on this
        machine and are never uploaded.
      * "predicting":  rows feed live inference (prediction_buffer) and, only if
        ENABLE_GCS_RAW=1, are also streamed to GCS for the cloud pipeline.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"[UDP] Listening on port {UDP_PORT}...")

    while True:
        data, addr = sock.recvfrom(4096)

        if len(data) < HEADER_SIZE:
            print("[UDP] Packet too small")
            continue

        try:
            header = data[:HEADER_SIZE]
            csi_raw = data[HEADER_SIZE:]

            device_id_raw, esp_timestamp, rssi, channel, csi_len = struct.unpack(
                HEADER_FORMAT, header
            )
            esp_id = device_id_raw.decode(errors="ignore").strip("\x00").lower()

            if len(csi_raw) != csi_len:
                print("[UDP] CSI length mismatch")
                continue

            csi_array = list(struct.unpack(f"{csi_len}b", csi_raw))
            timestamp = datetime.now().isoformat()

            # Per-packet confirmation so all 3 ESPs are visible in the terminal.
            print(f"📡 {esp_id} | rssi={rssi} | csi_len={csi_len}")

            row = {
                "esp_id": esp_id,
                "timestamp": timestamp,
                "rssi": int(rssi),
                "csi": csi_array,
            }

            if buffers.calibration_status["phase"] == "calibrating":
                # First 5 min — empty-room calibration. Feed the baseline only;
                # never upload these rows to GCS.
                with buffers.calibration_lock:
                    buffers.calibration_buffer.append(row)
            else:
                # Live phase — feed inference AND stream raw to GCS every 5 min
                # for the cloud job (which fills the BigQuery table).
                buffers.prediction_buffer.append(row)
                writer = _gcs_writer()
                if writer is not None:
                    writer.write_row({
                        "esp_id": esp_id,
                        "timestamp": timestamp,
                        "rssi": int(rssi),
                        "csi": str(csi_array),
                    })

        except Exception as e:
            print("[UDP ERROR]", e)
