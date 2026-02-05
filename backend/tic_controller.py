from ticlib import TicUSB
import json
import threading
import os
import time
from fastapi import FastAPI, Request

app = FastAPI()

# ---------------- CONFIG ----------------

PRESET_FILE = "presets.json"
PAN_SPEED = 25000
TOUR_DELAY = 10.0
MAX_ACCEL = 3000
MAX_DECEL = 3000

lock = threading.Lock()

# ---------------- TIC INSTANCE ----------------

tic = None

def init_tic():
    global tic
    if tic is not None:
        return tic

    tic = TicUSB()
    tic.exit_safe_start()
    tic.set_current_limit(1000)
    tic.set_step_mode(1)

    if hasattr(tic, "set_max_accel"):
        tic.set_max_accel(MAX_ACCEL)
        tic.set_max_decel(MAX_DECEL)

    return tic

# ---------------- MOTOR CONTROL ----------------

@app.post("/api/pan/start")
async def pan_start(data: dict):
    direction = int(data["direction"])
    with lock:
        t = init_tic()
        t.set_target_velocity(PAN_SPEED * direction)
    return {"ok": True}

@app.post("/api/pan/slider")
async def pan_slider(data: dict):
    value = float(data["value"])
    with lock:
        t = init_tic()
        t.set_target_velocity(int(PAN_SPEED * value))
    return {"ok": True}

@app.post("/api/stop")
async def stop_motor():
    with lock:
        t = init_tic()
        t.set_target_velocity(0)
    return {"ok": True}

# ---------------- TOUR DELAY ----------------

@app.post("/api/tour/delay")
async def set_tour_delay(data: dict):
    global TOUR_DELAY
    with lock:
        TOUR_DELAY = min(20.0, max(2.0, float(data["delay"])))
    return {"delay": TOUR_DELAY}
