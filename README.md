# WiFi CSI Person Counting using ESP32

This project detects and counts the number of people in predefined locations
using WiFi CSI data collected from ESP32 devices.

## Features
- CSI-based person counting (0–3 persons)
- ESP32 RX1/RX2 setup
- Random Forest ML model
- Flask backend
- Web dashboard frontend

## Project Structure
- `backend/` – Flask API and inference logic
- `frontend/` – Dashboard UI
- `preprocessing/` – CSI data processing
- `model/` – Training scripts and notebooks

## How to Run
1. Preprocess data then Train the model. cd grad_model_trainin python processing.py  
2. Start backend server  cd grad_dashboard/backend python app.py
3. Open frontend dashboard  cd grad_dashboard/frontend npm start 