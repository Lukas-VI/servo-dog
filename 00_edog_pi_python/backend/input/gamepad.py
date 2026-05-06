from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..models import GamepadCommand, Mode, MotionCommand


@dataclass
class GamepadMapping:
    axis_forward: int = 1
    axis_side: int = 0
    axis_yaw: int = 2
    button_emergency_stop: int = 1
    button_manual: int = 4
    button_track: int = 0
    button_stop: int = 2
    max_forward: float = 0.35
    max_side: float = 0.25
    max_yaw: float = 1.2
    deadzone: float = 0.10


class GamepadReader:
    def __init__(self, mapping: Optional[GamepadMapping] = None) -> None:
        self.mapping = mapping or GamepadMapping()
        self._pygame = None
        self._joystick = None
        self._available = False
        try:
            import pygame

            pygame.init()
            pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                self._joystick = pygame.joystick.Joystick(0)
                self._joystick.init()
                self._available = True
            self._pygame = pygame
        except Exception:
            self._available = False

    def poll(self) -> GamepadCommand:
        if not self._available or self._pygame is None or self._joystick is None:
            return GamepadCommand(connected=False)
        self._pygame.event.pump()
        m = self.mapping
        emergency = self._button(m.button_emergency_stop)
        manual = self._button(m.button_manual)
        selected_mode = None
        if self._button(m.button_track):
            selected_mode = Mode.TRACK
        elif self._button(m.button_stop):
            selected_mode = Mode.STOP

        motion = MotionCommand(
            forward=-self._axis(m.axis_forward) * m.max_forward,
            side=self._axis(m.axis_side) * m.max_side,
            yaw=self._axis(m.axis_yaw) * m.max_yaw,
        )
        return GamepadCommand(
            connected=True,
            emergency_stop=emergency,
            manual_enabled=manual,
            motion=motion,
            selected_mode=selected_mode,
        )

    def _axis(self, index: int) -> float:
        value = float(self._joystick.get_axis(index))
        return 0.0 if abs(value) < self.mapping.deadzone else value

    def _button(self, index: int) -> bool:
        return bool(self._joystick.get_button(index))
