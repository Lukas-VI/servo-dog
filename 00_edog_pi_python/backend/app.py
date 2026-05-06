from __future__ import annotations

import argparse
import signal
import time
from pathlib import Path

from .config import load_config
from .control.backends import make_backend
from .input.gamepad import GamepadReader
from .models import Mode
from .state import EdogStateMachine
from .vision.pure_vision import PureVisionTracker, VisionDebug


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pure-vision e-Dog Python runtime")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--backend", default="dry-run", choices=["dry-run", "serial", "lcm"])
    parser.add_argument("--dry-run", action="store_true", help="force dry-run backend")
    parser.add_argument("--serial-port", default=None)
    parser.add_argument("--mode", default="stop", choices=[m.value for m in Mode])
    parser.add_argument("--video", default=None, help="camera index or video path")
    parser.add_argument("--debug-dir", default=None)
    parser.add_argument("--no-gamepad", action="store_true")
    return parser.parse_args()


def main() -> int:
    import cv2

    args = parse_args()
    cfg = load_config(args.config if Path(args.config).exists() else None)
    if args.serial_port:
        cfg.serial_port = args.serial_port

    backend_kind = "dry-run" if args.dry_run else args.backend
    backend = make_backend(backend_kind, cfg.serial_port, cfg.serial_baud)
    tracker = PureVisionTracker(
        cfg,
        VisionDebug(
            enabled=bool(args.debug_dir),
            out_dir=Path(args.debug_dir) if args.debug_dir else None,
        ),
    )
    state = EdogStateMachine(cfg, Mode(args.mode))
    gamepad = None if args.no_gamepad else GamepadReader()
    stopping = False

    def request_stop(_signum, _frame) -> None:
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    source = args.video if args.video is not None else cfg.camera_index
    if isinstance(source, str) and source.isdigit():
        source = int(source)
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        backend.stop()
        raise RuntimeError(f"unable to open video source: {source}")

    frame_period = 1.0 / cfg.loop_hz
    try:
        while not stopping:
            start = time.monotonic()
            ok, frame = cap.read()
            if not ok:
                break
            vision = tracker.process(frame)
            pad = gamepad.poll() if gamepad else None
            if pad and pad.selected_mode:
                state.set_mode(pad.selected_mode)
            if pad and pad.emergency_stop:
                backend.stop()
            elif pad and pad.manual_enabled:
                backend.send_motion(pad.motion)
            else:
                decision = state.decide(vision)
                if decision.action == "stop":
                    backend.stop()
                elif decision.action:
                    backend.send_action(decision.action)
                elif decision.motion:
                    backend.send_motion(decision.motion)

            elapsed = time.monotonic() - start
            if elapsed < frame_period:
                time.sleep(frame_period - elapsed)
    finally:
        try:
            backend.stop()
        finally:
            backend.close()
            cap.release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

