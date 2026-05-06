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

## Stable Wired And Wireless

- Wired debug: `eth0 = 192.168.12.1/24`.
- WiFi AP: `wlan0 = 192.168.13.1/24`.
- Do not run the old `sudo ifconfig wlan0 down` step unless intentionally disabling wireless.

The edited robot scripts are backed up at `/home/pi/edog_backups/network_20260429_105205`.

## Safe Stop

Use the gamepad emergency stop button or press `Ctrl+C`. The runtime sends the
legacy stop frame on exit when a backend is active.
