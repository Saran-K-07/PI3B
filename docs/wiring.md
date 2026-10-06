# Wiring

## Forest node (Pi 3B)
| Module | Pi pin |
|---|---|
| Ra-02 VCC / GND | 3V3 Pin1 / GND Pin6 (+ all GND pads), antenna ON before power |
| Ra-02 NSS/SCK/MOSI/MISO | GPIO8 Pin24 / GPIO11 Pin23 / GPIO10 Pin19 / GPIO9 Pin21 |
| Ra-02 RST / DIO0 | GPIO22 Pin15 / GPIO24 Pin18 |
| PIR SE VCC/GND/OUT | 5V Pin2 / GND / GPIO17 Pin11, 30-60s warmup |
| SW-18010P VCC/GND/DO | 3.3V Pin17 / GND / GPIO27 Pin13 (LOW = vibration) |
| Sound Adiy VCC/GND/DO | 3.3V / GND / GPIO23 Pin16 (AO NC; set `sound_active_high` to match your board) |
| USB camera | any USB, check `/dev/video0` |

Enable SPI: `sudo raspi-config nonint do_spi 0`.

## Gateway (Pico)
| Module | Pico pin |
|---|---|
| Ra-02 3V3/GND | 3V3(OUT) Pin36 / GND Pin38 (+ all GNDs) |
| SCK/MOSI/MISO/NSS/RST/DIO0 | GP2 / GP3 / GP4 / GP5 / GP6 / GP7 |
| SIM800L VBAT | 4.0V buck 2A + 100-1000uF cap at module, common GND (NOT Pico 5V) |
| SIM800L UART | Pico GP8 TX → divider → SIM RX; GP9 RX ← SIM TX; 9600 baud |
| USB | to PC for `serial_monitor.py` logs |

Pico firmware: Arduino `src/gateway/gateway.ino` (recommended) or MicroPython `src/gateway/main.py` + vendored `sx127x.py`.
