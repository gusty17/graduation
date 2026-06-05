import socket
import struct
from datetime import datetime
import state.buffers as buffers
import pandas as pd
import os

# ================= CONFIG =================
UDP_IP = "0.0.0.0"
UDP_PORT = 5005

HEADER_FORMAT = "<8sIbbH"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

RAW_DATA_FOLDER = "raw_data"
RAW_DATA_CSV = os.path.join(RAW_DATA_FOLDER, "raw_data.csv")

# ================= SETUP =================
# Create folder if not exists
if not os.path.exists(RAW_DATA_FOLDER):
    os.makedirs(RAW_DATA_FOLDER)
    print(f"📁 Created folder: {RAW_DATA_FOLDER}")

# ================= UDP LISTENER =================
def start_udp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    print(f"[UDP] Listening on port {UDP_PORT}...")

    while True:
        data, addr = sock.recvfrom(4096)

        #  Debug: confirm packet arrival
        print(f"🔥 PACKET RECEIVED from {addr} | Size: {len(data)} bytes")

        if len(data) < HEADER_SIZE:
            print("[UDP] Packet too small")
            continue

        try:
            # ================= PARSE HEADER =================
            header = data[:HEADER_SIZE]
            csi_raw = data[HEADER_SIZE:]

            device_id_raw, esp_timestamp, rssi, channel, csi_len = struct.unpack(
                HEADER_FORMAT,
                header
            )

            esp_id = device_id_raw.decode(errors="ignore").strip("\x00").lower()

            print(f"[DEVICE] {esp_id} | RSSI={rssi} | CSI_LEN={csi_len}")

            # ================= VALIDATE CSI =================
            if len(csi_raw) != csi_len:
                print("[UDP] CSI length mismatch")
                continue

            csi_array = list(struct.unpack(f"{csi_len}b", csi_raw))

            timestamp = datetime.now().isoformat()

            # ================= BUILD DATA =================
            data_dict = {
                "esp_id": esp_id,
                "timestamp": timestamp,
                "rssi": int(rssi),
                "csi": csi_array
            }

            # ================= ADD TO BUFFER =================
            buffers.prediction_buffer.append(data_dict)

            print(
                f"[UDP BUFFER] {esp_id} | "
                f"Buffer size: {len(buffers.prediction_buffer)}"
            )

            # ================= SAVE TO CSV =================
            try:
                pd.DataFrame([{
                    "esp_id": esp_id,
                    "timestamp": timestamp,
                    "rssi": int(rssi),
                    "csi": str(csi_array)
                }]).to_csv(
                    RAW_DATA_CSV,
                    mode="a",
                    header=not os.path.exists(RAW_DATA_CSV),
                    index=False
                )
            except Exception as e:
                print("[CSV ERROR]", e)

        except Exception as e:
            print("[UDP ERROR]", e)