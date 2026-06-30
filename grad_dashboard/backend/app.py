from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import threading
import atexit
import signal
import sys
from dotenv import load_dotenv

load_dotenv()

from routes.analytics import analytics_bp
from routes.realtime import realtime_bp
from services.udp_service import start_udp_listener
from services.inference import realtime_prediction_worker

# ─────────────────────────────────────────
# App setup
# ─────────────────────────────────────────
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

app.register_blueprint(analytics_bp)
app.register_blueprint(realtime_bp)

# ─────────────────────────────────────────
# Graceful shutdown — flush raw CSVs to GCS
# ─────────────────────────────────────────
def _flush_on_exit():
    from services.gcs_service import csv_writer
    csv_writer.shutdown()

atexit.register(_flush_on_exit)

def _signal_handler(signum, frame):
    _flush_on_exit()
    sys.exit(0)

signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)

# ─────────────────────────────────────────
# Start UDP listener — receives ESP32 data, routes rows to the calibration /
# prediction buffers (and to GCS only when ENABLE_GCS_RAW=1).
# ─────────────────────────────────────────
threading.Thread(target=start_udp_listener, daemon=True).start()

# ─────────────────────────────────────────
# Start local inference worker — empty-room calibration, then live predictions
# streamed to the UI. Predictions are NOT sent to the cloud.
# ─────────────────────────────────────────
threading.Thread(
    target=realtime_prediction_worker, args=(socketio,), daemon=True
).start()

# ─────────────────────────────────────────
# Run server
# ─────────────────────────────────────────
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=False)