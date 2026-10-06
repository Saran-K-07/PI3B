# Field test checklist

1. Bench: each sensor DO toggles (hand wave → PIR HIGH; tap → VIB LOW pulses; clap → sound DO).
2. Camera: `ls /dev/video0`, capture 640x480 frame saves to `/tmp`. NOTE trixie: index 0 = capture (YUYV 640x480), index 1 = metadata (not a camera).
3. YOLO: person frame scores >0.5, empty forest frame scores 0.
4. LoRa 10m loopback TX→RX, then 200-500m line-of-sight.
5. Gateway: `AT` OK, `AT+CREG?` registered, SMS to 1 number arrives.
6. End-to-end: person + shake + clap → SMS <15s; wind-only → no SMS.
7. Log false alarms for 24h; tune `yolo_conf`, VIB pulses, sound ratio, fusion threshold.

## Observed 2026-10-06 signatures (trixie Pi 3B, all wired)
* PIR hits/80 = 0 during waving → check Pin 11 (GPIO17), 5V supply, H jumper, sensitivity pot mid, 60s warmup; rule out dead GPIO by temp-moving OUT to GPIO23.
* VIB low-hits 399/400 (stuck LOW) → threshold pot fully CW; trim to ~12 o'clock until idle reads HIGH and only taps pulse LOW.
* SND high:160/low:0 in silence (stuck HIGH) → SND pot too sensitive; trim CCW until signal LED dark in silence, one clap lights it; flip `sound_active_high` to False if board is LOW-on-loud.
* Single-shot `.value` reads miss ms pulses — always verify with 5-8s poll loops, not one read.
* `/dev/serial0` absent on node = normal (node uses SPI + USB; UART lives on Pico gateway).
