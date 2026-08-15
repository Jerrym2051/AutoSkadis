# Electromagnet Controller (Raspberry Pi + L298N)

A Python package for controlling one or two electromagnets via a Raspberry Pi and L298N H-bridge motor controller. Provides on/off control with polarity, safety timeout, and a command-line interface.

## Hardware Requirements

- **Raspberry Pi 4** (or compatible with the same GPIO header)
- **L298N H-bridge breakout board** (one or two channels)
- **Electromagnet coil(s)** (rated for your power supply voltage)
- **External DC power supply** (battery pack or bench supply) sized for the magnet's coil current

## Wiring Diagram — Single Channel (Channel A Only)

| Pi Physical Pin | Pi GPIO (BCM) | Use | L298N Connection |
|---|---|---|---|
| 31 | GPIO6 | IN1 | `IN1` |
| 32 | GPIO12 | ENA | `ENA` (enable) |
| 35 | GPIO19 | IN2 | `IN2` |
| 30, 34, or 39 | GND | Common Ground | `GND` |
| - | - | Power Supply + | `+12V`/`VMS` screw terminal |
| - | - | Power Supply - | `GND` screw terminal |
| - | - | Coil + | `OUT1` |
| - | - | Coil - | `OUT2` |

## Wiring Diagram — Dual Channel (Channel A + Channel B)

| Pi Physical Pin | Pi GPIO (BCM) | Use | L298N Connection |
|---|---|---|---|
| 31 | GPIO6 | IN1 (Ch A) | `IN1` |
| 32 | GPIO12 | ENA (Ch A) | `ENA` |
| 35 | GPIO19 | IN2 (Ch A) | `IN2` |
| 33 | GPIO13 | IN3 (Ch B) | `IN3` |
| 37 | GPIO26 | IN4 (Ch B) | `IN4` |
| 40 | GPIO21 | ENB (Ch B) | `ENB` |
| 30, 34, or 39 | GND | Common Ground | `GND` |
| - | - | Power Supply + | `+12V`/`VMS` screw terminal |
| - | - | Power Supply - | `GND` screw terminal |
| Ch A Coil + | `OUT1` |
| Ch A Coil - | `OUT2` |
| Ch B Coil + | `OUT3` |
| Ch B Coil - | `OUT4` |

### ⚠️ Important Pin Constraints

- **Only physical pins 27-40 are accessible** in this design.
- **DO NOT use physical pins 27 (GPIO0) or 28 (GPIO1)** — they are reserved for HAT EEPROM auto-detection.
- **No 3V3 or 5V power pins exist in this range.** The L298N logic supply must come from its onboard regulator (leave the "5V-EN" jumper in place) or from a separate 5V source. **Do not connect any Pi power pin to the L298N.**
- A **shared ground** between Pi and L298N is **mandatory** for correct logic reference.

### L298N Jumper Setting

Leave the **"5V-EN" jumper in place** so the L298N board self-generates its 5V logic supply from the motor power input. This eliminates the need for a separate 5V logic supply.

### Voltage Drop Note

The L298N drops approximately 1.4–2V across its H-bridge transistors. Factor this into your supply voltage choice to ensure the magnet receives its rated current. The chip also runs hot under sustained current — use a heatsink and avoid running the coil continuously at max current without checking thermal margins.

## Installation

On Raspberry Pi OS:

```bash
sudo apt install python3-gpiozero
```

Or in a virtual environment:

```bash
pip install gpiozero
```

No Pi 5-specific packages are needed — this is designed for Raspberry Pi 4.

## Usage

### Command-Line Interface

```bash
# Energize both channels (forward polarity, safety timeout from config)
python -m electromagnet on

# Energize only Channel A
python -m electromagnet on --channel A

# Energize Channel B in reverse polarity for 10 seconds
python -m electromagnet on --channel B --polarity reverse --duration 10

# Turn off both channels
python -m electromagnet off

# Turn off only Channel A
python -m electromagnet off --channel A

# Pulse both channels: 1s on, 0.5s off, 5 cycles
python -m electromagnet pulse --on-time 1 --off-time 0.5 --cycles 5

# Pulse only Channel B
python -m electromagnet pulse --channel B --on-time 1 --off-time 0.5 --cycles 3
```

### Python API — Single Channel

```python
from electromagnet import MagnetController

# Use as context manager (auto-cleanup on exit)
with MagnetController() as ctrl:
    ctrl.energize(channel="A")
    # ... do work ...
    ctrl.de_energize(channel="A")

# Manual cleanup
ctrl = MagnetController()
try:
    ctrl.energize()  # Channel A only (default)
finally:
    ctrl.de_energize()
    ctrl.cleanup()
```

### Python API — Dual Channel

```python
from electromagnet import MagnetController

# Enable both channels by providing enb_pin
with MagnetController(enb_pin=21, in3_pin=13, in4_pin=26) as ctrl:
    # Control both channels together
    ctrl.energize(channel="both")

    # Control channels independently
    ctrl.energize(channel="A", polarity="forward")
    ctrl.energize(channel="B", polarity="reverse")

    # Query per-channel state
    print(ctrl.is_energized_channel("A"))  # True
    print(ctrl.is_energized_channel("B"))  # True
    print(ctrl.has_channel_b)              # True

    # Turn off only Channel A
    ctrl.de_energize(channel="A")
```

### Advanced API

```python
from electromagnet import MagnetController

# Disable safety timeout (for legitimate long-duration holds)
ctrl = MagnetController(disable_safety_timeout=True)
ctrl.energize(channel="A")

# Per-call timeout override
ctrl.energize(channel="A", timeout=120)  # 2-minute timeout instead of default

# Query state
print(ctrl.is_energized)       # True if any channel is on
print(ctrl.polarity)           # Channel A polarity
```

## Configuration

Edit `electromagnet/config.py` to change defaults:

| Constant | Default | Description |
|---|---|---|
| `IN1_PIN` | 6 | Channel A direction input 1 (BCM) |
| `IN2_PIN` | 19 | Channel A direction input 2 (BCM) |
| `ENA_PIN` | 12 | Channel A digital enable pin (BCM) |
| `IN3_PIN` | 13 | Channel B direction input 1 (BCM) |
| `IN4_PIN` | 26 | Channel B direction input 2 (BCM) |
| `ENB_PIN` | 21 | Channel B digital enable pin (BCM) |
| `MAX_ON_SECONDS` | 60 | Safety timeout default |

## Safety Features

- **Safety timeout**: Automatically de-energizes each channel after `MAX_ON_SECONDS` (default 60s) to prevent overheating.
- **atexit cleanup**: Coil is de-energized on process exit or crash via `atexit` registration.
- **Context manager**: Guaranteed cleanup when used with `with MagnetController()`.

## Testing

Run unit tests (uses `gpiozero.pins.mock.MockFactory` — no hardware needed):

```bash
python -m pytest electromagnet/tests/test_magnet_controller.py -v
```

## Project Structure

```
electromagnet/
├── __init__.py               # Package exports
├── config.py                 # Pin numbers, safety limits
├── magnet_controller.py      # MagnetController class
├── cli.py                    # CLI entry point
├── README.md                 # This file
└── tests/
    ├── __init__.py
    └── test_magnet_controller.py  # Unit tests