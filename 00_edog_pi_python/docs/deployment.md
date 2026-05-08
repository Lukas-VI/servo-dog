# Deployment Notes

## Raspberry Pi Setup

```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip python3-opencv
cd ~/00_edog_pi_python
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Dry Run

```bash
python -m backend.app --dry-run --mode stop --no-gamepad
```

## Hardware Run

```bash
python -m backend.app --backend serial --serial-port /dev/serial0 --mode track
```

## Push from Windows

From `D:\AAA6`:

```powershell
python .\00_edog_pi_python\scripts\deploy_to_pi.py --host 192.168.12.1 --user pi --password 123456
```

or:

```powershell
.\00_edog_pi_python\scripts\deploy_to_pi.ps1
```

The script uploads runtime files to `/home/pi/edog_pi_python/releases/<timestamp>`,
backs up the previous `/home/pi/edog_pi_python/current`, switches the `current`
symlink, exports the OpenCV Python path, and runs compile/import checks.

Latest tested deployment:

- `/home/pi/edog_pi_python/releases/20260429_110335`
- `/home/pi/edog_pi_python/current`
- dry-run helper: `/home/pi/edog_pi_python/current/run_dry.sh`
- serial helper: `/home/pi/edog_pi_python/current/run_serial.sh`

## Browser Debug Console

Run the browser tuning server on the Pi:

```bash
cd /home/pi/edog_pi_python/current
export PYTHONPATH="/usr/local/lib/python3.7/site-packages/cv2/python-3.7:/home/pi/opencv/release/lib/python3:${PYTHONPATH:-}"
python3 -m backend.debug_server --host 0.0.0.0 --port 8080 --camera-source 0
```

Then open `http://192.168.12.1:8080` from the wired PC. The page can pull
`/api/frame.jpg` repeatedly, preview HSV masks in the browser, edit PID steering
parameters, and save `config.yaml`.

The old Qt `socketServer` listened for UDP JPEG frames on `30015` to `30018`
and sent threshold bytes to robot port `8000`. The new path replaces that with
one HTTP service to reduce firewall, address, and multi-port debugging pain.

## Systemd Services

After deployment, install service files from Windows:

```powershell
python .\00_edog_pi_python\scripts\install_systemd_services.py --host 192.168.12.1 --user pi --password 123456
```

This enables `edog-debug.service` at boot so the browser console is available at
`http://192.168.12.1:8080`.

`edog-runner.service` is installed but disabled by default. Start it manually
after the robot is on the course:

```bash
sudo systemctl start edog-runner.service
sudo systemctl stop edog-runner.service
```

Enable serial control at boot only after bench testing:

```bash
sudo systemctl enable edog-runner.service
```

The hardware run path keeps pygame gamepad support enabled. Emergency stop and
manual override are evaluated before autonomous vision decisions.

## Stable Wired And Wireless

- Wired debug: `eth0 = 192.168.12.1/24`.
- WiFi AP: `wlan0 = 192.168.13.1/24`.
- Do not run the old `sudo ifconfig wlan0 down` step unless intentionally disabling wireless.

The edited robot scripts are backed up at `/home/pi/edog_backups/network_20260429_105205`.

## Safe Stop

Use the gamepad emergency stop button or press `Ctrl+C`. The runtime sends the
legacy stop frame on exit when a backend is active.
