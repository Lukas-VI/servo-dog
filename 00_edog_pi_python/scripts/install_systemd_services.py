from __future__ import annotations

import argparse
import os

import paramiko


DEBUG_SERVICE = """[Unit]
Description=e-Dog Vision Studio debug web console
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/edog_pi_python/current
ExecStart=/home/pi/edog_pi_python/current/run_debug_server.sh
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
"""


RUNNER_SERVICE = """[Unit]
Description=e-Dog Python serial control runtime
After=network-online.target edog-debug.service
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/edog_pi_python/current
ExecStart=/home/pi/edog_pi_python/current/run_control_only.sh --mode stop
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
"""


def run(client: paramiko.SSHClient, command: str, password: str, timeout: int = 120) -> str:
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    stdin.write(password + "\n")
    stdin.flush()
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    status = stdout.channel.recv_exit_status()
    if status != 0:
        raise RuntimeError(f"remote command failed ({status}):\n{command}\n{out}\n{err}")
    return out + err


def main() -> int:
    parser = argparse.ArgumentParser(description="Install e-Dog systemd services on Raspberry Pi")
    parser.add_argument("--host", default="192.168.12.1")
    parser.add_argument("--user", default="pi")
    parser.add_argument("--password", default=os.environ.get("EDOG_PI_PASSWORD", "123456"))
    parser.add_argument("--enable-runner", action="store_true", help="also enable serial runtime at boot")
    args = parser.parse_args()

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

    command = f"""set -eu
cat > /tmp/edog-debug.service <<'EOF'
{DEBUG_SERVICE}EOF
cat > /tmp/edog-runner.service <<'EOF'
{RUNNER_SERVICE}EOF
sudo -S mv /tmp/edog-debug.service /etc/systemd/system/edog-debug.service
sudo -S mv /tmp/edog-runner.service /etc/systemd/system/edog-runner.service
sudo -S systemctl daemon-reload
sudo -S systemctl enable edog-debug.service
sudo -S systemctl restart edog-debug.service
sudo -S systemctl disable edog-runner.service >/dev/null 2>&1 || true
{"sudo -S systemctl enable edog-runner.service" if args.enable_runner else "true"}
sudo -S systemctl --no-pager --full status edog-debug.service | sed -n '1,12p'
sudo -S systemctl is-enabled edog-debug.service
sudo -S systemctl is-enabled edog-runner.service || true
"""
    print(run(client, command, args.password))
    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
