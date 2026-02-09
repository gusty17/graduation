from flask import Flask
from flask_cors import CORS
import threading

from routes.realtime import realtime_bp
from routes.analytics import analytics_bp
from routes.predict import predict_bp
from services.inference import realtime_prediction_worker

app = Flask(__name__)
CORS(app)

app.register_blueprint(realtime_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(predict_bp)

threading.Thread(
    target=realtime_prediction_worker,
    daemon=True
).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
