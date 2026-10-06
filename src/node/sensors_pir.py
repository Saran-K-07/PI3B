"""PIR motion sensor HAL (PIR SE module).

Wiring: VCC 5V, GND, OUT -> GPIO17 (Pin 11).
OUT is 3.3V digital HIGH = motion. 30-60s warmup after power-on.

Mock mode (PIR_MOCK=1 or mock=True) runs on any PC without GPIO.
"""
from __future__ import annotations

import os
import time

GPIO_PIN = 17


class PirSensor:
    def __init__(self, pin: int = GPIO_PIN, mock: bool | None = None,
                 warmup_s: float = 2.0):
        if not isinstance(pin, int) or pin < 0:
            raise ValueError(f"bad gpio pin: {pin!r}")
        self.pin = pin
        self.mock = os.getenv("PIR_MOCK", "0") == "1" if mock is None else mock
        self.warmup_s = max(0.0, float(warmup_s))
        self._gpio = None
        self._mock_state = False
        if not self.mock:
            try:
                from gpiozero import DigitalInputDevice  # type: ignore
                self._gpio = DigitalInputDevice(pin, pull_up=False)
            except Exception as e:
                raise RuntimeError(
                    f"gpiozero unavailable; use mock=True on PC ({e})"
                ) from e
        self._t0 = time.monotonic()

    def warmup_done(self) -> bool:
        return (time.monotonic() - self._t0) >= self.warmup_s

    def set_mock(self, motion: bool) -> None:
        self._mock_state = bool(motion)

    def motion(self) -> bool:
        if not self.warmup_done():
            return False
        if self.mock:
            return self._mock_state
        assert self._gpio is not None
        return bool(self._gpio.value)

    def wait_for_motion(self, timeout_s: float = 60.0) -> bool:
        if timeout_s <= 0:
            raise ValueError("timeout_s must be > 0")
        if self.mock:
            return self._mock_state
        assert self._gpio is not None
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self.motion():
                return True
            time.sleep(0.1)
        return False
