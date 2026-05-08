from __future__ import annotations

import argparse
import json
import threading
import time
from dataclasses import dataclass
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

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
}


@dataclass
class CameraState:
    source: str = "0"
    width: int = 640
    height: int = 480
    jpeg_quality: int = 72
    frame: Optional[bytes] = None
    ok: bool = False
    message: str = "camera not started"
    frames: int = 0
    last_frame_at: float = 0.0


class CameraStream:
    def __init__(self, state: CameraState) -> None:
        self.state = state
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="edog-camera-stream", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def snapshot(self) -> Tuple[Optional[bytes], Dict[str, Any]]:
        with self._lock:
            return self.state.frame, self.status()

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
            with self._lock:
                self.state.frame = encoded.tobytes()
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
        "pid": {},
        "branch": dict(DEFAULT_BRANCH),
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
    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0 and line.endswith(":"):
            section = line[:-1]
            color = None
        elif indent == 0 and ":" in line:
            key, value = line.split(":", 1)
            data[key] = _parse_scalar(value)
            section = None
            color = None
        elif section == "pid" and indent == 2 and ":" in line:
            key, value = line.split(":", 1)
            data["pid"][key] = _parse_scalar(value)
        elif section == "branch" and indent == 2 and ":" in line:
            key, value = line.split(":", 1)
            data["branch"][key.strip()] = _parse_scalar(value)
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
    loaded.setdefault("pid", {})
    loaded.setdefault("branch", dict(DEFAULT_BRANCH))
    loaded.setdefault("colors_hsv", {})
    loaded.setdefault("task_graph", {"nodes": [], "edges": []})
    loaded.setdefault("slam_demo", dict(DEFAULT_SLAM_DEMO))
    loaded["task_graph"].setdefault("nodes", [])
    loaded["task_graph"].setdefault("edges", [])
    for key, value in DEFAULT_SLAM_DEMO.items():
        loaded["slam_demo"].setdefault(key, value)
    for key, value in DEFAULT_BRANCH.items():
        loaded["branch"].setdefault(key, value)
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
    for key in ["camera_index", "frame_width", "frame_height", "loop_hz", "serial_port", "serial_baud", "stand_height"]:
        if key in data:
            lines.append(f"{key}: {_yaml_value(data[key])}")
    lines.append("pid:")
    for key, value in (data.get("pid") or {}).items():
        lines.append(f"  {key}: {_yaml_value(value)}")
    lines.append("branch:")
    branch = data.get("branch") or DEFAULT_BRANCH
    for key, value in branch.items():
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
        if path == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return
        super().do_GET()

    def do_POST(self) -> None:
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
            )
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
