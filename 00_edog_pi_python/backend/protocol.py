from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Tuple

from .models import MotionCommand


FRAME_HEAD = 0x8F
FRAME_TAIL = 0xFF
CMD_SIMPLE = 0x00
CMD_MOTION_SIMPLE = 0x25
CMD_ACTION = 0x51
GAIT_TROT = 0x02


ACTION_IDS = {
    "upstair": 0x00,
    "downstair": 0x01,
    "updais": 0x02,
    "lean": 0x0F,
    "lean_left": 0x10,
    "lean_right": 0x11,
    "leg_left": 0x12,
    "leg_right": 0x13,
}


CONTROL_MODE_TO_ACTION = {
    2: "upstair",
    3: "lean",
    5: "downstair",
    6: "updais",
    7: "lean_left",
    8: "lean_right",
    9: "leg_left",
    10: "leg_right",
}


@dataclass(frozen=True)
class EdogControlLcm:
    receive_flag: int = 0
    control_mode: int = 1
    v_des: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rpy_des: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    stand_height: float = 144.0


def checksum(payload: bytes) -> int:
    return sum(payload) & 0xFF


def pack_simple(data_byte: int) -> bytes:
    payload = bytes([CMD_SIMPLE, 0x01, data_byte & 0xFF])
    return bytes([FRAME_HEAD]) + payload + bytes([checksum(payload), FRAME_TAIL])


def pack_stop() -> bytes:
    return pack_simple(0x0D)


def pack_action(action_id: int) -> bytes:
    payload = bytes([CMD_ACTION, 0x01, action_id & 0xFF])
    return bytes([FRAME_HEAD]) + payload + bytes([checksum(payload), FRAME_TAIL])


def pack_named_action(name: str) -> bytes:
    if name not in ACTION_IDS:
        raise KeyError(f"unknown action: {name}")
    return pack_action(ACTION_IDS[name])


def pack_motion(command: MotionCommand, gait: int = GAIT_TROT) -> bytes:
    stand_height = int(command.stand_height) & 0xFF
    data = bytearray()
    data.extend([CMD_MOTION_SIMPLE, 0x16, gait & 0xFF])
    data.extend(struct.pack("<f", float(command.forward)))
    data.extend(struct.pack("<f", float(command.side)))
    data.extend(struct.pack("<f", float(command.yaw)))
    data.append(stand_height)
    # Mirror edog-brain translate(): roll bytes first, then pitch bytes.
    data.extend(struct.pack("<f", float(command.roll)))
    data.extend(struct.pack("<f", float(command.pitch)))
    return bytes([FRAME_HEAD]) + bytes(data) + bytes([checksum(data), FRAME_TAIL])


def lcm_to_frame(msg: EdogControlLcm) -> bytes:
    if msg.control_mode == 1:
        return pack_stop()
    if msg.control_mode == 4:
        return pack_motion(
            MotionCommand(
                forward=msg.v_des[0],
                side=msg.v_des[1],
                yaw=msg.v_des[2],
                roll=msg.rpy_des[0],
                pitch=msg.rpy_des[1],
                stand_height=int(msg.stand_height),
            )
        )
    action = CONTROL_MODE_TO_ACTION.get(msg.control_mode)
    if action:
        return pack_named_action(action)
    return pack_stop()


def frame_hex(frame: bytes) -> str:
    return " ".join(f"{byte:02X}" for byte in frame)
