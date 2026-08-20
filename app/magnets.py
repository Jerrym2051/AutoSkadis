"""Application adapter for the L298N electromagnet controller."""

import time
from typing import Optional, TYPE_CHECKING

from app.config import (
    FAKE_MODE, MAGNET_CHANNEL, MAGNET_ENA_PIN, MAGNET_ENB_PIN,
    MAGNET_IN1_PIN, MAGNET_IN2_PIN, MAGNET_IN3_PIN, MAGNET_IN4_PIN,
    MAGNET_MAX_ON_SECONDS, RELEASE_PULSE_DURATION,
)

if TYPE_CHECKING:
    from app.magnet_controller import MagnetController

_controller: Optional["MagnetController"] = None


def setup_magnets() -> None:
    global _controller
    if FAKE_MODE:
        print("[FAKE MAGNETS] setup")
        return
    if _controller is None:
        try:
            from app.magnet_controller import MagnetController
        except ImportError as exc:
            raise RuntimeError("gpiozero is required for real magnet control") from exc
        _controller = MagnetController(
            ena_pin=MAGNET_ENA_PIN, in1_pin=MAGNET_IN1_PIN, in2_pin=MAGNET_IN2_PIN,
            enb_pin=MAGNET_ENB_PIN if MAGNET_ENB_PIN > 0 else None,
            in3_pin=MAGNET_IN3_PIN, in4_pin=MAGNET_IN4_PIN,
            max_on_seconds=MAGNET_MAX_ON_SECONDS,
        )


def magnets_on() -> None:
    setup_magnets()
    if FAKE_MODE:
        print("[FAKE MAGNETS] on")
    else:
        _controller.energize(channel=MAGNET_CHANNEL)


def magnets_off() -> None:
    if FAKE_MODE:
        print("[FAKE MAGNETS] off")
        return
    setup_magnets()
    _controller.de_energize(channel=MAGNET_CHANNEL)


def release_pulse() -> None:
    setup_magnets()
    if FAKE_MODE:
        print("[FAKE MAGNETS] release pulse")
        return
    _controller.energize(
        polarity="reverse", channel=MAGNET_CHANNEL, timeout=RELEASE_PULSE_DURATION
    )
    time.sleep(RELEASE_PULSE_DURATION)
    _controller.de_energize(channel=MAGNET_CHANNEL)


def cleanup_magnets() -> None:
    global _controller
    if FAKE_MODE:
        print("[FAKE MAGNETS] cleanup")
    elif _controller is not None:
        _controller.cleanup()
        _controller = None
