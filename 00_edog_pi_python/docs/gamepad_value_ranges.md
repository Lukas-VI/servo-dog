# Gamepad Configuration Value Ranges

All gamepad fields live under `gamepad:` in `config.yaml`.

## Axis And Button Fields

- `axis_forward`, `axis_side`, `axis_roll`, `axis_pitch`, `axis_left_trigger`,
  `axis_right_trigger`: integer axis index, `0..15`.
- `button_emergency_stop`, `button_manual`: integer button index, `0..31`.
- `mode_buttons`: map of button index `0..31` to mode name.
- `action_buttons`: map of button index `0..31` to action name.

Pygame joystick axes are normalized to `-1.0..1.0`. Deadzone removes small
absolute values around zero. Triggers are treated as `0.0..1.0` after
normalization so the left trigger lowers height and the right trigger raises it.

## Motion Fields

- `max_forward`: `0.0..0.8`, applied to left stick forward/back.
- `max_side`: `0.0..0.8`, applied to left stick left/right.
- `max_roll`: `0.0..0.8`, applied to right stick left/right.
- `max_pitch`: `0.0..0.8`, applied to right stick forward/back.
- `deadzone`: `0.0..0.35`.

Manual stick output maps to the serial motion frame:

- left stick vertical -> `forward`;
- left stick horizontal -> `side`;
- right stick horizontal -> `roll`;
- right stick vertical -> `pitch`;
- triggers -> `stand_height`.

`yaw` remains controlled by the autonomous line tracker unless a later manual
mapping explicitly assigns an axis to yaw.

## Height And Gait

- `min_height`: integer, `60..180`.
- `max_height`: integer, `100..220`.
- `height_step`: `0.2..8.0`, height units per control loop at full trigger.
- `gait`: integer, `0..15`; default `2`, matching the legacy trot gait byte.

## Allowed Mode Values

- `stop`
- `track`
- `byroad_a`
- `byroad_b`
- `lean_left`
- `lean_right`
- `updais`
- `manual`

## Allowed Action Values

- `upstair`
- `downstair`
- `updais`
- `lean`
- `lean_left`
- `lean_right`
- `leg_left`
- `leg_right`

## Priority Contract

Runtime priority is fixed:

1. Emergency stop.
2. Manual hold-to-drive.
3. One-shot action button.
4. Mode button.
5. Autonomous vision state machine.

Mode and action buttons fire on rising edge, so holding an action button does
not resend the action every control frame.
