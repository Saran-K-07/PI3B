# Field test checklist

1. Bench: each sensor DO toggles (hand wave → PIR HIGH; tap → VIB LOW pulses; clap → sound DO).
2. Camera: `ls /dev/video0`, capture 640x480 frame saves to `/tmp`.
3. YOLO: person frame scores >0.5, empty forest frame scores 0.
4. LoRa 10m loopback TX→RX, then 200-500m line-of-sight.
5. Gateway: `AT` OK, `AT+CREG?` registered, SMS to 1 number arrives.
6. End-to-end: person + shake + clap → SMS <15s; wind-only → no SMS.
7. Log false alarms for 24h; tune `yolo_conf`, VIB pulses, sound ratio, fusion threshold.
