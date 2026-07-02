import socket
import struct
import time
from datetime import datetime

import state.buffers as buffers
import services.collector_service as collector

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
    # Large receive buffer so brief processing stalls don't overflow the kernel
    # queue and drop CSI packets (the main cause of a low capture rate).
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 << 20)  # 4 MB
    except OSError:
        pass
    sock.bind((UDP_IP, UDP_PORT))
    print(f"[UDP] Listening on port {UDP_PORT}...")

    # Per-receiver counters + a throttled heartbeat. Printing on EVERY packet
    # (console I/O is slow, esp. on Windows) stalls the loop and drops packets,
    # so we print at most once per second instead.
    seen = {"rx1": 0, "rx2": 0, "rx3": 0}
    last_report = time.monotonic()

    while True:
        data, addr = sock.recvfrom(4096)

        if len(data) < HEADER_SIZE:
            continue

        try:
            header = data[:HEADER_SIZE]
            csi_raw = data[HEADER_SIZE:]

            device_id_raw, esp_timestamp, rssi, channel, csi_len = struct.unpack(
                HEADER_FORMAT, header
            )
            # Prefer sender IP (reliable on real hardware), fall back to packet id.
            esp_id = collector.resolve_esp_id(addr[0], device_id_raw)

            if len(csi_raw) != csi_len:
                continue

            csi_array = list(struct.unpack(f"{csi_len}b", csi_raw))
            timestamp = datetime.now().isoformat()

            if esp_id in seen:
                seen[esp_id] += 1
            now = time.monotonic()
            if now - last_report >= 1.0:
                print(f"📡 [UDP] rx1={seen['rx1']} rx2={seen['rx2']} rx3={seen['rx3']} (cumulative)")
                last_report = now

            # Training-data collection takes over the stream when active: write
            # the row to the session CSV and skip the live prediction/GCS path.
            if collector.record(esp_id, timestamp, rssi, csi_array, csi_len):
                continue

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
