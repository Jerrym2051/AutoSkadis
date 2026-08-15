"""Electromagnet controller package for Raspberry Pi + L298N H-bridge."""

# Config can always be imported (no hardware dependency)
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

__all__ = [
    "MagnetController",
    "CHANNEL_A",
    "CHANNEL_B",
    "CHANNEL_BOTH",
    "ENA_PIN",
    "ENB_PIN",
    "IN1_PIN",
    "IN2_PIN",
    "IN3_PIN",
    "IN4_PIN",
    "MAX_ON_SECONDS",
    "POLARITY_FORWARD",
    "POLARITY_REVERSE",
]


def __getattr__(name):
    """Lazy import of MagnetController only when first accessed."""
    if name == "MagnetController":
        from electromagnet.magnet_controller import MagnetController

        return MagnetController
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")