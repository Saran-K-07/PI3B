import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.gateway.lora_rx import GatewayFilter
from src.gateway.sms_sim800l import build_cmgs_commands


def test_dedupe():
    f = GatewayFilter(dedupe_s=60.0)
    assert f.is_duplicate("F01", 42) is False
    assert f.is_duplicate("F01", 42) is True
    assert f.is_duplicate("F01", 43) is False


def test_cmgs_build():
    cmds = build_cmgs_commands("+911234567890", "ALERT F01 SUS")
    assert cmds[0] == "AT"
    assert cmds[3].startswith('AT+CMGS="+91')
    assert cmds[4].endswith("\x1a")


def test_cmgs_rejects_bad():
    for args in [("", "hi"), ("+91", ""), ("+91", "x" * 161)]:
        try:
            build_cmgs_commands(*args)
        except ValueError:
            continue
        raise AssertionError(f"should reject {args!r}")
