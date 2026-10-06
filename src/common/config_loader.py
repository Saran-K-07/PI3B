"""Minimal YAML-free config loader (stdlib only, MicroPython friendly).

Node/gateway YAML files here are flat `key: value` lines on purpose
so both CPython (Pi) and MicroPython (Pico) can parse them without PyYAML.
"""
from __future__ import annotations


def load_flat_config(path: str) -> dict:
    data: dict = {}
    with open(path, "r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                raise ValueError(f"{path}:{lineno}: missing ':' in {raw!r}")
            key, _, val = line.partition(":")
            key, val = key.strip(), val.strip().strip("\"'")
            if not key:
                raise ValueError(f"{path}:{lineno}: empty key")
            data[key] = _coerce(val)
    return data


def _coerce(val: str):
    low = val.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    return val
