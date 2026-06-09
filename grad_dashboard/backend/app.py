from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import threading
import atexit
import signal
import sys
from dotenv import load_dotenv

load_dotenv()

# Routes
from routes.realtime import realtime_bp
from routes.analytics import analytics_bp
from routes.predict import predict_bp

# Services
from services.inference import realtime_prediction_worker
#from services.mqtt_service import start_mqtt_client
from services.udp_service import start_udp_listener
# ─────────────────────────────────────────
# App setup
# ─────────────────────────────────────────
app = Flask(__name__)
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*")

# Register routes
app.register_blueprint(realtime_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(predict_bp)

# ─────────────────────────────────────────
# Graceful shutdown — flush raw CSVs to GCS
# ─────────────────────────────────────────
def _flush_on_exit():
    from services.gcs_service import csv_writer
    csv_writer.shutdown()

atexit.register(_flush_on_exit)

def _signal_handler(signum, frame):
    """Catch SIGINT / SIGTERM, flush data, then exit cleanly."""
    _flush_on_exit()
    sys.exit(0)

signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)

# ─────────────────────────────────────────
# Start background services
# ─────────────────────────────────────────

# ✅ Start MQTT listener (non-blocking)
# start_mqtt_client()

# ✅ Start prediction worker (pass socketio)
threading.Thread(
    target=realtime_prediction_worker,
    args=(socketio,),
    daemon=True
).start()

threading.Thread(
    target=start_udp_listener,
    daemon=True
).start()

# ─────────────────────────────────────────
# Run server
# ─────────────────────────────────────────
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=False)