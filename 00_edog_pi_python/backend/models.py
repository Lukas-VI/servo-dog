from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple


class Mode(str, Enum):
    STOP = "stop"
    TRACK = "track"
    BYROAD_A = "byroad_a"
    BYROAD_B = "byroad_b"
    LEAN_LEFT = "lean_left"
    LEAN_RIGHT = "lean_right"
    UP_DAIS = "updais"
    MANUAL = "manual"


@dataclass
class MotionCommand:
    forward: float = 0.0
    side: float = 0.0
    yaw: float = 0.0
    roll: float = 0.0
    pitch: float = 0.0
    stand_height: int = 144
    gait: int = 2


@dataclass
class VisionResult:
    line_error: float = 0.0
    line_angle: float = 0.0
    confidence: float = 0.0
    branches: Tuple[str, ...] = ()
    branch_confidence: float = 0.0
    branch_offsets: Optional[Dict[str, float]] = None
    detected_colors: Optional[Dict[str, float]] = None
    debug_frame: object = None


@dataclass
class GamepadCommand:
    connected: bool = False
    source: str = ""
    emergency_stop: bool = False
    manual_enabled: bool = False
    motion: MotionCommand = field(default_factory=MotionCommand)
    selected_mode: Optional[Mode] = None
    selected_action: Optional[str] = None
    raw_axes: Tuple[float, ...] = ()
    pressed_buttons: Tuple[int, ...] = ()
    hats: Tuple[Tuple[int, int], ...] = ()


@dataclass
class RuntimeStatus:
    mode: Mode
    backend: str
    frame_count: int = 0
    last_motion: MotionCommand = field(default_factory=MotionCommand)
    last_action: Optional[int] = None
    last_vision: VisionResult = field(default_factory=VisionResult)
    gamepad_connected: bool = False
    warnings: Tuple[str, ...] = ()
