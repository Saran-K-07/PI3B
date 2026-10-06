"""Ra-02 (SX1278) LoRa TX for Pi 3B.

SPI0: NSS GPIO8, SCK GPIO11, MOSI GPIO10, MISO GPIO9,
      RST GPIO22, DIO0 GPIO24. 3.3V ONLY. Antenna required before TX.

Mock mode (LORA_MOCK=1) records payloads in `sent` for tests.
Real mode uses `LoRaRF` (pip install LoRaRF) — pure-Python, works on
Python 3.13/trixie. Legacy `pySX127x` is NOT used: it caps at
Python <=3.11 and has no sdist, so pip cannot install it on this Pi.
"""
from __future__ import annotations

import os


def _set_tx_power(lora, power: int) -> None:
    """Set TX power across LoRaRF API variants.

    1.4.0 renamed/reshaped the power call vs older docs; probe instead of
    assuming. Raises RuntimeError listing available methods if none match.
    """
    if hasattr(lora, "setOutputPower"):
        lora.setOutputPower(power)
        return
    if hasattr(lora, "setTxPower"):
        try:
            lora.setTxPower(power)
        except TypeError:
            lora.setTxPower(power, True)  # some variants take paBoost flag
        return
    if hasattr(lora, "setPower"):
        lora.setPower(power)
        return
    avail = sorted(m for m in dir(lora) if "ower" in m or "Power" in m)
    raise RuntimeError(f"no TX-power method on LoRaRF driver (power-ish: {avail})")


class LoraTx:
    def __init__(self, frequency: float = 433e6, sf: int = 9, bw: int = 125,
                 power: int = 17, sync_word: int = 0x12,
                 mock: bool | None = None):
        if frequency not in (433e6, 868e6, 915e6):
            raise ValueError("frequency must be 433/868/915 MHz")
        if sf not in range(6, 13):
            raise ValueError("sf must be 6..12")
        if power < 2 or power > 20:
            raise ValueError("power must be 2..20 dBm")
        self.frequency, self.sf, self.bw = frequency, sf, bw
        self.power, self.sync_word = power, sync_word
        self.mock = os.getenv("LORA_MOCK", "0") == "1" if mock is None else mock
        self.sent: list[str] = []
        self._lora = None
        self._backend = "mock" if self.mock else ""
        if not self.mock:
            self._lora = self._init_lorarf()

    def _init_lorarf(self):
        try:
            from LoRaRF import SX127x  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "LoRaRF not installed; run "
                "'pip install --no-cache-dir LoRaRF' "
                f"in ~/pi3b-venv ({e})"
            ) from e
        try:
            lora = SX127x()
            lora.begin()
            lora.setFrequency(int(self.frequency))
            lora.setSpreadingFactor(self.sf)
            lora.setBandwidth(self.bw * 1000)  # kHz -> Hz
            lora.setSyncWord(self.sync_word)
            _set_tx_power(lora, self.power)
            self._backend = "LoRaRF"
            return lora
        except Exception as e:
            raise RuntimeError(f"LoRa HW init failed ({e})") from e

    def send(self, payload: str) -> bool:
        if not isinstance(payload, str) or not payload:
            raise ValueError("payload must be non-empty str")
        data = payload.encode("utf-8")
        if len(data) > 255:
            raise ValueError("payload exceeds 255-byte LoRa limit")
        if self.mock:
            self.sent.append(payload)
            return True
        assert self._lora is not None
        self._lora.send(data)
        return True

    def sleep(self) -> None:
        if self._lora is not None:
            try:
                self._lora.sleep()
            except Exception:
                pass
