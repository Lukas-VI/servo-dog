#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.models import MotionCommand
from backend.protocol import frame_hex, pack_motion, pack_stop


def parse_hex_frame(text: str) -> bytes:
    cleaned = text.replace(",", " ").replace("0x", " ").replace("0X", " ")
    parts = [part for part in cleaned.split() if part]
    try:
        return bytes(int(part, 16) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid hex frame: {text}") from exc


def list_ports() -> int:
    try:
        from serial.tools import list_ports
    except Exception as exc:
        print(f"pyserial is required to list ports: {exc}", file=sys.stderr)
        return 2

    ports = list(list_ports.comports())
    if not ports:
        print("No serial ports found.")
        return 1
    for port in ports:
        print(f"{port.device}\t{port.description}\t{port.hwid}")
    return 0


def open_serial(port: str, baud: int):
    import serial

    return serial.Serial(
        port=port,
        baudrate=baud,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.25,
        write_timeout=0.25,
    )


def write_frame(port: str, baud: int, frame: bytes, *, repeat: int, interval: float) -> None:
    with open_serial(port, baud) as ser:
        for idx in range(repeat):
            ser.write(frame)
            ser.flush()
            print(f"write {idx + 1}/{repeat}: {frame_hex(frame)}")
            if interval > 0 and idx + 1 < repeat:
                time.sleep(interval)


def make_neutral_motion(height: int) -> bytes:
    return pack_motion(
        MotionCommand(
            forward=0.0,
            side=0.0,
            yaw=0.0,
            roll=0.0,
            pitch=0.0,
            stand_height=height,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "RS232 recovery helper. Defaults to dry-run; use --force to write. "
            "Known protocol here is the edog-brain high-level motion layer, not "
            "Action Designer private per-joint pulse-width calibration frames."
        )
    )
    parser.add_argument("--list-ports", action="store_true", help="list local serial ports and exit")
    parser.add_argument("--port", default="COM7", help="serial port, e.g. COM7 or /dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=9600, help="baud rate; e-Dog docs use 9600 8N1")
    parser.add_argument("--force", action="store_true", help="actually write to serial")
    parser.add_argument("--repeat", type=int, default=1, help="number of writes")
    parser.add_argument("--interval", type=float, default=0.08, help="seconds between repeated writes")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--stop", action="store_true", help="send known high-level stop frame")
    group.add_argument(
        "--neutral-stand",
        action="store_true",
        help="send known high-level zero velocity, zero roll/yaw/pitch stand frame",
    )
    group.add_argument(
        "--raw-hex",
        type=parse_hex_frame,
        metavar="HEX",
        help="send an explicitly supplied raw frame, e.g. '8F 00 01 0D 0E FF'",
    )
    parser.add_argument("--height", type=int, default=144, help="stand height for --neutral-stand")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_ports:
        return list_ports()

    if args.stop:
        frame = pack_stop()
        label = "known stop"
    elif args.neutral_stand:
        frame = make_neutral_motion(args.height)
        label = f"known neutral stand height={args.height}"
    elif args.raw_hex is not None:
        frame = args.raw_hex
        label = "raw hex"
    else:
        parser.error("choose --list-ports, --stop, --neutral-stand, or --raw-hex")

    print(f"mode: {label}")
    print(f"port: {args.port}, baud: {args.baud}, 8N1")
    print(f"frame: {frame_hex(frame)}")
    if not args.force:
        print("dry-run only. Add --force after physically supporting the robot.")
        return 0

    write_frame(args.port, args.baud, frame, repeat=max(1, args.repeat), interval=max(0.0, args.interval))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
