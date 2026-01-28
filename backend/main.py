import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import threading
import tic_controller

app = FastAPI()

# ---------------- STARTUP ----------------
@app.on_event("startup")
def startup_event():
    """
    Initialize the Tic motor controller once when FastAPI starts.
    """
    tic_controller.init_tic()

# ---------------- REQUEST MODELS ----------------
class DirCmd(BaseModel):
    direction: int  # 1 or -1

class SlotCmd(BaseModel):
    slot: int

class DelayCmd(BaseModel):
    delay: float

# ---------------- API ROUTES ----------------
@app.post("/api/pan/start")
def pan_start(cmd: DirCmd):
    tic_controller.pan_start(cmd.direction)
    return {"status": "moving"}

@app.post("/api/stop")
def stop():
    tic_controller.stop_motor()
    return {"status": "stopped"}

@app.post("/api/energize")
def energize():
    tic_controller.energize()
    return {"status": "energized"}

@app.post("/api/deenergize")
def deenergize():
    tic_controller.deenergize()
    return {"status": "deenergized"}

@app.post("/api/reset")
def reset():
    tic_controller.reset_position()
    return {"status": "reset"}

@app.post("/api/learn")
def learn(cmd: SlotCmd):
    tic_controller.learn(cmd.slot)
    return {"status": "saved"}

@app.post("/api/goto")
def goto(cmd: SlotCmd):
    tic_controller.go_to(cmd.slot)
    return {"status": "moving"}

@app.post("/api/tour/start")
def start_tour():
    t = threading.Thread(target=tic_controller.start_tour)
    t.daemon = True
    t.start()
    return {"status": "tour started"}

@app.post("/api/tour/stop")
def stop_tour():
    tic_controller.stop_tour()
    return {"status": "tour stopped"}

@app.post("/api/tour/delay")
def set_tour_delay(cmd: DelayCmd):
    tic_controller.set_tour_delay(cmd.delay)
    return {"status": "delay updated", "delay": cmd.delay}

# ---------------- STATIC FILES ----------------
# Absolute path to the 'web' folder (outside 'backend')
WEB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../web"))

# Serve static files (CSS, JS, images, etc.)
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

# Serve index.html at the root
@app.get("/")
def root():
    return FileResponse(os.path.join(WEB_DIR, "index.html"))
