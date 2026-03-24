# -*- coding: utf-8 -*-
"""
Fake MQTT Publisher for Testing Real-Time Streaming

This script simulates WiFi CSI data from two receivers (RX1 and RX2),
sending data to the backend to test the entire real-time prediction pipeline.

Expected behavior:
  1. Generates RX1 and RX2 packets with SAME timestamp
  2. Sends both every 1 second
  3. After 50+ packets, realtime_prediction_worker triggers
  4. Predictions flow to frontend via SSE

Verification:
  Backend: Watch logs for "[OK] Prediction:" messages
  Frontend: Click "Start Live" and watch real-time updates
"""

import time
import random
import requests
from datetime import datetime

API_URL = "http://127.0.0.1:5000"
INGEST_ENDPOINT = f"{API_URL}/realtime/ingest"

print("=" * 70)
print("[*] Fake MQTT Publisher - Real-Time CSI Data Generator")
print("=" * 70)
print(f"Sending to: {INGEST_ENDPOINT}")
print()
print("This publisher sends RX1 + RX2 pairs every 1 second.")
print("Each receiver gets 128 CSI values + RSSI signal strength.")
print()
print("Expected flow:")
print("  1. Publisher sends RX1 + RX2 packets")
print("  2. Backend buffers them (need 50+ packets)")
print("  3. realtime_prediction_worker processes buffer")
print("  4. Predictions sent via SSE to frontend")
print("  5. Frontend displays real-time detections")
print()
print("Monitor backend:")
print("  - Look for: '[OK] Prediction: X person(s)'")
print()
print("Monitor frontend:")
print("  - Click 'Start Live' button")
print("  - Watch detection results update")
print("  - Check console (F12) for SSE activity")
print()

counter = 0

try:
    while True:
        # Use the SAME timestamp for RX1 and RX2 to match them
        from datetime import timezone
        ts = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

        rx1_payload = {
            "esp_id": "rx1",
            "timestamp": ts,
            "rssi": random.randint(-70, -50),
            "csi": [random.uniform(-100, 100) for _ in range(128)]
        }

        rx2_payload = {
            "esp_id": "rx2",
            "timestamp": ts,
            "rssi": random.randint(-70, -50),
            "csi": [random.uniform(-100, 100) for _ in range(128)]
        }

        try:
            # Send both packets
            r1 = requests.post(INGEST_ENDPOINT, json=rx1_payload, timeout=2)
            r2 = requests.post(INGEST_ENDPOINT, json=rx2_payload, timeout=2)
            
            if r1.status_code == 200 and r2.status_code == 200:
                buf_size = r2.json().get("buffer_size", "?")
                print(f"[OK] Sent RX1 + RX2 pair #{counter:3d} | Buffer: {buf_size}")
                
                # Print milestone message every 50 packets
                if counter > 0 and counter % 50 == 0:
                    print(f"     [*] After {counter} packets, worker should start processing...")
            else:
                print(f"[ERR] HTTP error: RX1={r1.status_code}, RX2={r2.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"[ERR] Cannot connect to {API_URL}")
            print("     Make sure backend is running: python app.py")
            print("     Retrying in 3 seconds...")
            time.sleep(3)
            continue
        except Exception as e:
            print(f"[ERR] Error: {e}")

        counter += 1
        time.sleep(1)  # Send pair every 1 second

except KeyboardInterrupt:
    print("=" * 70)
    print(f"[*] Stopped. Sent {counter} RX1/RX2 pairs")
    print("=" * 70)
