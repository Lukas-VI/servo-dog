from backend.config import RuntimeConfig
from backend.models import Mode, VisionResult
from backend.state import EdogStateMachine


def test_stop_mode_requests_stop():
    sm = EdogStateMachine(RuntimeConfig(), Mode.STOP)
    decision = sm.decide(VisionResult(confidence=1.0))
    assert decision.action == "stop"


def test_track_generates_motion_from_line_error():
    sm = EdogStateMachine(RuntimeConfig(), Mode.TRACK)
    decision = sm.decide(VisionResult(line_error=0.5, confidence=0.9, detected_colors={}))
    assert decision.motion is not None
    assert decision.motion.forward > 0
    assert decision.motion.yaw < 0


def test_color_triggers_action():
    sm = EdogStateMachine(RuntimeConfig(), Mode.TRACK)
    decision = sm.decide(VisionResult(confidence=0.7, detected_colors={"blue": 0.3}))
    assert decision.action == "updais"
    assert decision.mode == Mode.UP_DAIS

