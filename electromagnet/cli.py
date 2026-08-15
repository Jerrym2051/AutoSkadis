"""
Command-line interface for the Electromagnet Controller.

Usage:
    python -m electromagnet on [--channel A|B|both] [--polarity forward|reverse] [--duration SECONDS]
    python -m electromagnet off [--channel A|B|both]
    python -m electromagnet pulse --on-time SECONDS --off-time SECONDS [--cycles N] [--channel A|B|both]
"""

import argparse
import time
from typing import Optional


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="electromagnet",
        description="Control an electromagnet via Raspberry Pi + L298N H-bridge.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # -- on --
    on_p = sub.add_parser("on", help="Energize the magnet")
    on_p.add_argument(
        "--channel",
        choices=["A", "B", "both"],
        default="both",
        help="Channel to control (default: both)",
    )
    on_p.add_argument(
        "--polarity",
        choices=["forward", "reverse"],
        default="forward",
        help="Polarity (default: forward)",
    )
    on_p.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Auto-shutoff duration in seconds (overrides config default)",
    )
    on_p.add_argument(
        "--enb-pin",
        type=int,
        default=21,
        help="Channel B enable pin (default: 21, set to 0 to disable Channel B)",
    )
    on_p.add_argument(
        "--in3-pin",
        type=int,
        default=13,
        help="Channel B IN1 pin (default: 13)",
    )
    on_p.add_argument(
        "--in4-pin",
        type=int,
        default=26,
        help="Channel B IN2 pin (default: 26)",
    )

    # -- off --
    off_p = sub.add_parser("off", help="De-energize the magnet")
    off_p.add_argument(
        "--channel",
        choices=["A", "B", "both"],
        default="both",
        help="Channel to de-energize (default: both)",
    )
    off_p.add_argument(
        "--enb-pin",
        type=int,
        default=21,
        help="Channel B enable pin (default: 21, set to 0 to disable Channel B)",
    )
    off_p.add_argument(
        "--in3-pin",
        type=int,
        default=13,
        help="Channel B IN1 pin (default: 13)",
    )
    off_p.add_argument(
        "--in4-pin",
        type=int,
        default=26,
        help="Channel B IN2 pin (default: 26)",
    )

    # -- pulse --
    pulse_p = sub.add_parser("pulse", help="Run a series of on/off pulses")
    pulse_p.add_argument(
        "--channel",
        choices=["A", "B", "both"],
        default="both",
        help="Channel to pulse (default: both)",
    )
    pulse_p.add_argument(
        "--enb-pin",
        type=int,
        default=21,
        help="Channel B enable pin (default: 21, set to 0 to disable Channel B)",
    )
    pulse_p.add_argument(
        "--in3-pin",
        type=int,
        default=13,
        help="Channel B IN1 pin (default: 13)",
    )
    pulse_p.add_argument(
        "--in4-pin",
        type=int,
        default=26,
        help="Channel B IN2 pin (default: 26)",
    )
    pulse_p.add_argument(
        "--on-time",
        type=float,
        required=True,
        help="On duration in seconds",
    )
    pulse_p.add_argument(
        "--off-time",
        type=float,
        required=True,
        help="Off duration in seconds",
    )
    pulse_p.add_argument(
        "--cycles",
        type=int,
        default=1,
        help="Number of pulse cycles (default: 1)",
    )

    return parser


def _cmd_on(args: argparse.Namespace, ctrl: object) -> None:
    timeout = args.duration  # None means use config default

    print(f"[electromagnet] Energizing channel={args.channel}, polarity={args.polarity}")
    ctrl.energize(polarity=args.polarity, channel=args.channel, timeout=timeout)

    try:
        if args.duration is not None:
            time.sleep(args.duration)
        else:
            # Wait until safety timeout or Ctrl+C
            while ctrl.is_energized:
                time.sleep(0.5)
    except KeyboardInterrupt:
        print("[electromagnet] Interrupted, de-energizing...")
    finally:
        ctrl.de_energize(channel=args.channel)


def _cmd_off(args: argparse.Namespace, ctrl: object) -> None:
    print(f"[electromagnet] De-energizing channel={args.channel}...")
    ctrl.de_energize(channel=args.channel)


def _cmd_pulse(args: argparse.Namespace, ctrl: object) -> None:
    print(
        f"[electromagnet] Pulsing channel={args.channel}: on={args.on_time}s, off={args.off_time}s, cycles={args.cycles}"
    )
    try:
        for i in range(1, args.cycles + 1):
            ctrl.energize(channel=args.channel)
            time.sleep(args.on_time)
            ctrl.de_energize(channel=args.channel)
            time.sleep(args.off_time)
            print(f"  Pulse {i}/{args.cycles} complete")
    except KeyboardInterrupt:
        print("[electromagnet] Interrupted, de-energizing...")
    finally:
        ctrl.de_energize(channel=args.channel)


def main(argv: Optional[list] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Import here so the module can be imported without gpiozero on desktop
    from electromagnet import MagnetController

    # Build MagnetController with Channel B pins if specified
    # enb_pin=0 means disable Channel B, any positive value enables it
    enb_pin_raw = getattr(args, 'enb_pin', 21)
    enb_pin = enb_pin_raw if enb_pin_raw > 0 else None
    in3_pin = getattr(args, 'in3_pin', 13)
    in4_pin = getattr(args, 'in4_pin', 26)

    # Use context manager to guarantee cleanup
    with MagnetController(
        enb_pin=enb_pin,
        in3_pin=in3_pin,
        in4_pin=in4_pin,
    ) as ctrl:
        if args.command == "on":
            _cmd_on(args, ctrl)
        elif args.command == "off":
            _cmd_off(args, ctrl)
        elif args.command == "pulse":
            _cmd_pulse(args, ctrl)


if __name__ == "__main__":
    main()
