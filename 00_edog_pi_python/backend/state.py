from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Optional

from .config import RuntimeConfig, clamp
from .models import Mode, MotionCommand, VisionResult


COLOR_ACTIONS = {
    "blue": ("updais", Mode.UP_DAIS),
    "brown": ("lean_left", Mode.LEAN_LEFT),
    "purple": ("lean_right", Mode.LEAN_RIGHT),
}


@dataclass
class StateDecision:
    mode: Mode
    motion: Optional[MotionCommand] = None
    action: Optional[str] = None
    reason: str = ""


class EdogStateMachine:
    def __init__(self, cfg: RuntimeConfig, mode: Mode = Mode.STOP) -> None:
        self.cfg = cfg
        self.mode = mode
        self._last_error = 0.0
        self._last_time = monotonic()
        self._action_until = 0.0

    def set_mode(self, mode: Mode) -> None:
        self.mode = mode

    def decide(self, vision: VisionResult) -> StateDecision:
        now = monotonic()
        if self.mode == Mode.STOP:
            return StateDecision(Mode.STOP, action="stop", reason="stop mode")
        if now < self._action_until:
            return StateDecision(self.mode, reason="action cooldown")

        if vision.detected_colors:
            for color, score in sorted(
                vision.detected_colors.items(), key=lambda item: item[1], reverse=True
            ):
                if score >= 0.18 and color in COLOR_ACTIONS:
                    action, next_mode = COLOR_ACTIONS[color]
                    self.mode = next_mode
                    self._action_until = now + 1.2
                    return StateDecision(next_mode, action=action, reason=f"color {color}")

        if self.mode in {Mode.TRACK, Mode.BYROAD_A, Mode.BYROAD_B, Mode.LEAN_LEFT, Mode.LEAN_RIGHT, Mode.UP_DAIS}:
            return StateDecision(Mode.TRACK, motion=self._track_motion(vision), reason="vision track")

        return StateDecision(self.mode, action="stop", reason="fallback")

    def _track_motion(self, vision: VisionResult) -> MotionCommand:
        now = monotonic()
        dt = max(now - self._last_time, 1.0 / self.cfg.loop_hz)
        derivative = (vision.line_error - self._last_error) / dt
        self._last_error = vision.line_error
        self._last_time = now

        side = -(self.cfg.pid.kp_side * vision.line_error + self.cfg.pid.kd_side * derivative)
        yaw = -(self.cfg.pid.kp_yaw * vision.line_error + self.cfg.pid.kd_yaw * derivative)
        if vision.confidence < 0.2:
            side = 0.0
            yaw = 0.0

        return MotionCommand(
            forward=self.cfg.pid.forward_speed if vision.confidence >= 0.2 else 0.03,
            side=clamp(side, -self.cfg.pid.max_side, self.cfg.pid.max_side),
            yaw=clamp(yaw, -self.cfg.pid.max_yaw, self.cfg.pid.max_yaw),
            stand_height=self.cfg.stand_height,
        )
