"""USB serial monitor for Pico gateway logs (PC side).

Usage: python3 scripts/serial_monitor.py --port /dev/ttyACM0 --baud 115200
"""
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("--port", default="/dev/ttyACM0")
ap.add_argument("--baud", type=int, default=115200)
args = ap.parse_args()

try:
    import serial
except ImportError:
    raise SystemExit("pip install pyserial")

with serial.Serial(args.port, args.baud, timeout=1) as s:
    print(f"listening {args.port} @ {args.baud} (Ctrl+C to stop)")
    while True:
        line = s.readline().decode("utf-8", "ignore").strip()
        if line:
            print(line)
