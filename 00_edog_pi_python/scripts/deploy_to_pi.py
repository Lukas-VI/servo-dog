from __future__ import annotations

import argparse
import io
import os
import posixpath
import tarfile
import time
from pathlib import Path
from typing import Iterable

import paramiko


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INCLUDE = [
    "backend",
    "frontend",
    "docs",
    "scripts",
    "tests",
    "config.yaml",
    "pytest.ini",
    "requirements.txt",
    "README.md",
]
EXCLUDE_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", "tmp"}


def iter_files() -> Iterable[Path]:
    for item in INCLUDE:
        path = PROJECT_ROOT / item
        if path.is_file():
            yield path
        elif path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() and not EXCLUDE_PARTS.intersection(child.parts):
                    yield child


def build_archive() -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for path in iter_files():
            tar.add(path, arcname=path.relative_to(PROJECT_ROOT).as_posix())
    return buffer.getvalue()


def run(client: paramiko.SSHClient, command: str, password: str, timeout: int = 120) -> str:
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    if "sudo" in command:
        stdin.write(password + "\n")
        stdin.flush()
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    status = stdout.channel.recv_exit_status()
    if status != 0:
        raise RuntimeError(f"remote command failed ({status}):\n{command}\n{out}\n{err}")
    return out + err


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy pure-vision eDog runtime to Raspberry Pi")
    parser.add_argument("--host", default="192.168.12.1")
    parser.add_argument("--user", default="pi")
    parser.add_argument("--password", default=os.environ.get("EDOG_PI_PASSWORD", "123456"))
    parser.add_argument("--remote-root", default="/home/pi/edog_pi_python")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()

    stamp = time.strftime("%Y%m%d_%H%M%S")
    upload_path = f"/tmp/edog_pi_python_{stamp}.tar.gz"
    release_dir = posixpath.join(args.remote_root, "releases", stamp)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        args.host,
        username=args.user,
        password=args.password,
        timeout=10,
        banner_timeout=10,
        auth_timeout=10,
        look_for_keys=False,
        allow_agent=False,
    )

    sftp = client.open_sftp()
    with sftp.file(upload_path, "wb") as remote:
        remote.write(build_archive())
    sftp.close()

    setup = f"""
set -eu
mkdir -p {args.remote_root}/releases {args.remote_root}/backups
if [ -L {args.remote_root}/current ] || [ -d {args.remote_root}/current ]; then
  tar -C {args.remote_root} -czf {args.remote_root}/backups/current_{stamp}.tar.gz current
fi
mkdir -p {release_dir}
tar -xzf {upload_path} -C {release_dir}
rm -f {upload_path}
ln -sfn {release_dir} {args.remote_root}/current
cat > {args.remote_root}/current/run_dry.sh <<'EOF'
#!/bin/sh
set -eu
cd /home/pi/edog_pi_python/current
export PYTHONPATH="/usr/local/lib/python3.7/site-packages/cv2/python-3.7:/home/pi/opencv/release/lib/python3:${{PYTHONPATH:-}}"
python3 -m backend.app --dry-run --no-gamepad "$@"
EOF
cat > {args.remote_root}/current/run_serial.sh <<'EOF'
#!/bin/sh
set -eu
cd /home/pi/edog_pi_python/current
export PYTHONPATH="/usr/local/lib/python3.7/site-packages/cv2/python-3.7:/home/pi/opencv/release/lib/python3:${{PYTHONPATH:-}}"
python3 -m backend.app --backend serial --no-gamepad "$@"
EOF
chmod +x {args.remote_root}/current/run_dry.sh {args.remote_root}/current/run_serial.sh
"""
    print(run(client, setup, args.password))

    if not args.skip_tests:
        test = f"""
set -eu
cd {args.remote_root}/current
export PYTHONPATH="/usr/local/lib/python3.7/site-packages/cv2/python-3.7:/home/pi/opencv/release/lib/python3:${{PYTHONPATH:-}}"
python3 -m compileall backend scripts
python3 - <<'PY'
import cv2
import numpy
import serial
import pygame
from backend.protocol import frame_hex, pack_stop
print("cv2", cv2.__version__)
print("numpy", numpy.__version__)
print("serial", serial.VERSION)
print("pygame", pygame.version.ver)
print("stop_frame", frame_hex(pack_stop()))
PY
"""
        print(run(client, test, args.password))

    client.close()
    print(f"deployed {release_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
