from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

from .config import load_config
from .models import VisionResult
from .vision.pure_vision import PureVisionTracker

try:
    import yaml
except ImportError:
    yaml = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config.yaml"
DEFAULT_FRONTEND = PROJECT_ROOT / "frontend"
DEFAULT_SLAM_DEMO = {
    "enabled": True,
    "mode": "feature_odometry",
    "feature_count": 90,
    "map_decay": 0.94,
    "motion_scale": 1.0,
    "loop_threshold": 0.42,
}
DEFAULT_BRANCH = {
    "default_turn": "straight",
    "fork_confidence": 0.18,
    "turn_bias": 0.28,
    "branch_error_blend": 0.85,
    "fork_speed_factor": 0.88,
    "branch_latch_s": 0.75,
}
DEFAULT_PID = {
    "kp_side": 0.12,
    "kd_side": 0.04,
    "kp_yaw": 0.80,
    "kd_yaw": 0.18,
    "forward_speed": 0.18,
    "max_side": 0.22,
    "max_yaw": 0.9,
    "min_track_confidence": 0.18,
    "lost_rescue_s": 0.45,
    "lost_rescue_decay": 0.72,
}
DEFAULT_VISION = {
    "roi_start_ratio": 0.48,
    "gate_top_width_ratio": 0.66,
    "gate_bottom_width_ratio": 0.96,
    "exclude_background": True,
    "stripe_min_width_ratio": 0.08,
    "stripe_max_width_ratio": 0.82,
    "temporal_smoothing": 0.35,
}
DEFAULT_GAMEPAD = {
    "transport": "usb",
    "web_command_path": "/tmp/edog_web_gamepad.json",
    "axis_forward": 4,
    "axis_side": 3,
    "axis_yaw": 0,
    "axis_height": 1,
    "axis_roll": -1,
    "axis_pitch": -1,
    "axis_left_trigger": -1,
    "axis_right_trigger": -1,
    "button_emergency_stop": 1,
    "button_manual": 4,
    "manual_button_required": False,
    "max_forward": 0.35,
    "max_side": 0.25,
    "max_yaw": 0.85,
    "max_roll": 0.0,
    "max_pitch": 0.0,
    "min_height": 100,
    "max_height": 180,
    "height_step": 1.8,
    "height_axis_step": 1.8,
    "deadzone": 0.10,
    "gait": 2,
    "mode_buttons": {"0": "track", "2": "stop", "3": "byroad_a", "5": "byroad_b"},
    "action_buttons": {"6": "lean_left", "7": "lean_right"},
}
DEFAULT_RUNTIME_STATUS = "/tmp/edog_runtime_status.json"
DEFAULT_VISION_STATUS = "/tmp/edog_vision_status.json"
DEFAULT_VISION_FRAME = "/tmp/edog_vision_frame.jpg"


@dataclass
class CameraState:
    source: str = "0"
    width: int = 640
    height: int = 480
    jpeg_quality: int = 72
    frame: Optional[bytes] = None
    vision_frame: Optional[bytes] = None
    vision: Optional[Dict[str, Any]] = None
    ok: bool = False
    message: str = "camera not started"
    frames: int = 0
    last_frame_at: float = 0.0


