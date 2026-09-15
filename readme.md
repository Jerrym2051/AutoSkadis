# AutoSkadis

**AutoSkadis** is a Klipper-firmware 3D-printer-based robot that **retrieves and returns bins from a pegboard parts bin** (screws, resistors, LEDs, jumpers, etc.). It travels over an X/Y/Z cartesian gantry, uses a servo gripper plus **electromagnets** to pick up and release bins, locates bins with **AprilTags**, and exposes a simple **REST API**. A **pygame** dashboard on a small LCD shows live status, retrieved bins, a camera preview, and a HOME button.

> A work in progress. Hardware runs on a **Raspberry Pi 4**; the software also runs fully in **FAKE_MODE** on any OS so you can develop without the robot.

---

## How it works

```
                       +-----------------------+
   AprilTag camera --> |  FastAPI (app/main)   | <-->  REST clients / UI
                       +-----------+-----------+
                                   |
                          G-code via Moonraker (HTTP)
                                   |
                       +-----------v-----------+
                       |        Klipper        |
                       |  X/Y/Z steppers       |
                       |  + servo "gripper"    |
                       +-----------+-----------+
                                   |
                 gpiozero (BCM pins) --> L298N --> electromagnets

   display.py  -- reads -->  state.json  <-- writes --  simulator.py
```

- **`app/main.py`** — FastAPI service that orchestrates a full *retrieve* or *return* run: home → travel to a bin → drop Z → grip → magnet on/off → release pulse → carry to the delivery point.
- **`app/moonraker.py`** — sends G-code to the printer through Moonraker (`/printer/gcode/script`). In `FAKE_MODE` it just logs the command.
- **`app/magnet_controller.py` / `app/magnets.py`** — safe L298N electromagnet control over `gpiozero`, with an automatic de-energize timeout and cleanup-on-exit.
- **`app/bins.py`** — JSON-backed store (`app/bins.json`) of known bins: name, `x`, `y`, `tag_id`, `retrieved`.
- **`app/state.py`** — in-memory `RobotState` (status, current action, last error, action log).
- **`april_tag_detector.py`** — standalone OpenCV + `pyapriltags` tool to find/verify bin tags.
- **`display.py`** — fullscreen pygame UI for the Waveshare 3.5" LCD (480×320). Reads `state.json`.
- **`simulator.py`** — fakes retrieve/return activity and writes `state.json` so the display can be driven without hardware.

> **Note:** as of now the display and the simulator are connected through `state.json`, while the API service keeps its own in-memory state. The two are not yet fully wired together end-to-end.

---

## Features

- 🤖 **API-driven retrieve / return** of any registered bin.
- 📷 **AprilTag bin location** (OpenCV + pyapriltags).
- 🧲 **Safe electromagnet control** — L298N over `gpiozero` with an auto shutoff timer and guaranteed de-energize on exit.
- 🖥️ **Live LCD dashboard** — status indicator, scrolling bin "pills", picamera2 camera preview, and a touch HOME button.
- 🎭 **Simulator** to exercise the UI and state without the physical robot.
- 🧪 **FAKE_MODE** (default) so the API and tests run with no Klipper or GPIO hardware.
- ✅ **Unit tests** using `pytest` and `gpiozero`'s `MockFactory`.

---

## Project structure

```
AutoSkadis/
├── main.py                  # Thin re-export of the FastAPI app
├── app/
│   ├── main.py              # FastAPI app + REST endpoints
│   ├── config.py            # Env-driven configuration (pins, speeds, Z, FAKE_MODE)
│   ├── moonraker.py         # G-code bridge to Klipper via Moonraker
│   ├── magnet_controller.py # Low-level L298N / gpiozero controller (with safety)
│   ├── magnets.py           # Application adapter for the magnet controller
│   ├── bins.py              # JSON persistence for bins (app/bins.json)
│   ├── state.py             # In-memory RobotState
│   └── __init__.py
├── april_tag_detector.py    # Standalone AprilTag viewer
├── april_tag_detector_README.md
├── display.py               # pygame LCD dashboard (Waveshare 3.5", 480x320)
├── simulator.py             # Fakes activity and writes state.json
├── state.json               # Display/simulator state (tracked)
├── klipper/
│   └── printer.cfg.example  # Example Klipper config (XYZ steppers + gripper servo)
├── scripts/
│   └── start.sh             # uvicorn launcher
├── tests/
│   ├── test_app.py
│   └── test_magnet_controller.py
├── message.txt              # Design notes for the L298N electromagnet controller
├── requirements.txt
└── readme.md
```

