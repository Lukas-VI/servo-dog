# Operator Quickstart

## Connection

1. Connect the PC to the Raspberry Pi with Ethernet.
2. The robot wired address is `192.168.12.1`.
3. SSH login:

```bash
ssh pi@192.168.12.1
```

Password: `123456`.

The browser console is:

```text
http://192.168.12.1:8080
```

## Deployment From Windows

From `D:\AAA6`:

```powershell
.\00_edog_pi_python\scripts\deploy_to_pi.ps1
```

This uploads a timestamped release to:

```text
/home/pi/edog_pi_python/releases/<timestamp>
```

and switches:

```text
/home/pi/edog_pi_python/current
```

## Boot Services

Install or refresh systemd service files after deployment:

```powershell
python .\00_edog_pi_python\scripts\install_systemd_services.py --host 192.168.12.1 --user pi --password 123456
```

This enables only the debug web service at boot:

```bash
sudo systemctl status edog-debug.service
sudo systemctl restart edog-debug.service
```

The serial control runtime is installed but disabled by default for safety:

```bash
sudo systemctl status edog-runner.service
sudo systemctl start edog-runner.service
sudo systemctl stop edog-runner.service
```

Only enable robot control at boot after bench testing:

```bash
sudo systemctl enable edog-runner.service
```

## Manual Run Commands

Dry run, no serial output:

```bash
cd /home/pi/edog_pi_python/current
./run_dry.sh --mode track
```

Hardware serial run:

```bash
cd /home/pi/edog_pi_python/current
./run_serial.sh --mode stop
```

Start autonomous line tracking after checks:

```bash
./run_serial.sh --mode track
```

The serial runtime writes directly to `/dev/serial0` at `9600 8N1`.

## Gamepad Priority

Use the Xbox controller through its USB 2.4G receiver. The receiver must be
plugged into the Raspberry Pi before starting `edog-runner.service` or
`run_serial.sh`.

Priority order is:

1. Emergency stop button.
2. Manual hold-to-drive.
3. Mode buttons.
4. Autonomous vision state machine.

Default Xbox-style mapping through pygame:

- `B`: emergency stop, forces `STOP` and sends the stop frame.
- `LB`: hold manual override.
- Left stick vertical: forward/back.
- Left stick horizontal: side move.
- Right stick horizontal: roll.
- Right stick vertical: pitch.
- Left trigger: lower stand height.
- Right trigger: raise stand height.
- `A`: switch to `track`.
- `X`: switch to `stop`.

Button-to-mode and button-to-action mappings are editable in the Web console
under the gamepad panel and saved to `config.yaml`. Exact value ranges are in
`docs/gamepad_value_ranges.md`.

If button numbers differ on a receiver, run this quick pygame probe and adjust
`backend/input/gamepad.py`:

```bash
python3 - <<'PY'
import pygame, time
pygame.init()
pygame.joystick.init()
j = pygame.joystick.Joystick(0)
j.init()
while True:
    pygame.event.pump()
    buttons = [i for i in range(j.get_numbuttons()) if j.get_button(i)]
    axes = [round(j.get_axis(i), 2) for i in range(j.get_numaxes())]
    print("buttons", buttons, "axes", axes)
    time.sleep(0.2)
PY
```

## Browser Debugging

Open:

```text
http://192.168.12.1:8080
```

Use it to:

- start live camera preview;
- adjust HSV thresholds;
- adjust PID steering;
- adjust fork parameters under the SLAM panel;
- edit the task graph;
- save `config.yaml` on the active release.

Saving the browser config updates:

```text
/home/pi/edog_pi_python/current/config.yaml
```

Restart `edog-runner.service` after changing runtime parameters.

## Task Start Flow

Recommended competition flow:

1. Power on robot.
2. Confirm Xbox receiver is plugged in.
3. Open `http://192.168.12.1:8080`.
4. Check live camera and thresholds.
5. Start serial runtime:

```bash
sudo systemctl start edog-runner.service
```

6. Keep mode at `stop` until the robot is placed.
7. Press `A` on the controller to enter `track`, or start directly:

```bash
cd /home/pi/edog_pi_python/current
./run_serial.sh --mode track
```

8. Press `B` at any time for emergency stop.
