from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple

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


@dataclass
class BranchConfig:
    default_turn: str = "straight"
    fork_confidence: float = 0.18
    turn_bias: float = 0.28


@dataclass
class GamepadConfig:
    transport: str = "usb"
    web_command_path: str = "/tmp/edog_web_gamepad.json"
    axis_forward: int = 1
    axis_side: int = 0
    axis_roll: int = 2
    axis_pitch: int = 3
    axis_left_trigger: int = 4
    axis_right_trigger: int = 5
    button_emergency_stop: int = 1
    button_manual: int = 4
    max_forward: float = 0.35
    max_side: float = 0.25
    max_roll: float = 0.25
    max_pitch: float = 0.25
    min_height: int = 100
    max_height: int = 180
    height_step: float = 1.8
    deadzone: float = 0.10
    gait: int = 2
    mode_buttons: Dict[str, str] = field(default_factory=lambda: {"0": "track", "2": "stop"})
    action_buttons: Dict[str, str] = field(default_factory=lambda: {"3": "updais", "5": "lean_left", "6": "lean_right"})


@dataclass
class RuntimeConfig:
    camera_index: int = 0
    frame_width: int = 240
    frame_height: int = 180
    loop_hz: float = 14.0
    serial_port: str = "/dev/serial0"
    serial_baud: int = 9600
    stand_height: int = 144
    debug: bool = False
    pid: PIDConfig = field(default_factory=PIDConfig)
    branch: BranchConfig = field(default_factory=BranchConfig)
    gamepad: GamepadConfig = field(default_factory=GamepadConfig)
    colors_hsv: Dict[str, ColorRange] = field(default_factory=dict)


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
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0 and line.endswith(":"):
            section = line[:-1]
            color = None
            gamepad_map = None
            data.setdefault(section, {})
        elif indent == 0 and ":" in line:
            key, value = line.split(":", 1)
            data[key] = _parse_scalar(value)
            section = None
        elif section in {"pid", "branch", "gamepad"} and indent == 2 and line.endswith(":"):
            gamepad_map = line[:-1].strip()
            data[section].setdefault(gamepad_map, {})
        elif section in {"pid", "branch", "gamepad"} and indent == 2 and ":" in line:
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
        elif hasattr(cfg, key):
            setattr(cfg, key, value)
    return cfg


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
