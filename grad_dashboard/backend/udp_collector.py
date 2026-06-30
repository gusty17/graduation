import socket
import struct
import csv
import sys
import os
from datetime import datetime

# ============================================================================
# Standalone raw-CSI collector for data gathering.
#
# Run one collector per (session, class) segment and Ctrl+C to stop it, e.g.
#     python udp_collector.py collecting/session_01/0p.csv     # record FIRST (baseline)
#     python udp_collector.py collecting/session_01/1p.csv
#     python udp_collector.py collecting/session_01/2p.csv
#     python udp_collector.py collecting/session_02/0p.csv     # next loop...
#
# On Ctrl+C it prints a per-receiver row count so you can confirm all three
# ESPs captured enough data BEFORE moving on - the weakest receiver gates the
# whole window pipeline downstream.
# ============================================================================

UDP_IP = "0.0.0.0"
UDP_PORT = 5005

# Output path from the first CLI arg (defaults to a scratch file).
OUTPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "csi_data_formatted.csv"

# New firmware emits a single fixed CSI length. Drop anything else as a safety
# net so a stray legacy/STBC frame can never contaminate a clean capture.
EXPECTED_CSI_LEN = 256   # 128 subcarriers * 2 (imag, real) int8 values
ENFORCE_LEN = True

# Map sender IP -> receiver ID (ESP firmware's self-reported ID is unreliable).
DEVICE_MAP = {
    "192.168.8.88": "rx1",
    "192.168.8.113": "rx2",
    "192.168.8.2": "rx3",
}

HEADER_FORMAT = "<8sIbbH"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

os.makedirs(os.path.dirname(os.path.abspath(OUTPUT_FILE)), exist_ok=True)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Listening on UDP {UDP_PORT}  ->  writing {OUTPUT_FILE}")
print("Press Ctrl+C to stop this segment.\n")

counts = {"rx1": 0, "rx2": 0, "rx3": 0, "unknown": 0, "dropped_len": 0}

try:
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["esp_id", "timestamp", "rssi", "csi"])

        while True:
            data, addr = sock.recvfrom(4096)
            if len(data) < HEADER_SIZE:
                continue

            sender_ip = addr[0]
            header = data[:HEADER_SIZE]
            csi_raw = data[HEADER_SIZE:]

            _, esp_timestamp, rssi, channel, csi_len = struct.unpack(HEADER_FORMAT, header)

            if len(csi_raw) != csi_len:
                continue
            if ENFORCE_LEN and csi_len != EXPECTED_CSI_LEN:
                counts["dropped_len"] += 1
                continue

            esp_id = DEVICE_MAP.get(sender_ip, "unknown")
            csi_array = list(struct.unpack(f"{csi_len}b", csi_raw))
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

            writer.writerow([esp_id, timestamp, rssi, str(csi_array)])
            f.flush()

            counts[esp_id] = counts.get(esp_id, 0) + 1
            total = counts["rx1"] + counts["rx2"] + counts["rx3"]
            if total % 50 == 0:
                print(f"\rrx1={counts['rx1']}  rx2={counts['rx2']}  rx3={counts['rx3']}  "
                      f"dropped_len={counts['dropped_len']}", end="")

except KeyboardInterrupt:
    print("\n\n=== segment summary ===")
    for k in ("rx1", "rx2", "rx3", "unknown", "dropped_len"):
        print(f"  {k}: {counts[k]}")
    weakest = min(counts["rx1"], counts["rx2"], counts["rx3"])
    if weakest == 0:
        print("⚠️  A receiver captured ZERO rows - check it is powered/connected "
              "and re-record this segment.")
    else:
        print(f"✅ Weakest receiver captured {weakest} rows.")
    print(f"Saved -> {OUTPUT_FILE}")
