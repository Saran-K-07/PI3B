"""Pico LoRa RX parser with seq dedupe (MicroPython + CPython compatible).

Keeps last-seen seq per node for 60s to drop LoRa retransmit duplicates
before triggering an SMS.
"""
from __future__ import annotations

import time


class GatewayFilter:
    def __init__(self, dedupe_s: float = 60.0):
        if dedupe_s <= 0:
            raise ValueError("dedupe_s must be > 0")
        self.dedupe_s = float(dedupe_s)
        self._seen: dict = {}  # (node, seq) -> monotonic ts

    def _now(self) -> float:
        try:
            return time.monotonic()
        except Exception:
            return time.time()

    def is_duplicate(self, node: str, seq: int) -> bool:
        if not node or not isinstance(seq, int):
            raise ValueError("bad node/seq")
        now = self._now()
        # expire old entries
        for k, ts in list(self._seen.items()):
            if now - ts > self.dedupe_s:
                del self._seen[k]
        key = (node, seq)
        if key in self._seen:
            return True
        self._seen[key] = now
        return False