class CameraStream:
    def __init__(self, state: CameraState, config_path: Path = DEFAULT_CONFIG) -> None:
        self.state = state
        self.config_path = config_path
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="edog-camera-stream", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def snapshot(self) -> Tuple[Optional[bytes], Dict[str, Any]]:
        with self._lock:
            return self.state.frame, self.status()

    def vision_snapshot(self) -> Tuple[Optional[bytes], Dict[str, Any]]:
        with self._lock:
            status = self.status()
            status["vision"] = self.state.vision or {}
            return self.state.vision_frame, status

    def status(self) -> Dict[str, Any]:
        return {
            "ok": self.state.ok,
            "source": self.state.source,
            "width": self.state.width,
            "height": self.state.height,
            "frames": self.state.frames,
            "last_frame_at": self.state.last_frame_at,
            "message": self.state.message,
        }

    def _run(self) -> None:
        try:
            import cv2
        except Exception as exc:
            with self._lock:
                self.state.ok = False
                self.state.message = f"cv2 import failed: {exc}"
            return

        tracker: Optional[PureVisionTracker] = None
        try:
            tracker = PureVisionTracker(load_config(str(self.config_path)))
        except Exception as exc:
            with self._lock:
                self.state.vision = {"ok": False, "message": f"vision tracker init failed: {exc}"}

        source: Any = int(self.state.source) if str(self.state.source).isdigit() else self.state.source
        cap = cv2.VideoCapture(source)
        if self.state.width:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.state.width)
        if self.state.height:
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.state.height)

        if not cap.isOpened():
            with self._lock:
                self.state.ok = False
                self.state.message = f"unable to open camera source {self.state.source}"
            return

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), int(self.state.jpeg_quality)]
        while not self._stop.is_set():
            ok, frame = cap.read()
            if not ok:
                with self._lock:
                    self.state.ok = False
                    self.state.message = "camera read failed"
                time.sleep(0.15)
                continue
            ok, encoded = cv2.imencode(".jpg", frame, encode_param)
            if not ok:
                with self._lock:
                    self.state.ok = False
                    self.state.message = "jpeg encode failed"
                continue
            vision_frame = None
            vision_payload: Dict[str, Any] = {"ok": False, "message": "vision tracker disabled"}
            if tracker is not None:
                try:
                    result: VisionResult = tracker.process(frame)
                    ok_debug, encoded_debug = cv2.imencode(".jpg", result.debug_frame, encode_param)
                    if ok_debug:
                        vision_frame = encoded_debug.tobytes()
                    vision_payload = {
                        "ok": True,
                        "line_error": result.line_error,
                        "line_angle": result.line_angle,
                        "confidence": result.confidence,
                        "branches": list(result.branches),
                        "branch_confidence": result.branch_confidence,
                        "branch_offsets": result.branch_offsets or {},
                        "detected_colors": result.detected_colors or {},
                    }
                except Exception as exc:
                    vision_payload = {"ok": False, "message": str(exc)}
            with self._lock:
                self.state.frame = encoded.tobytes()
                if vision_frame:
                    self.state.vision_frame = vision_frame
                self.state.vision = vision_payload
                self.state.ok = True
                self.state.message = "streaming"
                self.state.frames += 1
                self.state.last_frame_at = time.time()
            time.sleep(0.03)
        cap.release()


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith("[") and value.endswith("]"):
        return [int(part.strip()) for part in value[1:-1].split(",") if part.strip()]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _read_known_yaml(path: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "pid": dict(DEFAULT_PID),
        "branch": dict(DEFAULT_BRANCH),
        "vision": dict(DEFAULT_VISION),
        "gamepad": dict(DEFAULT_GAMEPAD),
        "colors_hsv": {},
        "task_graph": {"nodes": [], "edges": []},
        "slam_demo": dict(DEFAULT_SLAM_DEMO),
    }
    if not path.exists():
        return data
    lines = path.read_text(encoding="utf-8").splitlines()
    section: Optional[str] = None
    color: Optional[str] = None
    graph_list: Optional[str] = None
    graph_item: Optional[Dict[str, Any]] = None
    gamepad_map: Optional[str] = None
    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0 and line.endswith(":"):
            section = line[:-1]
            color = None
            graph_list = None
            graph_item = None
            gamepad_map = None
        elif indent == 0 and ":" in line:
            key, value = line.split(":", 1)
            data[key] = _parse_scalar(value)
            section = None
            color = None
            graph_list = None
            graph_item = None
            gamepad_map = None
        elif section == "pid" and indent == 2 and ":" in line:
            key, value = line.split(":", 1)
            data["pid"][key] = _parse_scalar(value)
        elif section == "branch" and indent == 2 and ":" in line:
            key, value = line.split(":", 1)
            data["branch"][key.strip()] = _parse_scalar(value)
        elif section == "vision" and indent == 2 and ":" in line:
            key, value = line.split(":", 1)
            data["vision"][key.strip()] = _parse_scalar(value)
        elif section == "gamepad" and indent == 2 and line.endswith(":"):
            gamepad_map = line[:-1].strip()
            data["gamepad"].setdefault(gamepad_map, {})
        elif section == "gamepad" and indent == 2 and ":" in line:
            key, value = line.split(":", 1)
            data["gamepad"][key.strip()] = _parse_scalar(value)
        elif section == "gamepad" and gamepad_map and indent == 4 and ":" in line:
            key, value = line.split(":", 1)
            data["gamepad"][gamepad_map][str(_parse_scalar(key))] = str(_parse_scalar(value))
        elif section == "slam_demo" and indent == 2 and ":" in line:
            key, value = line.split(":", 1)
            data["slam_demo"][key.strip()] = _parse_scalar(value)
        elif section == "colors_hsv" and indent == 2 and line.endswith(":"):
            color = line[:-1]
            data["colors_hsv"][color] = {}
        elif section == "colors_hsv" and color and indent == 4 and ":" in line:
            key, value = line.split(":", 1)
            data["colors_hsv"][color][key] = _parse_scalar(value)
        elif section == "task_graph" and indent == 2 and line.endswith(":"):
            graph_list = line[:-1]
            graph_item = None
            data["task_graph"].setdefault(graph_list, [])
        elif section == "task_graph" and graph_list and indent == 4 and line.startswith("- ") and ":" in line:
            key, value = line[2:].split(":", 1)
            graph_item = {key.strip(): _parse_scalar(value)}
            data["task_graph"].setdefault(graph_list, []).append(graph_item)
        elif section == "task_graph" and graph_item is not None and indent == 6 and ":" in line:
            key, value = line.split(":", 1)
            graph_item[key.strip()] = _parse_scalar(value)
    return data


