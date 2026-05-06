from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

import paramiko


COMMANDS = [
    ("identity", "echo USER=$(whoami); id; hostname; uname -a; cat /etc/os-release 2>/dev/null || true"),
    ("network", "ip addr show 2>/dev/null || ifconfig -a; echo ---ROUTE---; ip route 2>/dev/null || route -n"),
    ("disk", "df -h; echo ---HOME---; du -sh /home/pi/* 2>/dev/null | sort -h"),
    (
        "processes",
        "ps -eo pid,ppid,user,stat,comm,args --width 240 | "
        "egrep -i 'edog|brain|track|socket|lcm|serial|python|qt|ffplay|hostapd|dnsmasq|dhcp|wpa|opencv|ros' "
        "| grep -v egrep || true",
    ),
    (
        "ports",
        "(ss -lntup 2>/dev/null || netstat -lntup 2>/dev/null || true) | "
        "egrep '(:22|:30012|:30014|:30015|:30016|:30017|:30018|:8000|:8080|:5000|:8888|:11311)' || true",
    ),
    (
        "services",
        "(systemctl list-units --type=service --state=running --no-pager 2>/dev/null || "
        "service --status-all 2>/dev/null || true) | "
        "egrep -i 'edog|brain|track|socket|lcm|hostapd|dnsmasq|dhcp|wifi|network|serial|python|ros' || true",
    ),
    (
        "projects",
        "find /home/pi -maxdepth 5 \\( -iname '*edog*' -o -iname '*brain*' -o -iname '*track*' "
        "-o -iname '*socket*' -o -iname '*computer*' -o -iname '*start*' -o -iname '*colorGroup*' \\) "
        "-print 2>/dev/null | sort | head -400",
    ),
    (
        "startup",
        "echo ---CRONTAB---; crontab -l 2>/dev/null || true; "
        "echo ---RCLOCAL---; sed -n '1,220p' /etc/rc.local 2>/dev/null || true; "
        "echo ---COMPUTER_START---; find /home/pi/computer_start_shell -maxdepth 2 -type f "
        "-print -exec sed -n '1,140p' {} \\; 2>/dev/null | head -600",
    ),
    (
        "packages",
        "dpkg-query -W -f='${Package}\\t${Version}\\n' 2>/dev/null | "
        "egrep -i '(^lcm|opencv|qt|python|pygame|serial|ros-|gstreamer|ffmpeg|hostapd|dnsmasq|dhcpcd|v4l|picamera)' "
        "| head -320 || true",
    ),
]


def connect(host: str, users: List[str], password: str) -> Tuple[paramiko.SSHClient, str]:
    for user in users:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                host,
                username=user,
                password=password,
                timeout=8,
                banner_timeout=8,
                auth_timeout=8,
                look_for_keys=False,
                allow_agent=False,
            )
            return client, user
        except Exception as exc:
            print(f"CONNECT_FAIL {user}: {type(exc).__name__}: {exc}")
    raise RuntimeError("unable to connect")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only e-Dog Raspberry Pi inventory")
    parser.add_argument("--host", default="192.168.12.1")
    parser.add_argument("--users", default="pi,root")
    parser.add_argument("--password", default="123456")
    parser.add_argument("--out", default="docs/remote_inventory_latest.txt")
    args = parser.parse_args()

    client, user = connect(args.host, [u.strip() for u in args.users.split(",") if u.strip()], args.password)
    lines = [f"CONNECTED_AS {user}@{args.host}\n"]
    try:
        for name, cmd in COMMANDS:
            lines.append(f"\n===== {name} =====\n")
            stdin, stdout, stderr = client.exec_command(cmd, timeout=25)
            lines.append(stdout.read().decode("utf-8", "replace"))
            err = stderr.read().decode("utf-8", "replace").strip()
            if err:
                lines.append(f"\n---ERR---\n{err}\n")
    finally:
        client.close()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(lines), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
