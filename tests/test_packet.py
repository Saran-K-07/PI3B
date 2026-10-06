import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.common.packet import AlertPacket, decode


def test_encode_decode_roundtrip():
    p = AlertPacket("F01", True, True, True, True, 92, "1935", 78, 42)
    assert decode(p.encode()) == p


def test_normal_event():
    p = AlertPacket("F01", False, False, False, False, 0, "0000", 100, 0)
    assert decode(p.encode()).suspicious is False


def test_rejects_bad():
    for bad in ["", "F01|S", "F01|S|P1V1S1|92|1935|78",
                "XX|S|P1V1S1|92|1935|78|001",
                "F01|X|P1V1S1|92|1935|78|001",
                "F01|S|P9V1S1|92|1935|78|001",
                "F01|S|P1V1S1|999|1935|78|001"]:
        try:
            decode(bad)
        except ValueError:
            continue
        raise AssertionError(f"should reject {bad!r}")


def test_sms_format():
    p = AlertPacket("F01", True, True, True, False, 92, "1935", 78, 42)
    sms = p.to_sms()
    assert sms.startswith("ALERT F01 SUS")
    assert len(sms) <= 160
