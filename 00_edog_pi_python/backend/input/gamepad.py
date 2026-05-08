from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from ..config import GamepadConfig
from ..models import GamepadCommand, Mode, MotionCommand


@dataclass
class GamepadMapping:
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


def mapping_from_config(cfg: Optional[GamepadConfig]) -> GamepadMapping:
    if cfg is None:
        return GamepadMapping()
    return GamepadMapping(
        axis_forward=cfg.axis_forward,
        axis_side=cfg.axis_side,
        axis_roll=cfg.axis_roll,
        axis_pitch=cfg.axis_pitch,
        axis_left_trigger=cfg.axis_left_trigger,
        axis_right_trigger=cfg.axis_right_trigger,
        button_emergency_stop=cfg.button_emergency_stop,
        button_manual=cfg.button_manual,
        max_forward=cfg.max_forward,
        max_side=cfg.max_side,
        max_roll=cfg.max_roll,
        max_pitch=cfg.max_pitch,
        min_height=cfg.min_height,
        max_height=cfg.max_height,
        height_step=cfg.height_step,
        deadzone=cfg.deadzone,
        gait=cfg.gait,
        mode_buttons=dict(cfg.mode_buttons),
        action_buttons=dict(cfg.action_buttons),
    )


class GamepadReader:
    def __init__(self, mapping: Optional[GamepadMapping] = None, initial_height: int = 144) -> None:
        self.mapping = mapping or GamepadMapping()
        self._stand_height = int(max(self.mapping.min_height, min(self.mapping.max_height, initial_height)))
        self._last_buttons = set()
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
        pressed = {index for index in range(self._joystick.get_numbuttons()) if self._button(index)}
        rising = pressed - self._last_buttons
        self._last_buttons = pressed
        emergency = self._button(m.button_emergency_stop)
        manual = self._button(m.button_manual)
        selected_mode = None
        for button, mode in m.mode_buttons.items():
            if int(button) in rising:
                selected_mode = Mode(mode)
                break
        selected_action = None
        for button, action in m.action_buttons.items():
            if int(button) in rising:
                selected_action = action
                break

        height_delta = self._trigger(m.axis_right_trigger) - self._trigger(m.axis_left_trigger)
        self._stand_height = int(max(m.min_height, min(m.max_height, self._stand_height + height_delta * m.height_step)))

        motion = MotionCommand(
            forward=-self._axis(m.axis_forward) * m.max_forward,
            side=self._axis(m.axis_side) * m.max_side,
            roll=self._axis(m.axis_roll) * m.max_roll,
            pitch=-self._axis(m.axis_pitch) * m.max_pitch,
            stand_height=self._stand_height,
            gait=m.gait,
        )
        return GamepadCommand(
            connected=True,
            emergency_stop=emergency,
            manual_enabled=manual,
            motion=motion,
            selected_mode=selected_mode,
            selected_action=selected_action,
        )

    def _axis(self, index: int) -> float:
        value = float(self._joystick.get_axis(index))
        return 0.0 if abs(value) < self.mapping.deadzone else value

    def _button(self, index: int) -> bool:
        return bool(self._joystick.get_button(index))

    def _trigger(self, index: int) -> float:
        value = self._axis(index)
        if value < -0.5:
            return 0.0
        return max(0.0, min(1.0, (value + 1.0) * 0.5))
