import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.node.fusion import fuse


def test_suspicious_full_evidence():
    r = fuse(0.92, 0.0, True, True)
    assert r["suspicious"] is True
    assert r["confidence"] == 92


def test_no_person_no_alert():
    r = fuse(0.0, 0.0, True, True)
    assert r["suspicious"] is False


def test_person_alone_below_threshold():
    # 0.55*0.6 + 0.1 pir = 0.43 < 0.6 -> not suspicious
    r = fuse(0.55, 0.0, False, False)
    assert r["suspicious"] is False


def test_person_plus_vibration_triggers():
    # 0.9*0.6 + 0.25 + 0.1 = 0.89 -> suspicious
    r = fuse(0.9, 0.0, True, False)
    assert r["suspicious"] is True


def test_rejects_bad_conf():
    try:
        fuse(2.0, 0.0, False, False)
    except ValueError:
        return
    raise AssertionError("should reject conf > 1")
