"""Multi-sensor fusion: YOLO + vibration + sound -> suspicious?.

score = max(person, vehicle)*0.6 + vib*0.25 + snd*0.25 (+pir 0.1), cap 1.0
SUSPICIOUS iff score >= threshold AND (person or vehicle present).

This keeps PIR-only wind/animal triggers from sending SMS.
"""
from __future__ import annotations


def fuse(person_conf: float, vehicle_conf: float, vibration_high: bool,
         sound_high: bool, pir: bool = True,
         threshold: float = 0.6) -> dict:
    for name, v in (("person_conf", person_conf),
                    ("vehicle_conf", vehicle_conf)):
        if not isinstance(v, (int, float)) or not 0.0 <= float(v) <= 1.0:
            raise ValueError(f"bad {name}: {v!r}")
    if not 0 < threshold <= 1.0:
        raise ValueError("threshold must be in (0, 1]")
    ai = max(float(person_conf), float(vehicle_conf))
    score = ai * 0.6
    if vibration_high:
        score += 0.25
    if sound_high:
        score += 0.25
    if pir:
        score += 0.10
    score = min(1.0, score)
    detected = person_conf > 0 or vehicle_conf > 0
    suspicious = bool(detected and score >= threshold)
    return {
        "score": round(score, 3),
        "suspicious": suspicious,
        "person": person_conf > 0,
        "confidence": int(round(max(person_conf, vehicle_conf) * 100)),
    }
