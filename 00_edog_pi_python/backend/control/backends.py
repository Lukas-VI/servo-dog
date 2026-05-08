from __future__ import annotations

import time
from pathlib import Path
from typing import List

try:
    from typing import Protocol
except ImportError:  # Python 3.7 on the robot image does not provide typing.Protocol.
    class Protocol:  # type: ignore
        pass

from ..models import MotionCommand
from ..protocol import frame_hex, pack_motion, pack_named_action, pack_stop


class ControlBackend(Protocol):
    name: str

    def send_motion(self, command: MotionCommand) -> None:
        ...

    def send_action(self, name: str) -> None:
        ...

    def stop(self) -> None:
        ...

    def close(self) -> None:
        ...


class DryRunBackend:
    name = "dry-run"

    def __init__(self) -> None:
        self.frames: List[bytes] = []
        self.last_frame_hex = ""
        self.last_error = ""
        self.write_count = 0

    def _record(self, frame: bytes) -> None:
        self.frames.append(frame)
        self.last_frame_hex = frame_hex(frame)
        self.write_count += 1
        print(f"[dry-run] {self.last_frame_hex}")

    def send_motion(self, command: MotionCommand) -> None:
        self._record(pack_motion(command))

    def send_action(self, name: str) -> None:
        self._record(pack_named_action(name))

    def stop(self) -> None:
        self._record(pack_stop())

    def close(self) -> None:
        pass


class SerialBackend:
    name = "serial"

    def __init__(self, port: str = "/dev/serial0", baud: int = 9600) -> None:
        import serial

        self.serial = serial.Serial(
            port=port,
            baudrate=baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0,
            write_timeout=0.2,
        )
        self.last_frame_hex = ""
        self.last_error = ""
        self.write_count = 0

    def _write(self, frame: bytes) -> None:
        try:
            self.serial.write(frame)
            self.serial.flush()
            self.last_frame_hex = frame_hex(frame)
            self.last_error = ""
            self.write_count += 1
        except Exception as exc:
            self.last_error = repr(exc)
            raise

    def send_motion(self, command: MotionCommand) -> None:
        self._write(pack_motion(command))

    def send_action(self, name: str) -> None:
        self._write(pack_named_action(name))

    def stop(self) -> None:
        self._write(pack_stop())

    def close(self) -> None:
        self.serial.close()


class LcmCompatBackend:
    """Optional LCM publisher backend.

    The direct serial backend is preferred because it replaces edog-brain.
    This backend keeps compatibility when an existing edog-brain bridge is
    already running and should remain responsible for serial output.
    """

    name = "lcm"

    def __init__(self) -> None:
        try:
            import lcm  # type: ignore
        except ImportError as exc:
            raise RuntimeError("python-lcm is not installed") from exc
        self._lcm = lcm.LCM()

    def send_motion(self, command: MotionCommand) -> None:
        raise NotImplementedError(
            "LCM publishing needs generated edog_control_lcm.py from the robot image"
        )

    def send_action(self, name: str) -> None:
        raise NotImplementedError(
            "LCM publishing needs generated edog_control_lcm.py from the robot image"
        )

    def stop(self) -> None:
        raise NotImplementedError(
            "LCM publishing needs generated edog_control_lcm.py from the robot image"
        )

    def close(self) -> None:
        pass


class FileLogBackend(DryRunBackend):
    name = "file-log"

    def __init__(self, path: str | Path) -> None:
        super().__init__()
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _record(self, frame: bytes) -> None:
        super()._record(frame)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(f"{time.time():.3f} {frame_hex(frame)}\n")


def make_backend(kind: str, serial_port: str, serial_baud: int) -> ControlBackend:
    if kind == "dry-run":
        return DryRunBackend()
    if kind == "serial":
        return SerialBackend(serial_port, serial_baud)
    if kind == "lcm":
        return LcmCompatBackend()
    if kind.startswith("file:"):
        return FileLogBackend(kind.split(":", 1)[1])
    raise ValueError(f"unknown backend: {kind}")
