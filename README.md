# Camera Controller

Web-based controller for Pololu Tic stepper motor camera rig.

## Features

- Pan left/right
- Learn presets
- Go to presets
- Start/stop tour
- Tour delay slider for cinematic effect
- Energize/de-energize motor
- Reset zero position

## Requirements

- Raspberry Pi (or Linux)
- Python 3.9+
- Pololu Tic USB controller
- `ticlib` Python library

## Installation

```bash
git clone https://github.com/joelchicas/camera-controller.git
cd camera-controller/backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
