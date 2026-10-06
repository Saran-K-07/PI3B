# LoRa protocol

* 433MHz, SF9, BW125, sync `0x12`, TX 17dBm (match both ends).
* Payload ASCII ≤32B: `NODE|EVENT|FLAGS|CONF|HHMM|BATT|SEQ`, e.g. `F01|S|P1V1S1|92|1935|78|042`.
* `EVENT` N/S, `FLAGS` P/V/S 0/1, `CONF/BATT` 0-100, `SEQ` 000-255 rolling.
* Gateway dedupes `(node, seq)` for 60s, drops malformed packets, only `S` sends SMS.
* SMS: `ALERT F01 SUS P1 V1 S1 92% 1935 B78%` (≤160 chars).