## Requirements

### Python

- **Python 3.10+** (developed on **3.13**)

### Software (see `requirements.txt`)

| Package | Purpose |
|---|---|
| `fastapi`, `uvicorn[standard]` | REST API server |
| `pydantic` | Request models |
| `requests` | Moonraker HTTP client |
| `pytest` | Tests |
| `opencv-python`, `pyapriltags`, `numpy` | AprilTag detection |
| `pygame` | LCD dashboard |
| `gpiozero` | Electromagnet / GPIO control (hardware) |

### Hardware (Raspberry Pi 4)

- **Raspberry Pi 4** running Klipper + **Moonraker**.
- **XYZ cartesian gantry** (steppers) as configured in `klipper/printer.cfg.example`.
- **Servo** wired as the Klipper `gripper` servo (pick/drop).
- **L298N motor driver** + **electromagnets** for bin pickup (GPIO-controlled).
- **Waveshare 3.5" LCD (480×320)** for the dashboard.
- **Raspberry Pi Camera** — the dashboard uses **`picamera2`** (part of Raspberry Pi OS, not in `requirements.txt`).
- **USB / webcam** for `april_tag_detector.py`.

> `display.py` and the camera preview are Raspberry-Pi-specific. On a desktop you can run everything else (API, simulator, tests) in `FAKE_MODE`.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Jerrym2051/AutoSkadis.git
cd AutoSkadis
```

### 2. Create and activate a virtual environment

```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

On **Raspberry Pi OS**, `gpiozero` is usually pre-installed; otherwise `pip install gpiozero` works. `picamera2` ships with Raspberry Pi OS and is **not** in `requirements.txt`.

---

## Configuration

Most settings are read from environment variables with sensible defaults in `app/config.py`.

| Variable | Default | Description |
|---|---|---|
| `FAKE_MODE` | `true` | When true, no real Moonraker/GPIO calls are made (great for dev/tests). Set `false` on the robot. |
| `MOONRAKER_URL` | `http://localhost:7125` | Moonraker base URL. |
| `BINS_FILE` | `app/bins.json` | Path to the bin store. |
| `MAGNET_ENA_PIN` | `12` | L298N `ENA` (BCM). |
| `MAGNET_IN1_PIN` | `6` | L298N `IN1` (BCM). |
| `MAGNET_IN2_PIN` | `19` | L298N `IN2` (BCM). |
| `MAGNET_ENB_PIN` | `21` | L298N `ENB` (BCM). Set `0` to disable channel B. |
| `MAGNET_IN3_PIN` | `13` | L298N `IN3` (BCM). |
| `MAGNET_IN4_PIN` | `26` | L298N `IN4` (BCM). |
| `MAGNET_CHANNEL` | `both` | `A`, `B`, or `both`. |
| `MAGNET_MAX_ON_SECONDS` | `60` | Auto de-energize timeout (safety). |
| `RELEASE_PULSE_DURATION` | `0.2` | Duration of the reverse-polarity release pulse (s). |

Fixed kinematic constants (edit in `app/config.py`): `DELIVERY_X/Y/Z`, `SAFE_Z` (20), `PICKUP_Z` (5), `TRAVEL_SPEED` (3000), `SLOW_SPEED` (1000).

### Klipper

Copy the example config and adjust pins to match your machine:

```bash
cp klipper/printer.cfg.example ~/printer_data/config/printer.cfg
```

The example defines `[stepper_x/y/z]`, a `[servo gripper]`, and `G28` / `GRIP_OPEN` / `GRIP_CLOSE` macros.

## Running

### API server

```bash
# option 1: helper script
bash scripts/start.sh

# option 2: directly
uvicorn app.main:app --reload
```

The server starts on `http://127.0.0.1:8000`. Interactive API docs are available at **`http://127.0.0.1:8000/docs`**.

### Simulator (drives the dashboard)

```bash
python simulator.py
```

Periodically fakes retrieve/return actions and writes `state.json`, which the dashboard reads.

### LCD dashboard (Raspberry Pi)

```bash
python display.py
```

Fullscreen on the 480×320 panel. Press **Escape** to exit. Uses `picamera2` for the camera preview and shows a HOME button.

