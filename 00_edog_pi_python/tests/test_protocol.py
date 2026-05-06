from backend.models import MotionCommand
from backend.protocol import (
    ACTION_IDS,
    frame_hex,
    lcm_to_frame,
    pack_action,
    pack_motion,
    pack_named_action,
    pack_stop,
    EdogControlLcm,
)


def test_stop_frame_matches_legacy_backend():
    assert pack_stop() == bytes([0x8F, 0x00, 0x01, 0x0D, 0x0E, 0xFF])


def test_action_frame_checksum():
    frame = pack_named_action("updais")
    assert frame == bytes([0x8F, 0x51, 0x01, 0x02, 0x54, 0xFF])
    assert pack_action(ACTION_IDS["lean_left"]) == bytes([0x8F, 0x51, 0x01, 0x10, 0x62, 0xFF])


def test_motion_frame_shape_and_checksum():
    frame = pack_motion(MotionCommand(forward=0.2, side=0.0, yaw=0.0, roll=0.0, pitch=0.0, stand_height=130))
    assert len(frame) == 27
    assert frame[:4] == bytes([0x8F, 0x25, 0x16, 0x02])
    assert frame[16] == 130
    assert frame[-1] == 0xFF
    assert frame[-2] == (sum(frame[1:-2]) & 0xFF)


def test_lcm_compat_mapping():
    assert lcm_to_frame(EdogControlLcm(control_mode=1)) == pack_stop()
    assert lcm_to_frame(EdogControlLcm(control_mode=6)) == pack_named_action("updais")
    motion = lcm_to_frame(
        EdogControlLcm(control_mode=4, v_des=(0.1, 0.2, -0.3), rpy_des=(0.0, 0.1, 0.0), stand_height=144)
    )
    assert frame_hex(motion).startswith("8F 25 16 02")

