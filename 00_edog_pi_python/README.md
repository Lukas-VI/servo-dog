# edog_pi_python

Python rewrite for the e-Dog contest stack.

The old project is split into two C++ layers:

- `edog-track`: contest application logic, camera processing, color/task state.
- `edog-brain`: backend bridge from TCP/LCM into the drive board serial protocol.

This tree replaces both layers with a Python-first control stack for Raspberry Pi
Ubuntu. The default runtime is pure vision, direct serial output, and a dry-run
mode for safe testing before touching hardware.

## Layout

- `backend/`: camera vision, task state machine, gamepad input, control outputs.
- `frontend/`: lightweight local monitor and tuning surface.
- `scripts/`: safe read-only inventory tooling.
- `docs/`: protocol, deployment, vision, and system clean-up notes.
- `tests/`: local tests for protocol and control decisions.

## Quick Start

```bash
cd 00_edog_pi_python
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m backend.app --dry-run --mode stop
```

For hardware:

```bash
python -m backend.app --backend serial --serial-port /dev/serial0 --mode track
```

For video replay:

```bash
python -m backend.app --dry-run --video path/to/test.mp4 --mode track --debug-dir runs/debug
```

## Safety Defaults

- Startup defaults to `stop`.
- `--dry-run` never writes to serial or LCM.
- Hardware helper `run_serial.sh` keeps pygame gamepad support enabled.
- Gamepad priority is emergency stop, manual hold-to-drive, mode selection, then autonomous vision.
- Abnormal shutdown attempts to send stop when a real backend is active.
- The loop target is 14 Hz, matching the old receive-rate comment.

See `docs/operator_quickstart.md` for competition operation, systemd services,
browser tuning, and Xbox controller mapping. See
`docs/gamepad_value_ranges.md` for the explicit config value ranges.
