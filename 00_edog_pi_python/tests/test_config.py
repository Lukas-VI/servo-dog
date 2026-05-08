from pathlib import Path

from backend.config import load_config


def test_load_config_fallback_reads_gamepad_without_yaml(tmp_path, monkeypatch):
    path = tmp_path / "config.yaml"
    path.write_text(
        """
stand_height: 144
gamepad:
  transport: web
  web_command_path: /tmp/edog_web_gamepad.json
  axis_forward: 1
  axis_side: 0
  axis_roll: 2
  axis_pitch: 3
  axis_left_trigger: 4
  axis_right_trigger: 5
  button_emergency_stop: 1
  button_manual: 4
  max_forward: 0.35
  max_side: 0.25
  max_roll: 0.25
  max_pitch: 0.25
  min_height: 100
  max_height: 180
  height_step: 1.8
  deadzone: 0.10
  gait: 2
  mode_buttons:
    0: track
    2: stop
  action_buttons:
    3: updais
branch:
  default_turn: straight
  fork_confidence: 0.18
  turn_bias: 0.28
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setattr("backend.config.yaml", None)

    cfg = load_config(str(Path(path)))

    assert cfg.gamepad.axis_roll == 2
    assert cfg.gamepad.transport == "web"
    assert cfg.gamepad.web_command_path == "/tmp/edog_web_gamepad.json"
    assert cfg.gamepad.axis_right_trigger == 5
    assert cfg.gamepad.mode_buttons == {"0": "track", "2": "stop"}
    assert cfg.gamepad.action_buttons == {"3": "updais"}
