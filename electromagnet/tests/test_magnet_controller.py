"""
Unit tests for electromagnet.magnet_controller using gpiozero's MockFactory.

Run with:
    python -m pytest electromagnet/tests/test_magnet_controller.py -v
"""

import time
import unittest
from unittest.mock import patch

from gpiozero.pins.mock import MockFactory, MockPWMServer

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
)
from electromagnet.magnet_controller import MagnetController


class MockPinFactory(unittest.TestCase):
    """Base class that sets up a MockFactory for each test."""

    def setUp(self):
        self.mock_pins = MockFactory(MockPWMServer)
        self.patch = patch(
            "gpiozero.RPiGPIOFactory",
            return_value=self.mock_pins,
        )
        self.patch.start()
        self.mock_pins.pin(ENA_PIN)
        self.mock_pins.pin(IN1_PIN)
        self.mock_pins.pin(IN2_PIN)
        self.mock_pins.pin(ENB_PIN)
        self.mock_pins.pin(IN3_PIN)
        self.mock_pins.pin(IN4_PIN)

    def tearDown(self):
        self.patch.stop()


class TestMagnetControllerChannelA(MockPinFactory):
    """Tests for Channel A control."""

    def test_energize_channel_a_forward(self):
        """Energize Channel A in forward polarity."""
        ctrl = MagnetController()
        try:
            ctrl.energize(channel="A")
            self.assertTrue(ctrl.is_energized_channel("A"))
            self.assertEqual(ctrl.polarity, "forward")
            self.assertEqual(ctrl._ena.value, 1)
        finally:
            ctrl.cleanup()

    def test_energize_channel_a_reverse(self):
        """Energize Channel A in reverse polarity."""
        ctrl = MagnetController()
        try:
            ctrl.energize(channel="A", polarity="reverse")
            self.assertTrue(ctrl.is_energized_channel("A"))
            self.assertEqual(ctrl._channel_state[CHANNEL_A]["polarity"], "reverse")
        finally:
            ctrl.cleanup()

    def test_energize_channel_b_fails_without_enb(self):
        """Energizing Channel B without enb_pin should not raise, but do nothing."""
        ctrl = MagnetController()
        try:
            ctrl.energize(channel="B")  # Channel B not configured
            # Channel A should still be off
            self.assertFalse(ctrl.is_energized_channel("A"))
        finally:
            ctrl.cleanup()


class TestMagnetControllerChannelB(MockPinFactory):
    """Tests for Channel B control with enb_pin."""

    def test_energize_channel_b(self):
        """Energize Channel B with enb_pin configured."""
        ctrl = MagnetController(enb_pin=ENB_PIN, in3_pin=IN3_PIN, in4_pin=IN4_PIN)
        try:
            ctrl.energize(channel="B")
            self.assertTrue(ctrl.has_channel_b)
            self.assertTrue(ctrl.is_energized_channel("B"))
            self.assertEqual(ctrl._enb.value, 1)
        finally:
            ctrl.cleanup()

    def test_energize_channel_b_reverse(self):
        """Energize Channel B in reverse polarity."""
        ctrl = MagnetController(enb_pin=ENB_PIN, in3_pin=IN3_PIN, in4_pin=IN4_PIN)
        try:
            ctrl.energize(channel="B", polarity="reverse")
            self.assertEqual(ctrl._channel_state[CHANNEL_B]["polarity"], "reverse")
        finally:
            ctrl.cleanup()


