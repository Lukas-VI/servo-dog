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
class RuntimeConfig:
    camera_index: int = 0
    frame_width: int = 320
    frame_height: int = 240
    loop_hz: float = 14.0
    serial_port: str = "/dev/serial0"
    serial_baud: int = 9600
    stand_height: int = 144
    debug: bool = False
    pid: PIDConfig = field(default_factory=PIDConfig)
    colors_hsv: Dict[str, ColorRange] = field(default_factory=dict)


DEFAULT_COLORS: Dict[str, ColorRange] = {
    "blue": ((95, 70, 40), (130, 255, 255)),
    "green": ((40, 60, 40), (85, 255, 255)),
    "purple": ((125, 40, 40), (165, 255, 255)),
    "brown": ((5, 45, 30), (25, 230, 220)),
    "black": ((0, 0, 0), (180, 255, 80)),
}


def load_config(path: Optional[str]) -> RuntimeConfig:
    cfg = RuntimeConfig(colors_hsv=dict(DEFAULT_COLORS))
    if not path:
        return cfg
    if yaml is None:
        return cfg
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    for key, value in data.items():
        if key == "pid":
            for pid_key, pid_value in value.items():
                setattr(cfg.pid, pid_key, pid_value)
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
