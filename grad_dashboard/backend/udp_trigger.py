import socket
import time

ESP32_TARGETS = [
    ("192.168.8.113", 3333),  #rx2
    ("192.168.8.2", 3333),   #rx3 
    ("192.168.8.88", 3333), #rx1
]

PACKET_RATE_HZ = 5  # was 3; raised to compensate for sender.c now dropping every
                      # frame that isn't the new fixed CSI length
MESSAGE = b"CSI_TRIGGER"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

interval = 1.0 / PACKET_RATE_HZ
counter = 0

print("Sending UDP trigger packets to ESP32 receivers...")
print(f"Packet rate per ESP: {PACKET_RATE_HZ} packets/sec")

while True:
    payload = MESSAGE + counter.to_bytes(4, "little")

    for ip, port in ESP32_TARGETS:
        sock.sendto(payload, (ip, port))

    counter += 1
    time.sleep(interval)