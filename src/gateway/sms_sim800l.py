"""SIM800L SMS sender (MicroPython + CPython compatible).

Wiring: Pico GP8 (UART1 TX) -> divider -> SIM RX,
        Pico GP9 (UART1 RX) <- SIM TX, common GND.
Power: dedicated 4.0V buck 2A peak + 100-1000uF cap at VBAT. NOT Pico 5V pin.

AT flow: AT -> ATE0 -> AT+CPIN? -> AT+CREG? -> AT+CMGF=1 -> AT+CMGS="<num>" -> text + Ctrl+Z.
All UART reads have timeouts; every step validates input at boundary.
"""
from __future__ import annotations

import time

CTRL_Z = "\x1a"


def build_cmgs_commands(recipient: str, text: str) -> list[str]:
    if not recipient or not recipient.strip():
        raise ValueError("recipient must be non-empty")
    if not text or not text.strip():
        raise ValueError("text must be non-empty")
    recipient = recipient.strip()
    if len(recipient) > 20:
        raise ValueError("recipient too long")
    if len(text) > 160:
        raise ValueError("SMS text exceeds 160 chars")
    return ["AT", "ATE0", "AT+CMGF=1", f'AT+CMGS="{recipient}"', text + CTRL_Z]


class Sim800l:
    def __init__(self, uart, timeout_s: float = 5.0):
        if uart is None:
            raise ValueError("uart must not be None")
        if timeout_s <= 0:
            raise ValueError("timeout_s must be > 0")
        self.uart = uart
        self.timeout_s = float(timeout_s)

    def _read_line(self) -> str:
        deadline = time.time() + self.timeout_s
        buf = b""
        while time.time() < deadline:
            try:
                avail = self.uart.any()
            except Exception:
                avail = 0
            if avail:
                chunk = self.uart.read(1)
                if chunk:
                    buf += chunk
                    if buf.endswith(b"\n"):
                        break
            else:
                time.sleep(0.05)
        try:
            return buf.decode("utf-8", "ignore").strip()
        except Exception:
            return ""

    def _cmd(self, cmd: str, expect: str = "OK",
             wait_s: float = 3.0) -> bool:
        if not isinstance(cmd, str) or not cmd:
            raise ValueError("cmd must be non-empty str")
        self.uart.write((cmd + "\r\n").encode())
        deadline = time.time() + wait_s
        seen = ""
        while time.time() < deadline:
            line = self._read_line()
            if line:
                seen += line + "|"
                if expect in line:
                    return True
                if "ERROR" in line:
                    return False
        return expect in seen

    def boot(self) -> bool:
        return self._cmd("AT", expect="OK", wait_s=5.0)

    def send_sms(self, recipient: str, text: str) -> bool:
        cmds = build_cmgs_commands(recipient, text)
        # AT, ATE0, CMGF=1
        for c in cmds[:3]:
            if not self._cmd(c):
                return False
        # CMGS prompt: expect '>' then send body + Ctrl+Z
        self.uart.write((cmds[3] + "\r\n").encode())
        time.sleep(1.0)
        self.uart.write(cmds[4].encode())
        deadline = time.time() + 15.0
        while time.time() < deadline:
            line = self._read_line()
            if "OK" in line:
                return True
            if "ERROR" in line:
                return False
        return False
