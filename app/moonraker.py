import time
from typing import Dict, Optional

import requests

from app.config import FAKE_MODE, MOONRAKER_URL, DELIVERY_X, DELIVERY_Y, DELIVERY_Z, PICKUP_Z, SAFE_Z, SLOW_SPEED, TRAVEL_SPEED


def _print_fake(message: str) -> None:
    print(f"[FAKE MOONRAKER] {message}")


def send_gcode(gcode: str) -> bool:
    """Send a G-code command to Moonraker or print a fake command."""
    if FAKE_MODE:
        _print_fake(gcode)
        return True

    try:
        response = requests.post(
            f"{MOONRAKER_URL}/printer/gcode/script",
            json={"script": gcode},
            timeout=5,
        )
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        raise RuntimeError(f"Moonraker request failed: {exc}") from exc


def check_moonraker() -> bool:
    """Check whether Moonraker is reachable."""
    if FAKE_MODE:
        return True

    try:
        response = requests.get(f"{MOONRAKER_URL}/server/info", timeout=3)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


def home_all() -> bool:
    return send_gcode("G28")


def wait_for_moves() -> None:
    time.sleep(0.2)


def move_xy(x: float, y: float) -> bool:
    send_gcode(f"G1 X{x:.1f} Y{y:.1f} F{TRAVEL_SPEED}")
    wait_for_moves()
    return True


def move_z(z: float) -> bool:
    send_gcode(f"G1 Z{z:.1f} F{SLOW_SPEED}")
    wait_for_moves()
    return True


def move_to_safe_z() -> bool:
    return move_z(SAFE_Z)


def move_to_pickup_z() -> bool:
    return move_z(PICKUP_Z)


def move_to_delivery() -> bool:
    move_xy(DELIVERY_X, DELIVERY_Y)
    return move_z(DELIVERY_Z)


def grip_open() -> bool:
    return send_gcode("SET_SERVO SERVO=gripper ANGLE=0")


def grip_close() -> bool:
    return send_gcode("SET_SERVO SERVO=gripper ANGLE=90")


def query_position() -> Dict[str, float]:
    if FAKE_MODE:
        return {"x": 0.0, "y": 0.0, "z": 0.0}
    return {"x": 0.0, "y": 0.0, "z": 0.0}
