"""
Sensor data backend.
Generates temperature, humidity, and acceleration data, refreshed every 60s.
App polls GET /sensor-data to get the latest values.

Run:
    pip install fastapi uvicorn
    python main.py

Deploy (e.g. Render):
    Start command: uvicorn main:app --host 0.0.0.0 --port $PORT
    Then call https://<your-render-url>/sensor-data from anywhere.
"""

import os
import random
import threading
import time
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Sensor Data API")

# Allow the Android app (or any client) to call this freely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- shared state, updated once a minute in the background ----
latest_data = {
    "temperature_c": 25.0,
    "humidity_pct": 50.0,
    "acceleration_g": {"x": 0.0, "y": 0.0, "z": 1.0},
    "updated_at": datetime.now(timezone.utc).isoformat(),
}
lock = threading.Lock()


def generate_reading():
    """Replace this with real sensor/beacon reads when you have a data source."""
    return {
        "temperature_c": round(random.uniform(20.0, 30.0), 1),
        "humidity_pct": round(random.uniform(30.0, 70.0), 1),
        "acceleration_g": {
            "x": round(random.uniform(-1.0, 1.0), 2),
            "y": round(random.uniform(-1.0, 1.0), 2),
            "z": round(random.uniform(0.8, 1.2), 2),
        },
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def updater_loop():
    global latest_data
    while True:
        reading = generate_reading()
        with lock:
            latest_data = reading
        print(f"[updated] {reading}")
        time.sleep(60)  # once a minute


@app.on_event("startup")
def start_background_updater():
    thread = threading.Thread(target=updater_loop, daemon=True)
    thread.start()


@app.get("/sensor-data")
def get_sensor_data():
    with lock:
        return latest_data


@app.get("/")
def root():
    return {"status": "running", "endpoint": "/sensor-data"}


if __name__ == "__main__":
    import uvicorn
    # host 0.0.0.0 + $PORT so hosting platforms (Render, Railway, etc.) can bind it
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
