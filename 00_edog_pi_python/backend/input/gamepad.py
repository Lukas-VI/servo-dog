from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
import time
from pathlib import Path
from typing import Dict, Optional

from ..config import GamepadConfig
from ..models import GamepadCommand, Mode, MotionCommand


@dataclass
class GamepadMapping:
    axis_forward: int = 1
    axis_side: int = 0
    axis_roll: int = 3
    axis_pitch: int = 4
    axis_left_trigger: int = 2
    axis_right_trigger: int = 5
    button_emergency_stop: int = 1
    button_manual: int = 4
    manual_button_required: bool = False
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
        manual_button_required=cfg.manual_button_required,
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
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
            import pygame

            pygame.init()
            pygame.display.init()
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
        try:
            self._pygame.event.pump()
        except Exception:
            self._available = False
            return GamepadCommand(connected=False)
        m = self.mapping
        raw_axes = tuple(round(float(self._joystick.get_axis(index)), 4) for index in range(self._joystick.get_numaxes()))
        pressed = {index for index in range(self._joystick.get_numbuttons()) if self._button(index)}
        hats = tuple(self._joystick.get_hat(index) for index in range(self._joystick.get_numhats()))
        rising = pressed - self._last_buttons
        self._last_buttons = pressed
        emergency = self._button(m.button_emergency_stop)
        manual_button = self._button(m.button_manual)
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
        motion_active = any(
            abs(value) > 0.001
            for value in (motion.forward, motion.side, motion.yaw, motion.roll, motion.pitch)
        ) or abs(height_delta) > 0.001
        manual = manual_button or (motion_active and not m.manual_button_required)
        return GamepadCommand(
            connected=True,
            source="usb",
            emergency_stop=emergency,
            manual_enabled=manual,
            motion=motion,
            selected_mode=selected_mode,
            selected_action=selected_action,
            raw_axes=raw_axes,
            pressed_buttons=tuple(sorted(pressed)),
            hats=hats,
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
        return max(0.0, min(1.0, value))


class WebGamepadReader:
    def __init__(self, command_path: str, timeout_s: float = 0.8) -> None:
        self.command_path = Path(command_path)
        self.timeout_s = timeout_s
        self._last_action_stamp = 0.0

    def poll(self) -> GamepadCommand:
        if not self.command_path.exists():
            return GamepadCommand(connected=False)
        try:
            data = json.loads(self.command_path.read_text(encoding="utf-8"))
        except Exception:
            return GamepadCommand(connected=False)

        updated_at = float(data.get("updated_at", 0.0) or 0.0)
        if updated_at and time.time() - updated_at > self.timeout_s:
            return GamepadCommand(connected=False)

        motion_data = data.get("motion") or {}
        selected_mode = data.get("selected_mode")
        selected_action = data.get("selected_action")
        mode = Mode(selected_mode) if selected_mode else None
        action = selected_action if selected_action and updated_at != self._last_action_stamp else None
        if action:
            self._last_action_stamp = updated_at
        return GamepadCommand(
            connected=True,
            source="web",
            emergency_stop=bool(data.get("emergency_stop", False)),
            manual_enabled=bool(data.get("manual_enabled", False)),
            selected_mode=mode,
            selected_action=action,
            motion=MotionCommand(
                forward=float(motion_data.get("forward", 0.0)),
                side=float(motion_data.get("side", 0.0)),
                yaw=float(motion_data.get("yaw", 0.0)),
                roll=float(motion_data.get("roll", 0.0)),
                pitch=float(motion_data.get("pitch", 0.0)),
                stand_height=int(motion_data.get("stand_height", 144)),
                gait=int(motion_data.get("gait", 2)),
            ),
        )


def make_gamepad_reader(cfg: GamepadConfig, initial_height: int = 144):
    if cfg.transport == "disabled":
        return None
    if cfg.transport == "web":
        return WebGamepadReader(cfg.web_command_path)
    return GamepadReader(mapping_from_config(cfg), initial_height)
