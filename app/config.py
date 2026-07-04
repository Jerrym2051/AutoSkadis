import os
from pathlib import Path

FAKE_MODE = os.getenv("FAKE_MODE", "true").lower() in {"1", "true", "yes", "on"}
MOONRAKER_URL = os.getenv("MOONRAKER_URL", "http://localhost:7125")

DELIVERY_X = 50
DELIVERY_Y = 50
DELIVERY_Z = 0
SAFE_Z = 20
PICKUP_Z = 5
TRAVEL_SPEED = 3000
SLOW_SPEED = 1000

GRIPPER_OPEN_POS = 0
GRIPPER_CLOSE_POS = 100

MAGNET_PINS = [17, 27]
RELEASE_PULSE_DURATION = 0.2

APP_DIR = Path(__file__).resolve().parent
BINS_FILE = os.getenv("BINS_FILE", str(APP_DIR / "bins.json"))
