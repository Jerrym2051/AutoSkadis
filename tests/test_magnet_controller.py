# Copyright (c) 2026 Zerui Ma
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Full license: see LICENSE in the repository root.

import time

import pytest

gpiozero = pytest.importorskip("gpiozero")
from gpiozero import Device
from gpiozero.pins.mock import MockFactory

from app.magnet_controller import MagnetController


@pytest.fixture(autouse=True)
def mock_gpio():
    previous = Device.pin_factory
    Device.pin_factory = MockFactory()
    yield
    Device.pin_factory = previous


def test_controls_both_channels_and_polarity():
    controller = MagnetController(enb_pin=21, max_on_seconds=0)
    try:
        controller.energize(channel="both", polarity="reverse")
        assert controller.is_energized_channel("A")
        assert controller.is_energized_channel("B")
        controller.de_energize(channel="A")
        assert not controller.is_energized_channel("A")
        assert controller.is_energized_channel("B")
    finally:
        controller.cleanup()


def test_safety_timeout_deenergizes():
    controller = MagnetController(max_on_seconds=0.02)
    try:
        controller.energize(channel="A")
        time.sleep(0.06)
        assert not controller.is_energized
    finally:
        controller.cleanup()


def test_unconfigured_channel_is_rejected():
    controller = MagnetController(max_on_seconds=0)
    try:
        with pytest.raises(ValueError, match="not configured"):
            controller.energize(channel="B")
    finally:
        controller.cleanup()
