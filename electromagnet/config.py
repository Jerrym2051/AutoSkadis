"""
Configuration constants for the Raspberry Pi + L298N Electromagnet Controller.

Pin Mapping (BCM numbering, matching physical pins 27-40):
  - ENA_PIN = 12 (physical pin 32, GPIO12, digital OUT) -> L298N ENA (enable)
  - IN1_PIN = 6  (physical pin 31, GPIO6)              -> L298N IN1 (direction)
  - IN2_PIN = 19 (physical pin 35, GPIO19)             -> L298N IN2 (direction)

NOTE: ENA_PIN is used as a plain digital enable/cutoff line (not PWM).
When ENA is HIGH, the magnet channel is enabled. When LOW, it is disabled.

CONSTRAINT: Only the bottom 7 pin rows of the 40-pin header are accessible
(physical pins 27-40). Physical pins 27/28 (GPIO0/ID_SD, GPIO1/ID_SC) are
reserved for HAT EEPROM auto-detection and MUST NOT be used as general-purpose
I/O. No 3V3 or 5V power pins exist in this range, so the L298N logic supply
must come from its onboard regulator (jumper ON) or external 5V source.

Shared ground between Pi and L298N is mandatory for correct logic reference.
"""

# L298N Channel A control pins (BCM numbering)
IN1_PIN = 6
IN2_PIN = 19
ENA_PIN = 12  # Digital enable pin (physical pin 32)

# L298N Channel B control pins (BCM numbering)
IN3_PIN = 13
IN4_PIN = 26
ENB_PIN = 21  # Digital enable pin (physical pin 40)

# Safety configuration
MAX_ON_SECONDS = 60  # Maximum continuous energize time before auto-shutoff

# Polarity options
POLARITY_FORWARD = "forward"
POLARITY_REVERSE = "reverse"

# Channel options
CHANNEL_A = "A"
CHANNEL_B = "B"
CHANNEL_BOTH = "both"
