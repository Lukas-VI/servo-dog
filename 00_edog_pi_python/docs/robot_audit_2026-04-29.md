# Robot audit - 2026-04-29

## Network
- Wired SSH is reachable at `pi@192.168.12.1` with the PC on `192.168.12.167`.
- Original conflict: `eth0` and the `create_ap` default gateway both used `192.168.12.1/24`.
- Applied fix: keep `eth0` at `192.168.12.1/24`; start WiFi AP with `create_ap -g 192.168.13.1 wlan0 eth0 edog-ap ...`.
- Backup of edited network scripts: `/home/pi/edog_backups/network_20260429_105205`.
- Verified after change: `eth0` stayed up at `192.168.12.1/24`; `wlan0` stayed up at `192.168.13.1/24`; `create_ap` had a running `wlan0` instance.

## Active processes and ports
- `edog-brain` is running from `/home/pi/edog-brain/edog-brain-app/edog-brain`.
- `edog-brain` listens on TCP `192.168.12.1:30012` and UDP `7667`.
- `rc.local` starts SSH and `/home/pi/computer_start_shell/openWifiAp.sh`; old `open_edogBrain.sh` autostart is currently commented.

## Project layout on robot
- `/home/pi/edog-brain`: active C++ backend bridge and action/mp3 assets, about 53 MB.
- `/home/pi/edog-track5`: latest active C++ track app candidate, about 6.1 MB.
- `/home/pi/edog-track6`: older parallel track copy, about 6.0 MB.
- `/home/pi/edog`: nested older copies, about 21 MB.
- `/home/pi/opencv`: full OpenCV source/build tree, about 1.1 GB.
- `/home/pi/lcm-1.3.1`: LCM source/build tree, about 33 MB.
- `/home/pi/.local/share/Trash`: old deleted build artifacts, about 2.7 MB.

## Python runtime
- System Python is `3.7.3`.
- Present: `numpy 1.16.2`, `pyserial 3.4`, `pygame 1.9.4`.
- Missing from default path: `PyYAML`.
- OpenCV Python exists but is outside default `sys.path`:
  `/usr/local/lib/python3.7/site-packages/cv2/python-3.7`.
- Deployment scripts export `PYTHONPATH` so `cv2` can be imported without apt changes.
- Deployed release: `/home/pi/edog_pi_python/releases/20260429_110335`.
- Current symlink: `/home/pi/edog_pi_python/current`.
- Legacy backup before Python deployment: `/home/pi/edog_backups/legacy_before_python_20260429_105940.tar.gz`.
- Cleanup backup: `/home/pi/edog_backups/cleanup_20260429_110409`.

## Test results
- Remote compile/import check passed on the deployed release.
- Verified imports: `cv2 4.6.0-dev`, `numpy 1.16.2`, `pyserial 3.4`, `pygame 1.9.4.post1`.
- Protocol check passed: stop frame is `8F 00 01 0D 0E FF`.
- Synthetic vision test passed: a generated center line produced a `track` motion command and valid motion frame.
- Camera smoke test is not complete: `/dev/video14` and `/dev/video15` opened but timed out when reading frames; other `/dev/video*` nodes did not open.

## Competition history pain points
- Repeated manual cycle: `cd edog-track*/build`, `qmake`, `make clean`, `make`, then run `./edog_track purple showImage`.
- Manual network recovery required `sudo ifconfig eth0 192.168.12.1 ...` and `sudo ifconfig wlan0 down`.
- Multiple nearly identical project copies made it unclear which binary was the last trusted one.
- C++ edits appear to have been pasted into the shell history at least once, showing poor operator ergonomics during urgent debugging.
- Reboots and manual `kill`/restart of `edog-brain` were used as recovery steps instead of scripted service control.

## Cleanup decision
- Do not delete active legacy folders before the Python stack is proven on the course.
- Completed safe cleanup: moved `/home/pi/.local/share/Trash` into a dated backup and recreated an empty trash directory.
- Candidate junk list saved in the cleanup backup for later review: autosaves, temporary source image files, and stray editor artifacts under `edog-track5/edog-track6`.
- Large cleanup target after freeze: `/home/pi/opencv` source/build tree can be archived off-board if the installed `cv2` module is retained and validated.
