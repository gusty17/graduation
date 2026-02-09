from collections import deque
import threading

BUFFER_SIZE = 200

prediction_buffer = deque(maxlen=BUFFER_SIZE)

latest_prediction = None
prediction_lock = threading.Lock()
