import time
from typing import Optional

from app.config import FAKE_MODE, MAGNET_PINS, RELEASE_PULSE_DURATION

try:
    import RPi.GPIO as GPIO
except ImportError:  # pragma: no cover - normal on desktop computers
    GPIO = None


_pin_setup_done = False


def setup_magnets() -> None:
    """Configure GPIO pins for magnet control."""
    global _pin_setup_done
    if FAKE_MODE:
        print("[FAKE MAGNETS] setup")
        _pin_setup_done = True
        return

    if GPIO is None:
        raise RuntimeError("RPi.GPIO is not available on this machine")

    GPIO.setmode(GPIO.BCM)
    for pin in MAGNET_PINS:
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
    _pin_setup_done = True


def magnets_on() -> None:
    """Turn magnets on with forward polarity."""
    if not _pin_setup_done:
        setup_magnets()

    if FAKE_MODE:
        print("[FAKE MAGNETS] on")
        return

    if GPIO is None:
        raise RuntimeError("RPi.GPIO is not available on this machine")

    GPIO.output(MAGNET_PINS[0], GPIO.HIGH)
    GPIO.output(MAGNET_PINS[1], GPIO.LOW)


def magnets_off() -> None:
    """Turn magnets off by driving all pins low."""
    if not _pin_setup_done:
        setup_magnets()

    if FAKE_MODE:
        print("[FAKE MAGNETS] off")
        return

    if GPIO is None:
        raise RuntimeError("RPi.GPIO is not available on this machine")

    for pin in MAGNET_PINS:
        GPIO.output(pin, GPIO.LOW)


def release_pulse() -> None:
    """Apply a short reverse-polarity pulse to release the bin."""
    if not _pin_setup_done:
        setup_magnets()

    if FAKE_MODE:
        print("[FAKE MAGNETS] release pulse")
        return

    if GPIO is None:
        raise RuntimeError("RPi.GPIO is not available on this machine")

    GPIO.output(MAGNET_PINS[0], GPIO.LOW)
    GPIO.output(MAGNET_PINS[1], GPIO.HIGH)
    time.sleep(RELEASE_PULSE_DURATION)
    magnets_off()


def cleanup_magnets() -> None:
    """Reset GPIO and clean up the pins."""
    if FAKE_MODE:
        print("[FAKE MAGNETS] cleanup")
        return

    if GPIO is None:
        return

    magnets_off()
    GPIO.cleanup()
