"""
MagnetController class for controlling one or two L298N H-bridge channels.

Wraps gpiozero DigitalOutputDevice instances to provide a clean API for
electromagnet on/off control with polarity, safety timeout, and
cleanup-on-exit. Supports controlling Channel A, Channel B, or both together.
"""

import atexit
import threading
from contextlib import contextmanager
from typing import Optional

from gpiozero import DigitalOutputDevice

from electromagnet.config import (
    CHANNEL_A,
    CHANNEL_B,
    CHANNEL_BOTH,
    ENA_PIN,
    ENB_PIN,
    IN1_PIN,
    IN2_PIN,
    IN3_PIN,
    IN4_PIN,
    MAX_ON_SECONDS,
    POLARITY_FORWARD,
    POLARITY_REVERSE,
)

# Valid channel identifiers
VALID_CHANNELS = (CHANNEL_A, CHANNEL_B, CHANNEL_BOTH)


class MagnetController:
    """Controls one or two L298N motor channels for electromagnet actuation.

    Uses DigitalOutputDevice instances:
      - Channel A: ENA (enable), IN1/IN2 (direction/polarity)
      - Channel B: ENB (enable), IN3/IN4 (direction/polarity) [optional]

    Args:
        ena_pin: Channel A enable pin (BCM). Defaults to ENA_PIN.
        in1_pin: Channel A input 1 pin (BCM). Defaults to IN1_PIN.
        in2_pin: Channel A input 2 pin (BCM). Defaults to IN2_PIN.
        enb_pin: Channel B enable pin (BCM). Set to None to disable Channel B.
        in3_pin: Channel B input 1 pin (BCM). Defaults to IN3_PIN.
        in4_pin: Channel B input 2 pin (BCM). Defaults to IN4_PIN.
        max_on_seconds: Auto-shutoff timeout in seconds. Set to 0 or None to
            disable. Defaults to MAX_ON_SECONDS.
        disable_safety_timeout: If True, safety timeout is disabled by default.

    Example:
        # Single channel (Channel A only)
        with MagnetController() as ctrl:
            ctrl.energize()
            ctrl.de_energize()

        # Dual channel
        ctrl = MagnetController(enb_pin=21, in3_pin=13, in4_pin=26)
        ctrl.energize(channel="A")
        ctrl.energize(channel="B", polarity="reverse")
        ctrl.de_energize(channel="both")
    """

    def __init__(
        self,
        ena_pin: int = ENA_PIN,
        in1_pin: int = IN1_PIN,
        in2_pin: int = IN2_PIN,
        enb_pin: Optional[int] = None,
        in3_pin: int = IN3_PIN,
        in4_pin: int = IN4_PIN,
        max_on_seconds: Optional[float] = MAX_ON_SECONDS,
        disable_safety_timeout: bool = False,
    ) -> None:
        self._ena_pin = ena_pin
        self._in1_pin = in1_pin
        self._in2_pin = in2_pin
        self._enb_pin = enb_pin
        self._in3_pin = in3_pin
        self._in4_pin = in4_pin
        self._disabled_safety_timeout = disable_safety_timeout
        self._default_max_on = max_on_seconds if not disable_safety_timeout else 0
        self._has_channel_b = enb_pin is not None

        # Channel A devices (always created)
        self._ena = DigitalOutputDevice(pin=ena_pin, initial_value=0)
        self._in1 = DigitalOutputDevice(pin=in1_pin, initial_value=0)
        self._in2 = DigitalOutputDevice(pin=in2_pin, initial_value=0)

        # Channel B devices (created only if enb_pin is provided)
        self._enb: Optional[DigitalOutputDevice] = None
        self._in3: Optional[DigitalOutputDevice] = None
        self._in4: Optional[DigitalOutputDevice] = None
        if self._has_channel_b and enb_pin is not None:
            self._enb = DigitalOutputDevice(pin=enb_pin, initial_value=0)
            self._in3 = DigitalOutputDevice(pin=in3_pin, initial_value=0)
            self._in4 = DigitalOutputDevice(pin=in4_pin, initial_value=0)

        # Per-channel state
        self._channel_state: dict = {
            CHANNEL_A: {"energized": False, "polarity": POLARITY_FORWARD},
        }
        if self._has_channel_b:
            self._channel_state[CHANNEL_B] = {
                "energized": False,
                "polarity": POLARITY_FORWARD,
            }

        # Per-channel safety timeouts
        self._timeout_handles: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

        # Register atexit cleanup
        atexit.register(self.cleanup)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def energize(
        self,
        polarity: str = POLARITY_FORWARD,
        channel: str = CHANNEL_BOTH,
        timeout: Optional[float] = None,
    ) -> None:
        """Energize one or both magnet channels.

        Args:
            polarity: "forward" or "reverse".
            channel: "A", "B", or "both". Defaults to "both".
            timeout: Override safety timeout for this call. Set to 0 to disable.
        """
        if channel not in VALID_CHANNELS:
            raise ValueError(f"Invalid channel: {channel!r}. Must be one of {VALID_CHANNELS}")
        if polarity not in (POLARITY_FORWARD, POLARITY_REVERSE):
            raise ValueError(
                f"Invalid polarity: {polarity!r}. Must be 'forward' or 'reverse'."
            )

        with self._lock:
            channels_to_control = self._resolve_channel(channel)
            for ch in channels_to_control:
                self._energize_channel(ch, polarity)

            # Schedule safety timeouts for each channel
            for ch in channels_to_control:
                self._cancel_timeout(ch)
                effective_timeout = timeout if timeout is not None else self._default_max_on
                if effective_timeout and effective_timeout > 0:
                    self._timeout_handles[ch] = threading.Timer(
                        effective_timeout, self._safety_shutoff, args=[ch]
                    )
                    self._timeout_handles[ch].daemon = True
                    self._timeout_handles[ch].start()

    def de_energize(
        self,
        channel: str = CHANNEL_BOTH,
    ) -> None:
        """De-energize one or both magnet channels.

        Args:
            channel: "A", "B", or "both". Defaults to "both".
        """
        if channel not in VALID_CHANNELS:
            raise ValueError(f"Invalid channel: {channel!r}. Must be one of {VALID_CHANNELS}")

        with self._lock:
            channels_to_control = self._resolve_channel(channel)
            for ch in channels_to_control:
                self._de_energize_channel(ch)
                self._cancel_timeout(ch)

    def is_energized_channel(self, channel: str) -> bool:
        """Check if a specific channel is energized.

        Args:
            channel: "A" or "B".

        Returns:
            True if the channel is energized.
        """
        if channel not in (CHANNEL_A, CHANNEL_B):
            raise ValueError(f"Invalid channel: {channel!r}. Must be 'A' or 'B'.")
        if channel not in self._channel_state:
            return False
        return self._channel_state[channel]["energized"]

    @property
    def is_energized(self) -> bool:
        """Whether any channel is currently energized."""
        return any(s["energized"] for s in self._channel_state.values())

    @property
    def polarity(self) -> str:
        """Current polarity of Channel A (deprecated, use per-channel queries)."""
        return self._channel_state[CHANNEL_A]["polarity"]

    @property
    def has_channel_b(self) -> bool:
        """Whether Channel B is enabled on this controller."""
        return self._has_channel_b

    def cleanup(self) -> None:
        """De-energize all channels and release GPIO pins. Safe to call multiple times."""
        with self._lock:
            self._de_energize_channel(CHANNEL_A)
            self._cancel_timeout(CHANNEL_A)
            if self._has_channel_b:
                self._de_energize_channel(CHANNEL_B)
                self._cancel_timeout(CHANNEL_B)

        try:
            self._ena.close()
        except Exception:
            pass
        try:
            self._in1.close()
        except Exception:
            pass
        try:
            self._in2.close()
        except Exception:
            pass
        if self._has_channel_b:
            try:
                if self._enb:
                    self._enb.close()
            except Exception:
                pass
            try:
                if self._in3:
                    self._in3.close()
            except Exception:
                pass
            try:
                if self._in4:
                    self._in4.close()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "MagnetController":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_channel(self, channel: str) -> list[str]:
        """Convert channel spec to list of channels to control."""
        if channel == CHANNEL_BOTH:
            return [ch for ch in self._channel_state]
        return [channel]

    def _energize_channel(self, channel: str, polarity: str) -> None:
        """Energize a single channel."""
        if channel == CHANNEL_A:
            self._set_direction_a(polarity)
            self._ena.on()
            self._channel_state[CHANNEL_A]["energized"] = True
            self._channel_state[CHANNEL_A]["polarity"] = polarity
        elif channel == CHANNEL_B and self._has_channel_b:
            self._set_direction_b(polarity)
            if self._enb:
                self._enb.on()
            self._channel_state[CHANNEL_B]["energized"] = True
            self._channel_state[CHANNEL_B]["polarity"] = polarity

    def _de_energize_channel(self, channel: str) -> None:
        """De-energize a single channel."""
        if channel == CHANNEL_A:
            self._ena.off()
            self._in1.off()
            self._in2.off()
            self._channel_state[CHANNEL_A]["energized"] = False
        elif channel == CHANNEL_B and self._has_channel_b:
            if self._enb:
                self._enb.off()
            if self._in3:
                self._in3.off()
            if self._in4:
                self._in4.off()
            self._channel_state[CHANNEL_B]["energized"] = False

    def _set_direction_a(self, polarity: str) -> None:
        """Set Channel A direction pins."""
        if polarity == POLARITY_FORWARD:
            self._in1.on()
            self._in2.off()
        else:
            self._in1.off()
            self._in2.on()

    def _set_direction_b(self, polarity: str) -> None:
        """Set Channel B direction pins."""
        if polarity == POLARITY_FORWARD:
            if self._in3:
                self._in3.on()
            if self._in4:
                self._in4.off()
        else:
            if self._in3:
                self._in3.off()
            if self._in4:
                self._in4.on()

    def _cancel_timeout(self, channel: str) -> None:
        """Cancel any pending safety shutoff timer for a channel."""
        handle = self._timeout_handles.get(channel)
        if handle is not None:
            handle.cancel()
            del self._timeout_handles[channel]

    def _safety_shutoff(self, channel: str) -> None:
        """Safety callback: de-energize a channel when timeout fires."""
        with self._lock:
            if self._channel_state.get(channel, {}).get("energized"):
                self._de_energize_channel(channel)
                self._cancel_timeout(channel)


@contextmanager
def managed_magnet(
    max_on_seconds: Optional[float] = MAX_ON_SECONDS,
    disable_safety_timeout: bool = False,
    enb_pin: Optional[int] = None,
    in3_pin: int = IN3_PIN,
    in4_pin: int = IN4_PIN,
):
    """Context manager factory for creating a temporary MagnetController.

    Args:
        max_on_seconds: Safety timeout value.
        disable_safety_timeout: If True, timeout is off by default.
        enb_pin: Channel B enable pin (set to None for Channel A only).
        in3_pin: Channel B input 1 pin.
        in4_pin: Channel B input 2 pin.

    Yields:
        A MagnetController instance.

    Example:
        # Single channel
        with managed_magnet() as ctrl:
            ctrl.energize()
        # automatically cleaned up

        # Dual channel
        with managed_magnet(enb_pin=21) as ctrl:
            ctrl.energize(channel="both")
    """
    ctrl = MagnetController(
        max_on_seconds=max_on_seconds,
        disable_safety_timeout=disable_safety_timeout,
        enb_pin=enb_pin,
        in3_pin=in3_pin,
        in4_pin=in4_pin,
    )
    try:
        yield ctrl
    finally:
        ctrl.cleanup()