# Protocol Notes

## Existing Split

- `edog-track` publishes movement intent over LCM channel `edogControlLcm`.
- `edog-brain` receives LCM, translates commands to serial frames, and writes to `/dev/serial0`.
- `edog-brain` also has a TCP server on `192.168.12.1:30012` for upper-computer commands.

## Serial Settings

Observed in `edog-brain/serial.cpp`:

- Device: `/dev/serial0`
- Baud: `9600`
- Data bits: `8`
- Parity: none
- Stop bits: `1`

## Frame Format

Command frames start with `8F` and end with `FF`.

Checksum is the low byte of the sum from command byte through data bytes.

## Core Frames

- Stop: `8F 00 01 0D 0E FF`
- Motion simple: `8F 25 16 02 <forward:f32le> <side:f32le> <yaw:f32le> <height:u8> <roll:f32le> <pitch:f32le> <sum> FF`
- Action call: `8F 51 01 <action_id> <sum> FF`

Known action IDs:

- `00`: upstair
- `01`: downstair
- `02`: updais
- `0F`: lean
- `10`: lean_left
- `11`: lean_right
- `12`: leg_left
- `13`: leg_right

## Python Direction

The Python runtime can bypass old LCM and write serial directly. A future LCM
compatibility backend can be enabled if the old `edog-brain` bridge remains in
service and generated Python LCM bindings are copied from the robot image.

