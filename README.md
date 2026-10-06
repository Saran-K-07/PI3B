# PI3B — Edge AI Tree Smuggling Detection (Pi 3B + Pico + Ra-02 + SIM800L)

PIR → USB camera → YOLOv8n (Pi 3B) → vibration/sound fusion → Ra-02 LoRa → Pico gateway → SIM800L SMS.

* Node: `src/node/main.py` (PIR GPIO17, VIB SW-18010P GPIO27 active-LOW, sound DO GPIO23, Ra-02 SPI0 RST GPIO22 DIO0 GPIO24)
* Gateway: `src/gateway/gateway.ino` (Arduino, recommended) or `src/gateway/main.py` (MicroPython)
* Packet: `F01|S|P1V1S1|92|1935|78|042` — see `docs/lora_protocol.md`
* Wiring: `docs/wiring.md` | Tests: `python3 -m pytest tests/ -q`

Mock demo (no hardware): `PIR_MOCK=1 VIB_MOCK=1 SOUND_MOCK=1 CAM_MOCK=1 YOLO_MOCK=1 LORA_MOCK=1 python3 -m src.node.main --once --mock`