def read_config(path: Path) -> Dict[str, Any]:
    if yaml is not None and path.exists():
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    else:
        loaded = _read_known_yaml(path)
    loaded.setdefault("pid", dict(DEFAULT_PID))
    loaded.setdefault("branch", dict(DEFAULT_BRANCH))
    loaded.setdefault("vision", dict(DEFAULT_VISION))
    loaded.setdefault("gamepad", dict(DEFAULT_GAMEPAD))
    loaded.setdefault("colors_hsv", {})
    loaded.setdefault("task_graph", {"nodes": [], "edges": []})
    loaded.setdefault("slam_demo", dict(DEFAULT_SLAM_DEMO))
    loaded["task_graph"].setdefault("nodes", [])
    loaded["task_graph"].setdefault("edges", [])
    for key, value in DEFAULT_SLAM_DEMO.items():
        loaded["slam_demo"].setdefault(key, value)
    for key, value in DEFAULT_BRANCH.items():
        loaded["branch"].setdefault(key, value)
    for key, value in DEFAULT_PID.items():
        loaded["pid"].setdefault(key, value)
    for key, value in DEFAULT_VISION.items():
        loaded["vision"].setdefault(key, value)
    for key, value in DEFAULT_GAMEPAD.items():
        loaded["gamepad"].setdefault(key, value)
    return loaded


def _yaml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(str(item) for item in value) + "]"
    return str(value)


