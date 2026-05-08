import json
import time

from backend.input.gamepad import WebGamepadReader
from backend.models import Mode


def test_web_gamepad_reads_command_file(tmp_path):
    command_path = tmp_path / "gamepad.json"
    command_path.write_text(
        json.dumps(
            {
                "updated_at": time.time(),
                "manual_enabled": True,
                "selected_mode": "track",
                "motion": {"forward": 0.2, "side": -0.1, "roll": 0.05, "pitch": -0.04, "stand_height": 150, "gait": 2},
            }
        ),
        encoding="utf-8",
    )

    command = WebGamepadReader(str(command_path)).poll()

    assert command.connected
    assert command.manual_enabled
    assert command.selected_mode == Mode.TRACK
    assert command.motion.forward == 0.2
    assert command.motion.stand_height == 150


def test_web_gamepad_times_out_stale_command(tmp_path):
    command_path = tmp_path / "gamepad.json"
    command_path.write_text(json.dumps({"updated_at": time.time() - 5}), encoding="utf-8")

    assert not WebGamepadReader(str(command_path), timeout_s=0.1).poll().connected
