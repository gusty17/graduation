# backend/services/mqtt_service.py

from state.buffers import prediction_buffer

def on_mqtt_message(payload):
    """
    Process incoming MQTT message from ESP32 or fake publisher.
    
    Appends to prediction_buffer for realtime_prediction_worker to process.
    """
    if not payload:
        print("❌ mqtt_service: Empty payload received")
        return
    
    try:
        # Log the payload
        print(f"📡 mqtt_service received payload:")
        print(f"   esp_id: {payload.get('esp_id')}")
        print(f"   timestamp: {payload.get('timestamp')}")
        print(f"   rssi: {payload.get('rssi')}")
        print(f"   csi_len: {len(payload.get('csi', []))}")

        # Append to buffer
        prediction_buffer.append(payload)
        print(f"📦 Buffer size: {len(prediction_buffer)} / {prediction_buffer.maxlen}")
        
    except Exception as e:
        print(f"❌ mqtt_service error processing payload: {e}")