def dump_config(data: Dict[str, Any]) -> str:
    if yaml is not None:
        return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    lines = []
    for key in ["camera_index", "frame_width", "frame_height", "loop_hz", "serial_port", "serial_baud", "stand_height", "runtime_status_path", "vision_status_path", "vision_frame_path"]:
        if key in data:
            lines.append(f"{key}: {_yaml_value(data[key])}")
    lines.append("pid:")
    for key, value in (data.get("pid") or {}).items():
        lines.append(f"  {key}: {_yaml_value(value)}")
    lines.append("branch:")
    branch = data.get("branch") or DEFAULT_BRANCH
    for key, value in branch.items():
        lines.append(f"  {key}: {_yaml_value(value)}")
    lines.append("vision:")
    vision = data.get("vision") or DEFAULT_VISION
    for key, value in vision.items():
        lines.append(f"  {key}: {_yaml_value(value)}")
    lines.append("gamepad:")
    gamepad = data.get("gamepad") or DEFAULT_GAMEPAD
    for key, value in gamepad.items():
        if isinstance(value, dict):
            lines.append(f"  {key}:")
            for map_key, map_value in value.items():
                lines.append(f"    {_yaml_value(map_key)}: {_yaml_value(map_value)}")
        else:
            lines.append(f"  {key}: {_yaml_value(value)}")
    lines.append("colors_hsv:")
    for name, spec in (data.get("colors_hsv") or {}).items():
        lines.append(f"  {name}:")
        lines.append(f"    min: {_yaml_value(spec.get('min', [0, 0, 0]))}")
        lines.append(f"    max: {_yaml_value(spec.get('max', [180, 255, 255]))}")
    graph = data.get("task_graph") or {"nodes": [], "edges": []}
    lines.append("task_graph:")
    lines.append("  nodes:")
    for node in graph.get("nodes", []):
        lines.append(f"    - id: {_yaml_value(node.get('id', ''))}")
        for key in ["label", "type", "color", "action"]:
            if key in node:
                lines.append(f"      {key}: {_yaml_value(node[key])}")
    lines.append("  edges:")
    for edge in graph.get("edges", []):
        lines.append(f"    - from: {_yaml_value(edge.get('from', ''))}")
        lines.append(f"      to: {_yaml_value(edge.get('to', ''))}")
        if "condition" in edge:
            lines.append(f"      condition: {_yaml_value(edge['condition'])}")
    lines.append("slam_demo:")
    slam_demo = data.get("slam_demo") or DEFAULT_SLAM_DEMO
    for key, value in slam_demo.items():
        lines.append(f"  {key}: {_yaml_value(value)}")
    return "\n".join(lines) + "\n"