### AprilTag detector

```bash
python april_tag_detector.py            # webcam 0
python april_tag_detector.py --camera 1
python april_tag_detector.py --video vid.mp4
```

See `april_tag_detector_README.md` for options and tag families.

---

## API reference

Base URL: `http://127.0.0.1:8000`

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Service liveness + `fake_mode` flag. |
| `GET` | `/status` | Current `RobotState` (status, action, errors, log). |
| `GET` | `/bins` | List all registered bins. |
| `POST` | `/retrieve/{bin_name}` | Full pick sequence: bring a bin to the delivery point. |
| `POST` | `/return/{bin_name}` | Full return sequence: drop a bin back into its pegboard slot. |
| `POST` | `/register_bin` | Register a new bin (JSON body: `name`, `x`, `y`, `tag_id`). |
| `DELETE` | `/bin/{bin_name}` | Delete a bin from the store. |
| `POST` | `/home` | Home all axes (`G28`). |
| `POST` | `/magnets/on` | Energize the magnet(s). |
| `POST` | `/magnets/off` | De-energize the magnet(s). |
| `POST` | `/magnets/release` | Send a reverse-polarity release pulse. |

**Errors:** `409` if the system is busy, `404` for an unknown bin, `400` for an empty bin name, `500` on a runtime/hardware failure.

### Examples

```bash
# Status
curl http://127.0.0.1:8000/status

# List bins
curl http://127.0.0.1:8000/bins

# Register a bin
curl -X POST http://127.0.0.1:8000/register_bin \
  -H "Content-Type: application/json" \
  -d '{"name": "M3 screws", "x": 40, "y": 30, "tag_id": 1}'

# Retrieve a bin
curl -X POST http://127.0.0.1:8000/retrieve/"M3 screws"

# Return a bin
curl -X POST http://127.0.0.1:8000/return/"M3 screws"

# Home
curl -X POST http://127.0.0.1:8000/home
```

---

## Hardware wiring (L298N + electromagnets)

The design targets the **bottom rows of the 40-pin header (physical pins 27–40)** on a Raspberry Pi 4, which exposes **no 3V3/5V power pins**. The L298N's own onboard 5V regulator feeds its logic (jumper **ON**), so the Pi only supplies GPIO signals plus a **shared ground**.

| Signal | L298N pin | Pi (BCM) |
|---|---|---|
| `ENA` | ENA | GPIO12 (pin 32) |
| `IN1` | IN1 | GPIO6 (pin 31) |
| `IN2` | IN2 | GPIO19 (pin 35) |
| `ENB` | ENB | GPIO21 (pin 40) |
| `IN3` | IN3 | GPIO13 |
| `IN4` | IN4 | GPIO26 |
| `GND` | GND | any ground (30 / 34 / 39) |

- **Common ground is mandatory** between the Pi and the L298N.
- Power the L298N from an **external DC supply** sized for the coil current; do **not** feed 5V back into the Pi.
- The L298N drops ~1.4–2V across the H-bridge and runs hot — use a heatsink and don't run the coil at max current indefinitely.
- **Never use physical pins 27/28** (GPIO0/1) — they're reserved for HAT EEPROM detection.

The full rationale, including safety-timer design and testing approach, is in [`message.txt`](message.txt).

---

## Testing

```bash
pytest
```

- `tests/test_app.py` — bins persistence + `FAKE_MODE` behavior (uses a temp `BINS_FILE`).
- `tests/test_magnet_controller.py` — `MagnetController` behavior using `gpiozero.pins.mock.MockFactory`, including polarity, channel handling, and the **safety de-energize timeout**.

Run the suite on a desktop without hardware — no GPIO is required thanks to the mock pin factory.

---

## Safety notes

- The magnet controller **always de-energizes on exit/crash** (`atexit` + context manager).
- An **automatic timeout** (`MAGNET_MAX_ON_SECONDS`, default 60s) cuts power if a coil is left on.
- Keep a **shared ground** and never energize the coil at full current continuously without checking thermal margins.
- Always confirm **common ground** and **coil polarity** before first power-up on real hardware.

---

## Project status & license

AutoSkadis is a **work in progress**. The display/simulator path is functional end-to-end, and the API + magnet controller are unit-tested in `FAKE_MODE`; the full hardware loop (API → Klipper → magnets) is still being integrated.

No `LICENSE` file is currently included.



