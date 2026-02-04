from ticlib import TicUSB
import json
import threading
import os
import time

# ---------------- CONFIG ----------------

PRESET_FILE = "presets.json"

PAN_SPEED = 25000

# Cinematic motion tuning
TOUR_DELAY = 10.0      # seconds between presets
MAX_ACCEL = 3000     # steps/sec^2
MAX_DECEL = 3000     # steps/sec^2

lock = threading.Lock()

# ---------------- CONSTANTS ----------------

STEP_MODE_FULL = 0
STEP_MODE_HALF = 1
STEP_MODE_QUARTER = 2
STEP_MODE_EIGHTH = 3
STEP_MODE_SIXTEENTH = 4

DECAY_MODE_FAST = 0
DECAY_MODE_SLOW = 1
DECAY_MODE_MIXED = 2

# ---------------- TIC INSTANCE ----------------

tic = None


def init_tic():
    global tic

    if tic is not None:
        return tic

    print("Initializing Pololu Tic controller...")

    tic = TicUSB()

    tic.exit_safe_start()
    tic.set_current_limit(1000)
    tic.set_step_mode(STEP_MODE_HALF)

    # --- Optional cinematic tuning (version safe) ---
    try:
        if hasattr(tic, "set_max_accel"):
            tic.set_max_accel(MAX_ACCEL)
            tic.set_max_decel(MAX_DECEL)
            print("Cinematic accel/decel enabled")
        else:
            print("Accel/decel tuning not supported by this ticlib version")
    except Exception as e:
        print("Accel tuning skipped:", e)

    print("Tic controller ready")

    return tic


# ---------------- PRESET STORAGE ----------------

if not os.path.exists(PRESET_FILE):
    with open(PRESET_FILE, "w") as f:
        json.dump({}, f)


def load_presets():
    with open(PRESET_FILE) as f:
        return json.load(f)


def save_presets(data):
    with open(PRESET_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ---------------- MOTOR CONTROL ----------------

def pan_start(direction: int):
    with lock:
        t = init_tic()
        t.set_target_velocity(PAN_SPEED * direction)


def stop_motor():
    with lock:
        t = init_tic()
        t.set_target_velocity(0)


def energize():
    with lock:
        t = init_tic()
        t.energize()


def deenergize():
    with lock:
        t = init_tic()
        t.deenergize()


def reset_position():
    with lock:
        t = init_tic()
        t.halt_and_set_position(0)


# ---------------- PRESET FUNCTIONS ----------------

def learn(slot: int):
    with lock:
        t = init_tic()
        presets = load_presets()
        pos = t.get_current_position()
        presets[str(slot)] = pos
        save_presets(presets)


def go_to(slot: int):
    with lock:
        presets = load_presets()
        pos = presets.get(str(slot))

        if pos is None:
            print(f"Preset {slot} not found")
            return

        t = init_tic()
        t.set_target_position(pos)


# ---------------- POSITION WAIT ----------------

def wait_until_position_reached(timeout=20):
    t = init_tic()

    # ✅ immediate exit if already at target
    if abs(t.get_current_position() - t.get_target_position()) <= 2:
        return
        
    start_time = time.time()

    while True:
        current = t.get_current_position()
        target = t.get_target_position()

        if abs(current - target) <= 2:
            break

        if time.time() - start_time > timeout:
            print("WARNING: Position wait timeout")
            break

        time.sleep(0.05)


# ---------------- TOUR MODE ----------------

tour_running = False


def start_tour():
    global tour_running

    tour_running = True

    energize()

    presets = load_presets()

    # ✅ stable numeric order
    positions = [presets[k] for k in sorted(presets, key=int)]

    if not positions:
        print("No presets saved")
        return

    print("Tour started")

    while tour_running:
        for pos in positions:
            if not tour_running:
                break

            print(f"Moving to {pos}")

            with lock:
                t = init_tic()
                t.set_target_position(pos)

            # ✅ re-assert target after planner settles    
            time.sleep(1)

            with lock:
                t.set_target_position(pos)    

            wait_until_position_reached()

            # thread-safe delay read
            with lock:
                delay = TOUR_DELAY

            time.sleep(delay)

    print("Tour stopped")


def stop_tour():
    global tour_running

    tour_running = False
    stop_motor()


def set_tour_delay(seconds: float):
    global TOUR_DELAY
    with lock:
        TOUR_DELAY = min(20.0, max(1.0, float(seconds)))

    print(f"Tour delay set to {TOUR_DELAY}s")


# ---------------- MANUAL TEST ----------------

if __name__ == "__main__":
    energize()

    try:
        print("Testing preset 1")
        go_to(1)
        wait_until_position_reached()
        print("Arrived")
    finally:
        deenergize()
