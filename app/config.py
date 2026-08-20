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

MAGNET_ENA_PIN = int(os.getenv("MAGNET_ENA_PIN", "12"))
MAGNET_IN1_PIN = int(os.getenv("MAGNET_IN1_PIN", "6"))
MAGNET_IN2_PIN = int(os.getenv("MAGNET_IN2_PIN", "19"))
MAGNET_ENB_PIN = int(os.getenv("MAGNET_ENB_PIN", "21"))
MAGNET_IN3_PIN = int(os.getenv("MAGNET_IN3_PIN", "13"))
MAGNET_IN4_PIN = int(os.getenv("MAGNET_IN4_PIN", "26"))
MAGNET_CHANNEL = os.getenv("MAGNET_CHANNEL", "both")
MAGNET_MAX_ON_SECONDS = float(os.getenv("MAGNET_MAX_ON_SECONDS", "60"))
RELEASE_PULSE_DURATION = float(os.getenv("RELEASE_PULSE_DURATION", "0.2"))

APP_DIR = Path(__file__).resolve().parent
BINS_FILE = os.getenv("BINS_FILE", str(APP_DIR / "bins.json"))
