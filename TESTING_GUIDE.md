# Quick Testing Guide

## 30-Second Start

### Terminal 1: Backend
```bash
cd backend
python app.py
```

### Terminal 2: Frontend
```bash
cd Dashboard
npm start
```

### Terminal 3: Fake Publisher
```bash
cd backend
python -m dev.fake_mqtt_publisher
```

Then open `http://localhost:3000` and click **"Start Live"**

---

## What to Watch For

### Backend Console
```
✅ Sent RX1 + RX2 pair #1 | Buffer: 2
✅ Sent RX1 + RX2 pair #2 | Buffer: 4
...
✅ Sent RX1 + RX2 pair #25 | Buffer: 50
   📊 After 50 packets, realtime_prediction_worker should start processing...
✅ Prediction: 1 person(s) | Confidence: 95.1%
✅ Prediction: 1 person(s) | Confidence: 94.8%
```

### Frontend Browser
- Real-time occupancy updates
- "● LIVE" indicator visible
- Confidence percentage displayed

### Browser Console (F12)
```
✅ SSE connection opened
📨 SSE message #1: {timestamp: "...", person_count: 1, confidence: 95.2}
📨 SSE message #2: {timestamp: "...", person_count: 1, confidence: 94.9}
```

---

## Troubleshooting

### No real-time updates?
1. Check backend is running: `http://localhost:5000/analytics`
2. Check publisher is sending: Look for "✅ Sent" messages
3. Check browser console for SSE errors

### Buffer not accumulating?
- Verify publisher is actually sending packets
- Check `/realtime/ingest` validation (backend logs)

### "Cannot find EventSource"?
- Make sure you're on a modern browser
- Use Firefox, Chrome, Safari, Edge (not IE)

### "Connection refused"?
- Backend not running
- Backend running on wrong port
- CORS not enabled

---

## Test Scenarios

### Scenario 1: Live Streaming
1. Start all three terminals
2. Click "Start Live"
3. Wait 50+ packets (5+ seconds)
4. Verify updates appear

### Scenario 2: CSV Upload
1. Upload a CSV file from `backend/uploads/`
2. Check detections appear
3. Click Analytics
4. Verify predictions show by day

### Scenario 3: Switch Between Modes
1. Upload CSV and analyze
2. Click "Start Live"
3. Observe file clears after live stops
4. Upload new CSV
5. Verify analytics still work

---

## Performance Expectations

- **Backend**: ~50ms to process 50 RX samples
- **SSE**: ~0.3s latency (configured in code)
- **Frontend**: Instant UI update on SSE message
- **Memory**: ~50MB steady state

---

## Debug Commands

### Check backend is running
```bash
curl http://127.0.0.1:5000/analytics
```

### Check /ingest endpoint
```bash
curl -X POST http://127.0.0.1:5000/realtime/ingest \
  -H "Content-Type: application/json" \
  -d '{"esp_id":"rx1","timestamp":"2026-02-09T20:00:00","rssi":-60,"csi":[1,2,3]}'
```

### Monitor backend
```bash
python app.py 2>&1 | grep "✅\|❌"
```

---

## Success Criteria

✅ Backend starts without errors  
✅ Frontend loads at localhost:3000  
✅ Fake publisher sends packets  
✅ Buffer accumulates (shown in logs)  
✅ Predictions trigger after 50 packets  
✅ SSE stream sends updates  
✅ Frontend displays real-time occupancy  
✅ CSV mode still works  
✅ Analytics mode still works  

If all pass → **System is production-ready!**
