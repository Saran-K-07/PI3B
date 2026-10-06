"""Compact LoRa alert packet for forest node <-> Pico gateway.

Format (ASCII, <32 bytes on air):
    F01|S|P1V1S1|92|1935|78|042

Fields:
  node   : 3-char ID, e.g. F01 (validated [A-Z0-9]{3})
  event  : N=normal, S=suspicious
  flags  : P0/1 person, V0/1 vibration-high, S0/1 sound-high
  conf   : 0-100 AI confidence
  hm     : HHMM 24h time of detection
  batt   : 0-100 battery percent
  seq    : 0-255 rolling sequence (dedupe on gateway)

Validation happens at both encode and decode (system boundary).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

NODE_RE = re.compile(r"^[A-Z0-9]{3}$")
FLAGS_RE = re.compile(r"^P[01]V[01]S[01]$")
HM_RE = re.compile(r"^([01]\d|2[0-3])[0-5]\d$")

MAX_PACKET_LEN = 64


@dataclass
class AlertPacket:
    node: str
    suspicious: bool
    person: bool
    vibration_high: bool
    sound_high: bool
    confidence: int
    hhmm: str
    battery: int
    seq: int

    def encode(self) -> str:
        validate_packet(self)
        event = "S" if self.suspicious else "N"
        flags = (
            f"P{1 if self.person else 0}"
            f"V{1 if self.vibration_high else 0}"
            f"S{1 if self.sound_high else 0}"
        )
        return (
            f"{self.node}|{event}|{flags}|{self.confidence}|"
            f"{self.hhmm}|{self.battery}|{self.seq:03d}"
        )

    def to_sms(self) -> str:
        """Human-readable SMS text for SIM800L."""
        validate_packet(self)
        kind = "SUS" if self.suspicious else "OK"
        return (
            f"ALERT {self.node} {kind} "
            f"P{1 if self.person else 0} "
            f"V{1 if self.vibration_high else 0} "
            f"S{1 if self.sound_high else 0} "
            f"{self.confidence}% {self.hhmm} B{self.battery}%"
        )


def validate_packet(p: AlertPacket) -> None:
    if not NODE_RE.match(p.node):
        raise ValueError(f"bad node id: {p.node!r}")
    if not HM_RE.match(p.hhmm):
        raise ValueError(f"bad hhmm: {p.hhmm!r}")
    for name, v, lo, hi in (
        ("confidence", p.confidence, 0, 100),
        ("battery", p.battery, 0, 100),
        ("seq", p.seq, 0, 255),
    ):
        if not isinstance(v, int) or not (lo <= v <= hi):
            raise ValueError(f"bad {name}: {v!r}")


def decode(raw: str) -> AlertPacket:
    """Parse + validate a received packet. Raises ValueError on bad input."""
    if not isinstance(raw, str):
        raise ValueError("packet must be str")
    raw = raw.strip()
    if not raw or len(raw) > MAX_PACKET_LEN:
        raise ValueError("packet empty or too long")
    parts = raw.split("|")
    if len(parts) != 7:
        raise ValueError(f"want 7 fields, got {len(parts)}: {raw!r}")
    node, event, flags, conf, hhmm, batt, seq = parts
    if not NODE_RE.match(node):
        raise ValueError(f"bad node: {node!r}")
    if event not in ("N", "S"):
        raise ValueError(f"bad event: {event!r}")
    if not FLAGS_RE.match(flags):
        raise ValueError(f"bad flags: {flags!r}")
    try:
        confidence = int(conf)
        battery = int(batt)
        seq_n = int(seq)
    except ValueError as e:
        raise ValueError(f"bad numeric field: {e}") from e
    pkt = AlertPacket(
        node=node,
        suspicious=(event == "S"),
        person=(flags[1] == "1"),
        vibration_high=(flags[3] == "1"),
        sound_high=(flags[5] == "1"),
        confidence=confidence,
        hhmm=hhmm,
        battery=battery,
        seq=seq_n,
    )
    validate_packet(pkt)
    return pkt
