from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import threading

# Routes
from routes.realtime import realtime_bp
from routes.analytics import analytics_bp
from routes.predict import predict_bp

# Services
from services.inference import realtime_prediction_worker
from services.mqtt_service import start_mqtt_client

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
# Start background services
# ─────────────────────────────────────────

# ✅ Start MQTT listener (non-blocking)
start_mqtt_client()

# ✅ Start prediction worker (pass socketio)
threading.Thread(
    target=realtime_prediction_worker,
    args=(socketio,),
    daemon=True
).start()

# ─────────────────────────────────────────
# Run server
# ─────────────────────────────────────────
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=False)