import socket
import struct
import random
import time

# ================= CONFIG =================
UDP_IP = "127.0.0.1"   # localhost for local testing (change to your PC IP for real network)
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Must match backend struct
HEADER_FORMAT = "<8sIbbH"

def generate_packet(device_id):
    esp_id_bytes = device_id.encode().ljust(8, b'\x00')  # pad to 8 bytes
    esp_timestamp = int(time.time())
    rssi = random.randint(-70, -40)
    channel = 1

    # Generate fake CSI (128 values)
    csi = [random.randint(-100, 100) for _ in range(128)]
    csi_len = len(csi)

    header = struct.pack(
        HEADER_FORMAT,
        esp_id_bytes,
        esp_timestamp,
        rssi,
        channel,
        csi_len
    )

    csi_bytes = struct.pack(f"{csi_len}b", *csi)

    return header + csi_bytes

print("🚀 Fake UDP publisher started...")

counter = 0

while True:
    try:
        # Send RX1, RX2, RX3 (same timestamp)
        packet1 = generate_packet("rx1")
        packet2 = generate_packet("rx2")
        packet3 = generate_packet("rx3")

        sock.sendto(packet1, (UDP_IP, UDP_PORT))
        sock.sendto(packet2, (UDP_IP, UDP_PORT))
        sock.sendto(packet3, (UDP_IP, UDP_PORT))

        print(f"[SENT] Packet set #{counter} (rx1, rx2, rx3)")

        counter += 1
        time.sleep(1)

    except Exception as e:
        print("[ERROR]", e)