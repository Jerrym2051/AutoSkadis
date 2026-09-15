# Copyright (c) 2026 Zerui Ma
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Full license: see LICENSE in the repository root.

"""Safe L298N electromagnet control using BCM-numbered GPIO pins."""

import atexit
import threading
from typing import Optional

from gpiozero import DigitalOutputDevice

CHANNEL_A = "A"
CHANNEL_B = "B"
CHANNEL_BOTH = "both"
POLARITY_FORWARD = "forward"
POLARITY_REVERSE = "reverse"
VALID_CHANNELS = (CHANNEL_A, CHANNEL_B, CHANNEL_BOTH)


class MagnetController:
    """Control one or two L298N channels with automatic safety shutoff."""

    def __init__(self, ena_pin: int = 12, in1_pin: int = 6, in2_pin: int = 19,
                 enb_pin: Optional[int] = None, in3_pin: int = 13, in4_pin: int = 26,
                 max_on_seconds: Optional[float] = 60) -> None:
        self._ena = DigitalOutputDevice(ena_pin, initial_value=False)
        self._in1 = DigitalOutputDevice(in1_pin, initial_value=False)
        self._in2 = DigitalOutputDevice(in2_pin, initial_value=False)
        self._enb = DigitalOutputDevice(enb_pin, initial_value=False) if enb_pin else None
        self._in3 = DigitalOutputDevice(in3_pin, initial_value=False) if enb_pin else None
        self._in4 = DigitalOutputDevice(in4_pin, initial_value=False) if enb_pin else None
        self._max_on_seconds = max_on_seconds
        self._states = {CHANNEL_A: False}
        if enb_pin:
            self._states[CHANNEL_B] = False
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.RLock()
        self._closed = False
        atexit.register(self.cleanup)

    @property
    def is_energized(self) -> bool:
        return any(self._states.values())

    def is_energized_channel(self, channel: str) -> bool:
        if channel not in (CHANNEL_A, CHANNEL_B):
            raise ValueError("channel must be 'A' or 'B'")
        return self._states.get(channel, False)

    def _channels(self, channel: str) -> list[str]:
        if channel not in VALID_CHANNELS:
            raise ValueError(f"invalid channel {channel!r}")
        if channel == CHANNEL_BOTH:
            return list(self._states)
        if channel not in self._states:
            raise ValueError(f"channel {channel!r} is not configured")
        return [channel]

    def energize(self, polarity: str = POLARITY_FORWARD, channel: str = CHANNEL_BOTH,
                 timeout: Optional[float] = None) -> None:
        if polarity not in (POLARITY_FORWARD, POLARITY_REVERSE):
            raise ValueError(f"invalid polarity {polarity!r}")
        with self._lock:
            if self._closed:
                raise RuntimeError("magnet controller is closed")
            for selected in self._channels(channel):
                enable, first, second = self._devices(selected)
                first.value = polarity == POLARITY_FORWARD
                second.value = polarity == POLARITY_REVERSE
                enable.on()
                self._states[selected] = True
                self._cancel_timer(selected)
                duration = self._max_on_seconds if timeout is None else timeout
                if duration and duration > 0:
                    timer = threading.Timer(duration, self.de_energize, kwargs={"channel": selected})
                    timer.daemon = True
                    self._timers[selected] = timer
                    timer.start()

    def de_energize(self, channel: str = CHANNEL_BOTH) -> None:
        with self._lock:
            if self._closed:
                return
            for selected in self._channels(channel):
                enable, first, second = self._devices(selected)
                enable.off()
                first.off()
                second.off()
                self._states[selected] = False
                self._cancel_timer(selected)

    def _devices(self, channel: str):
        if channel == CHANNEL_A:
            return self._ena, self._in1, self._in2
        return self._enb, self._in3, self._in4

    def _cancel_timer(self, channel: str) -> None:
        timer = self._timers.pop(channel, None)
        if timer:
            timer.cancel()

    def cleanup(self) -> None:
        with self._lock:
            if self._closed:
                return
            self.de_energize()
            for device in (self._ena, self._in1, self._in2, self._enb, self._in3, self._in4):
                if device is not None:
                    device.close()
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.cleanup()
