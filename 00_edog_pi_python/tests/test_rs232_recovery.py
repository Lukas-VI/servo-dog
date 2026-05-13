from scripts.rs232_recovery import make_neutral_motion, parse_hex_frame


def test_parse_hex_frame_accepts_spaces_commas_and_prefixes():
    assert parse_hex_frame("8F, 00, 0x01 0D 0E FF") == bytes([0x8F, 0x00, 0x01, 0x0D, 0x0E, 0xFF])


def test_neutral_motion_frame_shape():
    frame = make_neutral_motion(144)
    assert frame[:4] == bytes([0x8F, 0x25, 0x16, 0x02])
    assert frame[-1] == 0xFF
    assert len(frame) == 27
