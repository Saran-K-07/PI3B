"""Adiy sound sensor HAL (KY-038-like, DO only in v1).

Wiring: VCC 3.3V, GND, DO -> GPIO23 (Pin 16). AO left unconnected
(Pi 3B has no ADC; add MCP3008 later for analog level).

Polarity depends on pot/module: most boards drive DO HIGH on loud.
Set `active_high=False` if yours pulls LOW on loud.
We require sustained loud readings over a window to reject wind gusts.

Mock mode via SOUND_MOCK=1.
"""
from __future__ import annotations

import os
import time

GPIO_PIN = 23


class SoundSensor:
    def __init__(self, pin: int = GPIO_PIN, active_high: bool = True,
                 mock: bool | None = None):
        if not isinstance(pin, int) or pin < 0:
            raise ValueError(f"bad gpio pin: {pin!r}")
        self.pin = pin
        self.active_high = bool(active_high)
        self.mock = os.getenv("SOUND_MOCK", "0") == "1" if mock is None else mock
        self._gpio = None
        self._mock_loud = False
        if not self.mock:
            try:
                from gpiozero import DigitalInputDevice  # type: ignore
                self._gpio = DigitalInputDevice(pin, pull_up=False)
            except Exception as e:
                raise RuntimeError(
                    f"gpiozero unavailable; use mock=True ({e})"
                ) from e

    def set_mock_loud(self, loud: bool) -> None:
        self._mock_loud = bool(loud)

    def loud_now(self) -> bool:
        if self.mock:
            return self._mock_loud
        assert self._gpio is not None
        v = bool(self._gpio.value)
        return v if self.active_high else (not v)

    def sample_window(self, window_s: float = 3.0,
                      loud_ratio: float = 0.4) -> tuple[bool, float]:
        """Return (is_high, fraction_loud). is_high if fraction >= loud_ratio."""
        if window_s <= 0 or window_s > 30:
            raise ValueError("window_s must be in (0, 30]")
        if not 0 < loud_ratio <= 1.0:
            raise ValueError("loud_ratio must be in (0, 1]")
        hits, total, t0 = 0, 0, time.monotonic()
        while time.monotonic() - t0 < window_s:
            total += 1
            if self.loud_now():
                hits += 1
            time.sleep(0.05)
        frac = (hits / total) if total else 0.0
        return frac >= loud_ratio, frac
