"""Tiny logger that works on CPython and MicroPython."""
from __future__ import annotations

import sys
import time


def _ts() -> str:
    try:
        t = time.localtime()
        return f"{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
    except Exception:
        return "?"


class Logger:
    def __init__(self, tag: str = "node"):
        if not tag or not isinstance(tag, str):
            raise ValueError("tag must be non-empty str")
        self.tag = tag

    def _emit(self, level: str, msg: str) -> None:
        sys.stdout.write(f"[{_ts()}] [{level}] [{self.tag}] {msg}\n")

    def info(self, msg: str) -> None:
        self._emit("INFO", str(msg))

    def warn(self, msg: str) -> None:
        self._emit("WARN", str(msg))

    def error(self, msg: str) -> None:
        self._emit("ERR", str(msg))
