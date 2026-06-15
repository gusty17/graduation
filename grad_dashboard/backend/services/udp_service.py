import socket
import struct
from datetime import datetime
from services.gcs_service import csv_writer

# ================= CONFIG =================
UDP_IP = "0.0.0.0"
UDP_PORT = 5005

HEADER_FORMAT = "<8sIbbH"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

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

            # ================= SAVE TO GCS =================
            csv_writer.write_row({
                "esp_id": esp_id,
                "timestamp": timestamp,
                "rssi": int(rssi),
                "csi": str(csi_array)
            })

        except Exception as e:
            print("[UDP ERROR]", e)