#!/usr/bin/env bash
# Pi 3B forest-node setup for Debian 13 trixie (aarch64, Python 3.13).
# Run ON THE PI over SSH. Idempotent: safe to re-run.
set -euo pipefail
cd "$(dirname "$0")/.."

sudo raspi-config nonint do_spi 0 || true

# APT layer: Debian builds of cv2/numpy/gpiozero (fast, low RAM).
# NOTE: libatlas-base-dev does NOT exist on trixie; libopenblas pulls in via deps.
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip python3-opencv \
  python3-numpy python3-gpiozero python3-pytest v4l-utils

# Venv that REUSES apt site packages (trixie PEP-668 compliant, no --break-system-packages).
if [ ! -d "$HOME/pi3b-venv" ]; then
  python3 -m venv --system-site-packages "$HOME/pi3b-venv"
fi
# shellcheck disable=SC1091
source "$HOME/pi3b-venv/bin/activate"
python3 -m pip install --upgrade pip
# --no-cache-dir: Pi 3B has ~600M available; default pip cache can exhaust RAM/tmp.
python3 -m pip install --no-cache-dir -r config/requirements-node.txt

python3 -c "import numpy; print('numpy', numpy.__version__)"
python3 -c "import cv2; print('cv2', cv2.__version__)"
python3 -c "import gpiozero; print('gpiozero ok')"
ls /dev/spidev0.* /dev/video0

# Heavy step last: downloads yolov8n.pt (~6MB) then ncnn export. May OOM on
# 1GB Pi — failure here is non-fatal; ONNX-Runtime fallback documented in docs.
python3 scripts/export_yolov8n_ncnn.py --imgsz 320 || true
echo "OK. Then: source ~/pi3b-venv/bin/activate && python3 -m src.node.main --config config/node.yaml"
