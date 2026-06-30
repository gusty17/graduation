from flask import Blueprint, Response, jsonify
import json
import time

import state.buffers as buffers

realtime_bp = Blueprint("realtime", __name__)


@realtime_bp.route("/calibration/status")
def calibration_status():
    """Current empty-room calibration phase + countdown, polled by the UI.

    Returns: {"phase": "calibrating"|"predicting", "remaining": int, "duration": int}
    """
    return jsonify(buffers.calibration_status)


@realtime_bp.route("/realtime/stream")
def realtime_stream():
    """
    Server-Sent Events (SSE) stream of real-time predictions.

    Clients (React) connect via EventSource:
      const source = new EventSource('/realtime/stream');
      source.onmessage = (e) => console.log(JSON.parse(e.data));

    The connection stays open, streaming each new prediction as it arrives.
    Live CSI is ingested over UDP (see services/udp_service.py), not HTTP.
    """
    def event_stream():
        last_sent = None

        while True:
            # Copy under the lock, then yield outside it so the network write
            # never blocks the inference worker.
            with buffers.prediction_lock:
                current = buffers.latest_prediction

            if current != last_sent:
                last_sent = current
                yield f"data: {json.dumps(current)}\n\n"

            time.sleep(0.3)  # smooth delivery, low CPU usage

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable proxy buffering
        },
    )
