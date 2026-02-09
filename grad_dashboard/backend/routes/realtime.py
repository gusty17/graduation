from flask import Blueprint, Response, request, jsonify
import json
import time

import state.buffers as buffers
from services.mqtt_service import on_mqtt_message

realtime_bp = Blueprint("realtime", __name__)

@realtime_bp.route("/realtime/ingest", methods=["POST"])
def ingest_realtime_data():
    """
    Ingest real-time WiFi CSI data from ESP or MQTT publisher.
    
    Expected payload:
    {
      "esp_id": "rx1" or "rx2",
      "timestamp": "2026-02-09T12:34:56.123456",
      "rssi": -55,
      "csi": [-0.5, 0.3, ...]  // array of 128+ values
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data received"}), 400

    # Validate required fields
    required = ["esp_id", "timestamp", "rssi", "csi"]
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    # Validate esp_id is rx1 or rx2
    if data["esp_id"] not in ["rx1", "rx2"]:
        return jsonify({"error": "esp_id must be 'rx1' or 'rx2'"}), 400

    # Validate csi is array-like
    if not isinstance(data.get("csi"), (list, tuple)):
        return jsonify({"error": "csi must be an array"}), 400

    # Validate csi has reasonable length (128+ samples)
    if len(data["csi"]) < 128:
        return jsonify(
            {"error": f"csi array too short: {len(data['csi'])} < 128"}
        ), 400

    # Process through mqtt_service (which appends to buffer)
    on_mqtt_message(data)

    print(
        f"✅ Ingested {data['esp_id']} | "
        f"time={data['timestamp']} | "
        f"rssi={data['rssi']} | "
        f"csi_len={len(data['csi'])}"
    )

    return jsonify({"status": "ok", "buffer_size": len(buffers.prediction_buffer)})

@realtime_bp.route("/realtime/stream")
def realtime_stream():
    """
    Server-Sent Events (SSE) stream of real-time predictions.
    
    Clients (React) can connect via EventSource:
      const source = new EventSource('/realtime/stream');
      source.onmessage = (e) => console.log(JSON.parse(e.data));
    
    Connection stays open, streaming new predictions as they arrive.
    """
    def event_stream():
        last_sent = None

        while True:
            with buffers.prediction_lock:
                print("🧠 SSE sees latest_prediction =", buffers.latest_prediction)
                # Only send if prediction is new
                if buffers.latest_prediction != last_sent:
                    last_sent = buffers.latest_prediction
                    yield f"data: {json.dumps(buffers.latest_prediction)}\n\n"

            time.sleep(0.3)  # Smooth delivery, low CPU usage
            
    #keep sending data until client disconnects (handled by EventSource on frontend)
    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable proxy buffering
        },
    )
