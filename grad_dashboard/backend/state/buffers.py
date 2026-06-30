import os
from collections import deque
import threading

BUFFER_SIZE = 200

prediction_buffer = deque(maxlen=BUFFER_SIZE)

latest_prediction = None
prediction_lock = threading.Lock()

# ── Startup empty-room calibration ────────────────────────────────────────────
CALIBRATION_SECONDS = int(os.environ.get("CALIBRATION_SECONDS", "300"))  # 5 min

calibration_buffer = []                 # raw empty-room rows gathered during calibration
calibration_lock = threading.Lock()

# Polled by the UI via GET /calibration/status.
calibration_status = {
    "phase": "calibrating",             # "calibrating" -> "predicting"
    "remaining": CALIBRATION_SECONDS,   # seconds left in the calibration phase
    "duration": CALIBRATION_SECONDS,
}
