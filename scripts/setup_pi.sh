#!/usr/bin/env bash
# Pi 3B setup: SPI, deps, YOLO ncnn export hint. Run on the Pi, not PC.
set -euo pipefail
sudo raspi-config nonint do_spi 0 || true
sudo apt-get update
sudo apt-get install -y python3-pip python3-opencv libatlas-base-dev
python3 -m pip install --upgrade pip
python3 -m pip install -r config/requirements-node.txt
python3 scripts/export_yolov8n_ncnn.py --imgsz 320 || true
echo "OK. Reboot once, then: python3 -m src.node.main --config config/node.yaml"
