"""Power helpers for Pi 3B field node (no true deep sleep on Pi)."""
from __future__ import annotations

import time


def cooldown(seconds: float = 5.0) -> None:
    if seconds < 0:
        raise ValueError("seconds must be >= 0")
    time.sleep(seconds)


def battery_percent() -> int:
    """Placeholder: no fuel gauge on stock Pi. Override via BATT_PCT env."""
    import os
    try:
        v = int(os.getenv("BATT_PCT", "78"))
    except ValueError:
        v = 78
    return max(0, min(100, v))