class TestMagnetControllerBothChannels(MockPinFactory):
    """Tests for controlling both channels together."""

    def test_energize_both_channels(self):
        """Energize both channels simultaneously."""
        ctrl = MagnetController(enb_pin=ENB_PIN, in3_pin=IN3_PIN, in4_pin=IN4_PIN)
        try:
            ctrl.energize(channel="both")
            self.assertTrue(ctrl.is_energized_channel("A"))
            self.assertTrue(ctrl.is_energized_channel("B"))
            self.assertTrue(ctrl.is_energized)
        finally:
            ctrl.cleanup()

    def test_de_energize_channel_a_only(self):
        """De-energize only Channel A, Channel B stays on."""
        ctrl = MagnetController(enb_pin=ENB_PIN, in3_pin=IN3_PIN, in4_pin=IN4_PIN)
        try:
            ctrl.energize(channel="both")
            ctrl.de_energize(channel="A")
            self.assertFalse(ctrl.is_energized_channel("A"))
            self.assertTrue(ctrl.is_energized_channel("B"))
            self.assertTrue(ctrl.is_energized)  # B is still on
        finally:
            ctrl.cleanup()

    def test_de_energize_both(self):
        """De-energize both channels."""
        ctrl = MagnetController(enb_pin=ENB_PIN, in3_pin=IN3_PIN, in4_pin=IN4_PIN)
        try:
            ctrl.energize(channel="both")
            ctrl.de_energize(channel="both")
            self.assertFalse(ctrl.is_energized_channel("A"))
            self.assertFalse(ctrl.is_energized_channel("B"))
            self.assertFalse(ctrl.is_energized)
        finally:
            ctrl.cleanup()


class TestMagnetControllerDeEnergize(MockPinFactory):
    """Tests for de_energize() method."""

    def test_de_energize_clears_state(self):
        """de_energize should set is_energized to False and ENA off."""
        ctrl = MagnetController()
        try:
            ctrl.energize()
            self.assertTrue(ctrl.is_energized)
            self.assertEqual(ctrl._ena.value, 1)
            ctrl.de_energize()
            self.assertFalse(ctrl.is_energized)
            self.assertEqual(ctrl._ena.value, 0)
        finally:
            ctrl.cleanup()

    def test_de_energize_is_idempotent(self):
        """Calling de_energize multiple times should not raise."""
        ctrl = MagnetController()
        try:
            ctrl.de_energize()
            ctrl.de_energize()
        finally:
            ctrl.cleanup()


class TestMagnetControllerSafetyTimeout(MockPinFactory):
    """Tests for the safety timeout feature."""

    def test_safety_timeout_cancels_on_de_energize(self):
        """Calling de_energize should cancel the safety timer."""
        ctrl = MagnetController(max_on_seconds=0.1)
        try:
            ctrl.energize()
            self.assertTrue(ctrl.is_energized)
            ctrl.de_energize()
            time.sleep(0.2)
            self.assertFalse(ctrl.is_energized)
        finally:
            ctrl.cleanup()

    def test_safety_timeout_can_be_disabled(self):
        """max_on_seconds=0 should disable the safety timeout."""
        ctrl = MagnetController(max_on_seconds=0)
        try:
            ctrl.energize()
            self.assertTrue(ctrl.is_energized)
        finally:
            ctrl.cleanup()

    def test_safety_timeout_can_be_disabled_via_flag(self):
        """disable_safety_timeout=True should disable the default timeout."""
        ctrl = MagnetController(disable_safety_timeout=True)
        try:
            ctrl.energize()
            self.assertTrue(ctrl.is_energized)
        finally:
            ctrl.cleanup()


class TestMagnetControllerContextManager(MockPinFactory):
    """Tests for context manager support."""

    def test_context_manager_cleans_up(self):
        """Exiting the context manager should call cleanup."""
        with MagnetController() as ctrl:
            ctrl.energize()
            self.assertTrue(ctrl.is_energized)
        ctrl.cleanup()  # should not raise


class TestMagnetControllerInvalidChannel(MockPinFactory):
    """Tests for invalid channel handling."""

    def test_invalid_channel_raises(self):
        """Invalid channel should raise ValueError."""
        ctrl = MagnetController()
        try:
            with self.assertRaises(ValueError):
                ctrl.energize(channel="invalid")
        finally:
            ctrl.cleanup()


if __name__ == "__main__":
    unittest.main()