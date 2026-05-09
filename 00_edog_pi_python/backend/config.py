from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    import yaml
except ImportError:  # Raspberry Pi base images often miss python3-yaml.
    yaml = None


ColorRange = Tuple[Tuple[int, int, int], Tuple[int, int, int]]


@dataclass
class PIDConfig:
    kp_side: float = 0.12
    kd_side: float = 0.04
    kp_yaw: float = 0.80
    kd_yaw: float = 0.18
    forward_speed: float = 0.18
    max_side: float = 0.22
    max_yaw: float = 0.9
    min_track_confidence: float = 0.18
    lost_rescue_s: float = 0.45
    lost_rescue_decay: float = 0.72


@dataclass
class BranchConfig:
    default_turn: str = "straight"
    fork_confidence: float = 0.18
    turn_bias: float = 0.28
    branch_error_blend: float = 0.85
    fork_speed_factor: float = 0.88
    branch_latch_s: float = 0.75


@dataclass
class VisionConfig:
    roi_start_ratio: float = 0.48
    gate_top_width_ratio: float = 0.66
    gate_bottom_width_ratio: float = 0.96
    exclude_background: bool = True
    stripe_min_width_ratio: float = 0.08
    stripe_max_width_ratio: float = 0.82
    temporal_smoothing: float = 0.35


@dataclass
class GamepadConfig:
    transport: str = "usb"
    web_command_path: str = "/tmp/edog_web_gamepad.json"
    axis_forward: int = 4
    axis_side: int = 3
    axis_yaw: int = 0
    axis_height: int = 1
    axis_roll: int = -1
    axis_pitch: int = -1
    axis_left_trigger: int = -1
    axis_right_trigger: int = -1
    button_emergency_stop: int = 1
    button_manual: int = 4
    manual_button_required: bool = False
    max_forward: float = 0.35
    max_side: float = 0.25
    max_yaw: float = 0.85
    max_roll: float = 0.0
    max_pitch: float = 0.0
    min_height: int = 100
    max_height: int = 180
    height_step: float = 1.8
    height_axis_step: float = 1.8
    deadzone: float = 0.10
    gait: int = 2
    mode_buttons: Dict[str, str] = field(default_factory=lambda: {"0": "track", "2": "stop", "3": "byroad_a", "5": "byroad_b"})
    action_buttons: Dict[str, str] = field(default_factory=lambda: {"6": "lean_left", "7": "lean_right"})


@dataclass
class RuntimeConfig:
    camera_index: int = 0
    frame_width: int = 240
    frame_height: int = 180
    loop_hz: float = 14.0
    serial_port: str = "/dev/serial0"
    serial_baud: int = 9600
    stand_height: int = 144
    runtime_status_path: str = "/tmp/edog_runtime_status.json"
    vision_status_path: str = "/tmp/edog_vision_status.json"
    vision_frame_path: str = "/tmp/edog_vision_frame.jpg"
    debug: bool = False
    pid: PIDConfig = field(default_factory=PIDConfig)
    branch: BranchConfig = field(default_factory=BranchConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    gamepad: GamepadConfig = field(default_factory=GamepadConfig)
    colors_hsv: Dict[str, ColorRange] = field(default_factory=dict)
    task_graph: Dict[str, Any] = field(default_factory=lambda: {"nodes": [], "edges": []})


DEFAULT_COLORS: Dict[str, ColorRange] = {
    "blue": ((95, 70, 40), (130, 255, 255)),
    "green": ((40, 60, 40), (85, 255, 255)),
    "purple": ((125, 40, 40), (165, 255, 255)),
    "brown": ((5, 45, 30), (25, 230, 220)),
    "black": ((0, 0, 0), (180, 255, 80)),
}


def _parse_scalar(value: str):
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


def _read_known_yaml(path: Path) -> Dict:
    data: Dict = {}
    if not path.exists():
        return data
    section = None
    color = None
    gamepad_map = None
    graph_list = None
    graph_item = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0 and line.endswith(":"):
            section = line[:-1]
            color = None
            gamepad_map = None
            graph_list = None
            graph_item = None
            data.setdefault(section, {})
        elif indent == 0 and ":" in line:
            key, value = line.split(":", 1)
            data[key] = _parse_scalar(value)
            section = None
            graph_list = None
            graph_item = None
        elif section in {"pid", "branch", "vision", "gamepad"} and indent == 2 and line.endswith(":"):
            gamepad_map = line[:-1].strip()
            data[section].setdefault(gamepad_map, {})
        elif section in {"pid", "branch", "vision", "gamepad"} and indent == 2 and ":" in line:
            key, value = line.split(":", 1)
            data[section][key.strip()] = _parse_scalar(value)
            gamepad_map = None
        elif section == "gamepad" and gamepad_map and indent == 4 and ":" in line:
            key, value = line.split(":", 1)
            data[section][gamepad_map][str(_parse_scalar(key))] = str(_parse_scalar(value))
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


def load_config(path: Optional[str]) -> RuntimeConfig:
    cfg = RuntimeConfig(colors_hsv=dict(DEFAULT_COLORS))
    if not path:
        return cfg
    if yaml is None:
        data = _read_known_yaml(Path(path))
    else:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    for key, value in data.items():
        if key == "pid":
            for pid_key, pid_value in value.items():
                setattr(cfg.pid, pid_key, pid_value)
        elif key == "branch":
            for branch_key, branch_value in value.items():
                setattr(cfg.branch, branch_key, branch_value)
        elif key == "vision":
            for vision_key, vision_value in value.items():
                setattr(cfg.vision, vision_key, vision_value)
        elif key == "gamepad":
            for gamepad_key, gamepad_value in value.items():
                if gamepad_key in {"mode_buttons", "action_buttons"}:
                    setattr(cfg.gamepad, gamepad_key, {str(k): str(v) for k, v in gamepad_value.items()})
                else:
                    setattr(cfg.gamepad, gamepad_key, gamepad_value)
        elif key == "colors_hsv":
            cfg.colors_hsv = {
                name: (tuple(v["min"]), tuple(v["max"]))
                for name, v in value.items()
            }
        elif key == "task_graph":
            cfg.task_graph = value or {"nodes": [], "edges": []}
        elif hasattr(cfg, key):
            setattr(cfg, key, value)
    return cfg


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
