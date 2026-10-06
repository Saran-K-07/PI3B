"""Pico gateway main (MicroPython).

Wiring (SPI0): SCK GP2, MOSI GP3, MISO GP4, NSS GP5, RST GP6, DIO0 GP7.
SIM800L on UART1: TX GP8 -> SIM RX (via divider), RX GP9 <- SIM TX.
Config: edit CFG below or copy config/gateway.yaml values here.

Needs vendored `sx127x.py` driver on Pico (see docs/wiring.md).
Run: copy main.py + sx127x.py to Pico via Thonny, reset.
"""
from machine import Pin, SPI, UART  # type: ignore

import time
import sys

sys.path.append("")

CFG = {
    "freq": 433e6,
    "sf": 9,
    "bw": 125,
    "power": 17,
    "recipients": ["+91XXXXXXXXXX"],  # <-- set ranger numbers
    "dedupe_s": 60.0,
}

_seen = {}


def _expired(now, ts, window):
    return (now - ts) > window


def is_duplicate(node, seq, now):
    for k in list(_seen.keys()):
        if _expired(now, _seen[k], CFG["dedupe_s"]):
            del _seen[k]
    key = (node, seq)
    if key in _seen:
        return True
    _seen[key] = now
    return False


def parse_minimal(raw):
    # Minimal decode without importing CPython packet.py (keeps Pico lean).
    # Validates 7 fields; raises ValueError on bad input.
    if not raw or len(raw) > 64:
        raise ValueError("bad len")
    p = raw.strip().split("|")
    if len(p) != 7:
        raise ValueError("want 7 fields")
    node, event, flags = p[0], p[1], p[2]
    if len(node) != 3 or event not in ("N", "S") or len(flags) != 6:
        raise ValueError("bad header/flags")
    conf, hhmm, batt, seq = int(p[3]), p[4], int(p[5]), int(p[6])
    if not (0 <= conf <= 100 and 0 <= batt <= 100 and 0 <= seq <= 255):
        raise ValueError("bad numbers")
    kind = "SUS" if event == "S" else "OK"
    sms = "ALERT %s %s %s %d%% %s B%d%%" % (node, kind, flags, conf, hhmm, batt)
    return node, seq, event, sms


def uart_cmd(uart, cmd, wait_s=3.0):
    uart.write((cmd + "\r\n").encode())
    t0 = time.time()
    buf = ""
    while time.time() - t0 < wait_s:
        if uart.any():
            try:
                buf += uart.read(1).decode("ignore")
            except Exception:
                pass
            if "OK" in buf:
                return True
            if "ERROR" in buf:
                return False
        else:
            time.sleep(0.05)
    return "OK" in buf


def send_sms(uart, recipient, text):
    if not uart_cmd(uart, "AT", 5.0):
        return False
    uart_cmd(uart, "ATE0")
    if not uart_cmd(uart, "AT+CMGF=1"):
        return False
    uart.write(('AT+CMGS="%s"\r\n' % recipient).encode())
    time.sleep(1.0)
    uart.write((text + "\x1a").encode())
    t0 = time.time()
    buf = ""
    while time.time() - t0 < 15:
        if uart.any():
            try:
                buf += uart.read(32).decode("ignore")
            except Exception:
                pass
            if "OK" in buf:
                return True
            if "ERROR" in buf:
                return False
        else:
            time.sleep(0.1)
    return False


def main():
    print("[gw] boot: LoRa RX -> SIM800L SMS")
    spi = SPI(0, baudrate=5_000_000, sck=Pin(2), mosi=Pin(3), miso=Pin(4))
    try:
        from sx127x import SX127x  # vendored driver
    except Exception as e:
        print("[gw] missing sx127x.py driver:", e)
        return
    lora = SX127x(spi, pins={"ss": 5, "reset": 6, "dio_0": 7},
                  parameters={"frequency": CFG["freq"],
                              "spreading_factor": CFG["sf"],
                              "signal_bandwidth": CFG["bw"],
                              "tx_power_level": CFG["power"],
                              "sync_word": 0x12})
    uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9), timeout=2000)
    print("[gw] listening 433MHz SF9...")
    while True:
        try:
            raw = None
            try:
                if lora.available():
                    raw = lora.read_payload(as_string=True)
            except Exception:
                time.sleep(0.2)
                continue
            if not raw:
                time.sleep(0.2)
                continue
            print("[gw] RX:", raw)
            try:
                node, seq, event, sms = parse_minimal(raw)
            except Exception as e:
                print("[gw] bad packet:", e)
                continue
            if is_duplicate(node, seq, time.time()):
                print("[gw] dupe ignored")
                continue
            print("[gw] USB-LOG:", sms)
            if event == "S":
                for r in CFG["recipients"]:
                    ok = send_sms(uart, r, sms)
                    print("[gw] SMS", r, "OK" if ok else "FAIL")
                    time.sleep(2)
            time.sleep(0.2)
        except Exception as e:
            print("[gw] loop err:", e)
            time.sleep(1.0)


if __name__ == "__main__":
    main()
