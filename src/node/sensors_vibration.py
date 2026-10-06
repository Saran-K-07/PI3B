"""SW-18010P vibration sensor HAL.

Wiring: VCC 3.3V, GND, DO -> GPIO27 (Pin 13).
Module is ACTIVE-LOW: DO LOW = vibration over threshold (pot-adjusted).

We count LOW pulses inside a window: count >= threshold => HIGH vibration.
Mock mode via VIB_MOCK=1 for PC testing.
"""
from __future__ import annotations

import os
import time

GPIO_PIN = 27


class VibrationSensor:
    def __init__(self, pin: int = GPIO_PIN, mock: bool | None = None):
        if not isinstance(pin, int) or pin < 0:
            raise ValueError(f"bad gpio pin: {pin!r}")
        self.pin = pin
        self.mock = os.getenv("VIB_MOCK", "0") == "1" if mock is None else mock
        self._gpio = None
        self._mock_pulses = 0
        if not self.mock:
            try:
                from gpiozero import DigitalInputDevice  # type: ignore
                # Idle HIGH, active LOW -> pull_up keeps line stable.
                self._gpio = DigitalInputDevice(pin, pull_up=True)
            except Exception as e:
                raise RuntimeError(
                    f"gpiozero unavailable; use mock=True ({e})"
                ) from e

    def set_mock_pulses(self, n: int) -> None:
        if n < 0:
            raise ValueError("n must be >= 0")
        self._mock_pulses = int(n)

    def _active_now(self) -> bool:
        if self.mock:
            if self._mock_pulses > 0:
                self._mock_pulses -= 1
                return True
            return False
        assert self._gpio is not None
        return not bool(self._gpio.value)  # LOW = vibration

    def sample_window(self, window_s: float = 3.0,
                      pulse_threshold: int = 3) -> tuple[bool, int]:
        """Sample for window_s; return (is_high, pulse_count)."""
        if window_s <= 0 or window_s > 30:
            raise ValueError("window_s must be in (0, 30]")
        if pulse_threshold < 1:
            raise ValueError("pulse_threshold must be >= 1")
        pulses, seen_active, t0 = 0, False, time.monotonic()
        while time.monotonic() - t0 < window_s:
            active = self._active_now()
            if active and not seen_active:
                pulses += 1
                seen_active = True
            elif not active:
                seen_active = False
            time.sleep(0.02)
        return pulses >= pulse_threshold, pulses
