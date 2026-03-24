import time
import json
import paho.mqtt.client as mqtt
import pandas as pd
import os

import state.buffers as buffers

# ================= MQTT CONFIG =================
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC = "esp32/csi"
MQTT_CLIENT_ID = f"csi-backend-{int(time.time())}"

# ================= RAW DATA STORAGE =================
RAW_DATA_FOLDER = "raw_data"
RAW_DATA_CSV = os.path.join(RAW_DATA_FOLDER, "raw_data.csv")

# Create folder if needed
if not os.path.exists(RAW_DATA_FOLDER):
    os.makedirs(RAW_DATA_FOLDER)
    print(f"📁 Created folder: {RAW_DATA_FOLDER}")

# Create CSV if needed
if not os.path.exists(RAW_DATA_CSV):
    pd.DataFrame(columns=[
        "esp_id", "timestamp", "rssi", "csi"
    ]).to_csv(RAW_DATA_CSV, index=False)
    print(f"📄 Created CSV: {RAW_DATA_CSV}")

# ================= SETTINGS =================
VALID_DEVICES = {"rx1", "rx2"}


# ================= MQTT CALLBACKS =================
def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"[MQTT] Connected: {reason_code}")
    client.subscribe(MQTT_TOPIC, qos=0)
    print(f"[MQTT] Subscribed to {MQTT_TOPIC}")


def on_message(client, userdata, msg):
    try:
        raw = msg.payload.decode("utf-8", errors="ignore").strip()
        print("[RAW INCOMING]", raw)

        if not raw:
            return

        # Expected format:
        # rx1, timestamp, rssi, "[csi values]"
        parts = raw.split(",", 3)

        if len(parts) < 4:
            print("[MQTT] Invalid format")
            return

        esp_id = parts[0].strip()

        # ✅ Validate device
        if esp_id not in VALID_DEVICES:
            print(f"[MQTT] Unknown device: {esp_id}")
            return

        timestamp = parts[1].strip()

        try:
            rssi = int(parts[2].strip())
        except:
            print("[MQTT] Invalid RSSI")
            return

        # ================= CSI PARSING =================
        csi_str = parts[3].strip().strip('"')

        try:
            csi = json.loads(csi_str)
        except:
            print("[MQTT] CSI parse failed")
            return

        # ✅ Validate CSI
        if not isinstance(csi, list) or len(csi) == 0:
            print("[MQTT] Invalid CSI data")
            return

        # ================= BUILD DATA =================
        data = {
            "esp_id": esp_id,
            "timestamp": timestamp,
            "rssi": rssi,
            "csi": csi
        }

        # ================= ADD TO BUFFER =================
        # 🔥 IMPORTANT: MQTT ONLY APPENDS (no popping here)
        buffers.prediction_buffer.append(data)

        print(
            f"[BUFFER] Device={esp_id} | "
            f"RSSI={rssi} | CSI={len(csi)} | "
            f"Total Buffer={len(buffers.prediction_buffer)}"
        )

        # ================= SAVE RAW DATA =================
        raw_data_record = {
            "esp_id": esp_id,
            "timestamp": timestamp,
            "rssi": rssi,
            "csi": json.dumps(csi)  # store as JSON string
        }

        try:
            pd.DataFrame([raw_data_record]).to_csv(
                RAW_DATA_CSV,
                mode="a",
                header=False,
                index=False
            )
            print("💾 Raw data saved")
        except Exception as save_error:
            print(f"⚠️ Failed to save raw data: {save_error}")

    except Exception as e:
        print("[MQTT ERROR]", e)


# ================= START CLIENT =================
def start_mqtt_client():
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=MQTT_CLIENT_ID
    )

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    print("[MQTT] Starting loop...")
    client.loop_start()

    return client