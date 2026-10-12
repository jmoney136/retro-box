"""Minimal Linux joystick support using the kernel's /dev/input/js* API."""

from __future__ import annotations

import glob
import os
import struct
import time
from pathlib import Path


_JS_EVENT = struct.Struct("@IhBB")
_JS_EVENT_BUTTON = 0x01
_JS_EVENT_AXIS = 0x02
_DEADZONE = 16_000


def decode_joystick_event(packet: bytes) -> tuple[int, int, int] | None:
    """Decode a Linux joystick event as (type, number, value)."""
    if len(packet) != _JS_EVENT.size:
        return None

    _timestamp, value, event_type, number = _JS_EVENT.unpack(packet)
    return event_type & 0x7F, number, value


class GamepadMapper:
    """Translate standard joystick axes/buttons into launcher actions."""

    def __init__(self, deadzone: int = _DEADZONE) -> None:
        self.deadzone = deadzone
        self._directions: dict[int, int] = {}

    def reset(self) -> None:
        self._directions.clear()

    def map_event(self, event: tuple[int, int, int]) -> str | None:
        """Map an event to up/down/left/right/select, if it triggers an action."""
        event_type, number, value = event
        if event_type == _JS_EVENT_BUTTON:
            return "select" if number == 0 and value == 1 else None

        if event_type != _JS_EVENT_AXIS or number not in (0, 1, 6, 7):
            return None

        direction = -1 if value < -self.deadzone else 1 if value > self.deadzone else 0
        previous = self._directions.get(number, 0)
        self._directions[number] = direction
        if not direction or direction == previous:
            return None

        if number in (1, 7):
            return "up" if direction < 0 else "down"
        return "left" if direction < 0 else "right"


class LinuxGamepad:
    """Poll the first connected Linux joystick without blocking the Tk event loop."""

    def __init__(self) -> None:
        self._fd: int | None = None
        self.device_path: Path | None = None
        self._buffer = bytearray()
        self._mapper = GamepadMapper()
        self._retry_at = 0.0

    @property
    def connected(self) -> bool:
        return self._fd is not None

    def _connect(self) -> None:
        self._retry_at = time.monotonic() + 1.0
        flags = os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0)
        for device in sorted(glob.glob("/dev/input/js*")):
            try:
                self._fd = os.open(device, flags)
            except OSError:
                continue
            self.device_path = Path(device)
            self._buffer.clear()
            self._mapper.reset()
            return

    def _disconnect(self) -> None:
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
        self._fd = None
        self.device_path = None
        self._buffer.clear()
        self._mapper.reset()

    def poll(self) -> list[str]:
        """Return controller actions currently waiting, without waiting for input."""
        if self._fd is None:
            if time.monotonic() >= self._retry_at:
                self._connect()
            if self._fd is None:
                return []

        actions: list[str] = []
        try:
            while True:
                try:
                    chunk = os.read(self._fd, _JS_EVENT.size * 32)
                except BlockingIOError:
                    break
                if not chunk:
                    self._disconnect()
                    break
                self._buffer.extend(chunk)
                while len(self._buffer) >= _JS_EVENT.size:
                    packet = bytes(self._buffer[: _JS_EVENT.size])
                    del self._buffer[: _JS_EVENT.size]
                    event = decode_joystick_event(packet)
                    if event is not None:
                        action = self._mapper.map_event(event)
                        if action is not None:
                            actions.append(action)
        except OSError:
            self._disconnect()

        return actions

    def close(self) -> None:
        """Close the controller device, if connected."""
        self._disconnect()
