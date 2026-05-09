from __future__ import annotations

import argparse
import json
import signal
import time
from dataclasses import asdict
from pathlib import Path

from .config import load_config
from .control.backends import make_backend
from .input.gamepad import WebGamepadReader, make_gamepad_reader
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
    parser.add_argument("--no-vision", action="store_true", help="run gamepad/web control without opening a camera")
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
    gamepad = None if args.no_gamepad else make_gamepad_reader(cfg.gamepad, cfg.stand_height)
    web_control = None if args.no_gamepad else WebGamepadReader(cfg.gamepad.web_command_path)
    status_path = Path(cfg.runtime_status_path)
    vision_status_path = Path(cfg.vision_status_path)
    vision_frame_path = Path(cfg.vision_frame_path)
    stopping = False

    def pad_status(pad) -> dict:
        if not pad:
            return {"connected": False}
        data = asdict(pad)
        if pad.selected_mode:
            data["selected_mode"] = pad.selected_mode.value
        return data

    def write_status(reason: str, pad=None, last_decision: str = "") -> None:
        payload = {
            "ok": True,
            "updated_at": time.time(),
            "mode": state.mode.value,
            "backend": getattr(backend, "name", backend_kind),
            "reason": reason,
            "decision": last_decision,
            "gamepad": pad_status(pad),
            "last_frame_hex": getattr(backend, "last_frame_hex", ""),
            "last_serial_error": getattr(backend, "last_error", ""),
            "write_count": getattr(backend, "write_count", 0),
            "vision_available": vision_available,
            "map_pose": state.map_pose,
        }
        try:
            status_path.parent.mkdir(parents=True, exist_ok=True)
            status_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def write_vision_status(vision) -> None:
        if vision is None:
            return
        payload = {
            "ok": True,
            "updated_at": time.time(),
            "source": "auto_runtime",
            "vision": {
                "ok": True,
                "line_error": vision.line_error,
                "line_angle": vision.line_angle,
                "confidence": vision.confidence,
                "branches": list(vision.branches),
                "branch_confidence": vision.branch_confidence,
                "branch_offsets": vision.branch_offsets or {},
                "detected_colors": vision.detected_colors or {},
            },
        }
        try:
            vision_status_path.parent.mkdir(parents=True, exist_ok=True)
            vision_status_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            if vision.debug_frame is not None:
                ok, encoded = cv2.imencode(".jpg", vision.debug_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 58])
                if ok:
                    vision_frame_path.write_bytes(encoded.tobytes())
        except Exception:
            pass

    def request_stop(_signum, _frame) -> None:
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    source = args.video if args.video is not None else cfg.camera_index
    if isinstance(source, str) and source.isdigit():
        source = int(source)
    cap = None
    vision_available = not args.no_vision
    if vision_available:
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            backend.stop()
            print(f"[warn] unable to open video source: {source}; continuing in control-only mode")
            vision_available = False

    frame_period = 1.0 / cfg.loop_hz
    try:
        while not stopping:
            start = time.monotonic()
            vision = None
            if vision_available and cap is not None:
                ok, frame = cap.read()
                if ok:
                    vision = tracker.process(frame)
                    write_vision_status(vision)
                else:
                    print("[warn] camera read failed; switching to control-only mode")
                    cap.release()
                    cap = None
                    vision_available = False
            web_pad = web_control.poll() if web_control else None
            pad = web_pad if web_pad and web_pad.connected else (gamepad.poll() if gamepad else None)
            reason = "idle"
            if pad and pad.emergency_stop:
                state.set_mode(Mode.STOP)
                backend.stop()
                write_status("emergency_stop", pad, "stop")
                continue
            if pad and pad.manual_enabled:
                backend.send_motion(pad.motion)
                write_status("manual_motion", pad, "motion")
                continue
            if pad and pad.selected_action:
                backend.send_action(pad.selected_action)
                write_status("selected_action", pad, pad.selected_action)
                continue
            if pad and pad.selected_mode:
                state.set_mode(pad.selected_mode)
                reason = "selected_mode"
            elif vision is not None:
                decision = state.decide(vision)
                if decision.action == "stop":
                    backend.stop()
                    reason = "vision_stop"
                elif decision.action:
                    backend.send_action(decision.action)
                    reason = f"vision_action:{decision.action}"
                elif decision.motion:
                    backend.send_motion(decision.motion)
                    reason = "vision_motion"
            elif state.mode != Mode.STOP:
                backend.stop()
                reason = "control_only_no_vision_stop"
            write_status(reason, pad)

            elapsed = time.monotonic() - start
            if elapsed < frame_period:
                time.sleep(frame_period - elapsed)
    finally:
        try:
            backend.stop()
        finally:
            backend.close()
            if cap is not None:
                cap.release()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
