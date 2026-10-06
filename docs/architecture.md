# Architecture

```
PIR SE (GPIO17) ─┐
SW-18010P (GPIO27, active-LOW) ─┼→ Pi 3B → USB cam (/dev/video0, 640x480)
Adiy sound DO (GPIO23) ─┘         → YOLOv8n person/vehicle → fusion → Ra-02 TX (SPI0)
                                                                            │ 433MHz SF9
                                              Pico Ra-02 RX (SPI0 GP2-7) ←──┘
                                              → dedupe seq 60s → SIM800L UART1 SMS → USB log
```

Fusion: `score = ai*0.6 + vib*0.25 + snd*0.25 + pir*0.1`, SUS if `score>=0.6` and person/vehicle.
Packet: `F01|S|P1V1S1|92|1935|78|042`. Images stay on Pi SD.