class DebugHandler(SimpleHTTPRequestHandler):
    config_path = DEFAULT_CONFIG
    camera: Optional[CameraStream] = None
    runtime_process: Optional[subprocess.Popen] = None

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/config":
            self._send_json(read_config(self.config_path))
            return
        if path == "/api/status":
            camera_status = self.camera.status() if self.camera else {"ok": False, "message": "camera disabled"}
            self._send_json({"ok": True, "config": str(self.config_path), "camera": camera_status})
            return
        if path == "/api/camera/status":
            self._send_json(self.camera.status() if self.camera else {"ok": False, "message": "camera disabled"})
            return
        if path == "/api/frame.jpg":
            self._send_frame()
            return
        if path == "/api/vision/frame.jpg":
            self._send_vision_frame()
            return
        if path == "/api/vision/status":
            self._send_vision_status()
            return
        if path == "/api/gamepad":
            self._send_gamepad()
            return
        if path == "/api/runtime/status":
            self._send_runtime_status()
            return
        if path == "/api/runtime/process":
            self._send_runtime_process()
            return
        if path == "/api/maps":
            self._send_maps()
            return
        if path.startswith("/api/maps/"):
            self._send_map(path)
            return
        if path == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if self.path == "/api/gamepad":
            self._receive_gamepad()
            return
        if path == "/api/runtime/auto":
            self._start_auto_runtime()
            return
        if path == "/api/runtime/stop":
            self._stop_auto_runtime()
            return
        if path.startswith("/api/maps/"):
            self._save_map(path)
            return
        if self.path != "/api/config":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length)
        try:
            data = json.loads(payload.decode("utf-8"))
            self.config_path.write_text(dump_config(data), encoding="utf-8")
        except Exception as exc:
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self._send_json({"ok": True, "config": str(self.config_path)})

    def _gamepad_command_path(self) -> Path:
        config = read_config(self.config_path)
        gamepad = config.get("gamepad") or {}
        return Path(str(gamepad.get("web_command_path", DEFAULT_GAMEPAD["web_command_path"])))

    def _runtime_status_path(self) -> Path:
        config = read_config(self.config_path)
        return Path(str(config.get("runtime_status_path", DEFAULT_RUNTIME_STATUS)))

    def _vision_status_path(self) -> Path:
        config = read_config(self.config_path)
        return Path(str(config.get("vision_status_path", DEFAULT_VISION_STATUS)))

    def _vision_frame_path(self) -> Path:
        config = read_config(self.config_path)
        return Path(str(config.get("vision_frame_path", DEFAULT_VISION_FRAME)))

    def _maps_dir(self) -> Path:
        return self.config_path.parent / "maps"

    def _map_path(self, request_path: str) -> Path:
        name = Path(urlparse(request_path).path).name
        if not name.endswith(".json"):
            name = f"{name}.json"
        safe = "".join(ch for ch in name if ch.isalnum() or ch in {"-", "_", "."})
        if not safe or safe in {".json", "..json"}:
            raise ValueError("invalid map name")
        return self._maps_dir() / safe

    def _send_runtime_status(self) -> None:
        path = self._runtime_status_path()
        if not path.exists():
            self._send_json({"ok": False, "message": "runtime status not found", "path": str(path)})
            return
        try:
            self._send_json(json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))

    def _send_runtime_process(self) -> None:
        proc = self.runtime_process
        running = bool(proc and proc.poll() is None)
        self._send_json({"ok": True, "running": running, "pid": proc.pid if running and proc else None})

    def _start_auto_runtime(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        data: Dict[str, Any] = {}
        if length:
            try:
                data = json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception:
                data = {}
        mode = str(data.get("mode") or "track")
        if mode not in {"track", "byroad_a", "byroad_b"}:
            self.send_error(HTTPStatus.BAD_REQUEST, "invalid auto mode")
            return
        proc = self.runtime_process
        if proc and proc.poll() is None:
            self._send_json({"ok": True, "running": True, "pid": proc.pid, "mode": mode, "message": "auto runtime already running"})
            return
        if self.camera:
            self.camera.stop()
        log_path = Path("/tmp/edog_auto_runtime.log")
        log = log_path.open("ab")
        env = dict(os.environ)
        extra_pythonpath = "/usr/local/lib/python3.7/site-packages/cv2/python-3.7:/home/pi/opencv/release/lib/python3"
        env["PYTHONPATH"] = f"{extra_pythonpath}:{env.get('PYTHONPATH', '')}"
        env.setdefault("SDL_VIDEODRIVER", "dummy")
        command = [str(PROJECT_ROOT / "run_serial.sh"), "--mode", mode]
        try:
            self.__class__.runtime_process = subprocess.Popen(command, cwd=str(PROJECT_ROOT), stdout=log, stderr=subprocess.STDOUT, env=env)
            log.close()
        except Exception as exc:
            log.close()
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        self._send_json({"ok": True, "running": True, "pid": self.runtime_process.pid, "mode": mode, "log": str(log_path)})

    def _stop_auto_runtime(self) -> None:
        proc = self.runtime_process
        if proc and proc.poll() is None:
            proc.send_signal(signal.SIGTERM)
            try:
                proc.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                proc.kill()
        self.__class__.runtime_process = None
        if self.camera:
            self.camera.start()
        self._send_json({"ok": True, "running": False})

    def _send_maps(self) -> None:
        root = self._maps_dir()
        maps = []
        if root.exists():
            for path in sorted(root.glob("*.json")):
                maps.append({"name": path.stem, "file": path.name, "updated_at": path.stat().st_mtime})
        self._send_json({"ok": True, "maps": maps, "dir": str(root)})

    def _send_map(self, request_path: str) -> None:
        try:
            path = self._map_path(request_path)
            if not path.exists():
                self.send_error(HTTPStatus.NOT_FOUND, "map not found")
                return
            self._send_json(json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))

    def _save_map(self, request_path: str) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length)
        try:
            data = json.loads(payload.decode("utf-8"))
            path = self._map_path(request_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self._send_json({"ok": True, "path": str(path)})

    def _send_vision_status(self) -> None:
        runtime_path = self._vision_status_path()
        if runtime_path.exists() and time.time() - runtime_path.stat().st_mtime < 2.5:
            try:
                self._send_json(json.loads(runtime_path.read_text(encoding="utf-8")))
                return
            except Exception:
                pass
        if not self.camera:
            self._send_json({"ok": False, "message": "camera disabled"})
            return
        _, status = self.camera.vision_snapshot()
        self._send_json(status)

    def _send_gamepad(self) -> None:
        path = self._gamepad_command_path()
        if not path.exists():
            self._send_json({"ok": True, "connected": False, "message": "no web gamepad command"})
            return
        try:
            self._send_json(json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))

    def _receive_gamepad(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length)
        try:
            data = json.loads(payload.decode("utf-8"))
            data["updated_at"] = time.time()
            path = self._gamepad_command_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        except Exception as exc:
            self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self._send_json({"ok": True, "path": str(path)})

    def _send_json(self, payload: Dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_frame(self) -> None:
        if not self.camera:
            self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "camera disabled")
            return
        frame, status = self.camera.snapshot()
        if not frame:
            self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, status.get("message", "no frame"))
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(frame)))
        self.end_headers()
        self.wfile.write(frame)

    def _send_vision_frame(self) -> None:
        runtime_frame = self._vision_frame_path()
        if runtime_frame.exists() and time.time() - runtime_frame.stat().st_mtime < 2.5:
            frame = runtime_frame.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(frame)))
            self.end_headers()
            self.wfile.write(frame)
            return
        if not self.camera:
            self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, "camera disabled")
            return
        frame, status = self.camera.vision_snapshot()
        if not frame:
            self.send_error(HTTPStatus.SERVICE_UNAVAILABLE, status.get("message", "no vision frame"))
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(frame)))
        self.end_headers()
        self.wfile.write(frame)


def main() -> int:
    parser = argparse.ArgumentParser(description="Browser debug console for e-Dog Python runtime")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--frontend", default=str(DEFAULT_FRONTEND))
    parser.add_argument("--camera-source", default="0", help="OpenCV VideoCapture source, for example 0 or /dev/video14")
    parser.add_argument("--camera-width", type=int, default=640)
    parser.add_argument("--camera-height", type=int, default=480)
    parser.add_argument("--jpeg-quality", type=int, default=72)
    parser.add_argument("--no-camera", action="store_true")
    args = parser.parse_args()

    frontend = Path(args.frontend).resolve()
    handler = lambda *h_args, **h_kwargs: DebugHandler(*h_args, directory=str(frontend), **h_kwargs)
    DebugHandler.config_path = Path(args.config).resolve()
    camera = None
    if not args.no_camera:
        camera = CameraStream(
            CameraState(
                source=args.camera_source,
                width=args.camera_width,
                height=args.camera_height,
                jpeg_quality=args.jpeg_quality,
            ),
            Path(args.config).resolve(),
        )
        camera.start()
    DebugHandler.camera = camera
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"debug console: http://{args.host}:{args.port}")
    print(f"config: {DebugHandler.config_path}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if camera:
            camera.stop()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
