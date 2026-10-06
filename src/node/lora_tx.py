"""Ra-02 (SX1278) LoRa TX for Pi 3B.

SPI0: NSS GPIO8, SCK GPIO11, MOSI GPIO10, MISO GPIO9,
      RST GPIO22, DIO0 GPIO24. 3.3V ONLY. Antenna required before TX.

Mock mode (LORA_MOCK=1) records payloads in `sent` for tests.
Real mode needs `pySX127x` (pip install pySX127x) + SPI enabled.
"""
from __future__ import annotations

import os


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
        if not self.mock:
            try:
                from SX127x.LoRa import LoRa  # type: ignore
                from SX127x.board_config import BOARD  # type: ignore
                BOARD.setup()
                self._lora = LoRa(verbose=False)
                self._lora.set_mode(1)  # standby
                self._lora.set_freq(frequency / 1e6)
                self._lora.set_spreading_factor(sf)
                self._lora.set_bw(bw)
                self._lora.set_pa_config(pa_select=1, max_power=21,
                                         output_power=power)
                self._lora.set_sync_word(sync_word)
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
        self._lora.write_payload(list(data))
        self._lora.set_mode(3)  # TX
        return True

    def sleep(self) -> None:
        if self._lora is not None:
            try:
                self._lora.set_mode(0)
            except Exception:
                pass
