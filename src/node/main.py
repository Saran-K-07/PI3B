"""Forest node main loop: PIR -> camera -> YOLO -> fuse -> LoRa.

Run on Pi 3B:  python3 -m src.node.main --config config/node.yaml
Mock on PC:   PIR_MOCK=1 VIB_MOCK=1 SOUND_MOCK=1 CAM_MOCK=1 YOLO_MOCK=1 LORA_MOCK=1 \
              python3 -m src.node.main --once
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.common.config_loader import load_flat_config  # noqa: E402
from src.common.logger import Logger  # noqa: E402
from src.common.packet import AlertPacket  # noqa: E402
from src.node.camera import Camera  # noqa: E402
from src.node.detector_yolo import Detector  # noqa: E402
from src.node.fusion import fuse  # noqa: E402
from src.node.lora_tx import LoraTx  # noqa: E402
from src.node.power import battery_percent, cooldown  # noqa: E402
from src.node.sensors_audio import SoundSensor  # noqa: E402
from src.node.sensors_pir import PirSensor  # noqa: E402
from src.node.sensors_vibration import VibrationSensor  # noqa: E402

LOG = Logger("forest-node")


def _hhmm() -> str:
    return datetime.now().strftime("%H%M")


def build(config: dict, mock_all: bool = False):
    m = True if mock_all else None
    pir = PirSensor(pin=int(config.get("pir_pin", 17)),
                    mock=m, warmup_s=float(config.get("pir_warmup_s", 2.0)))
    vib = VibrationSensor(pin=int(config.get("vib_pin", 27)), mock=m)
    snd = SoundSensor(pin=int(config.get("sound_pin", 23)),
                      active_high=bool(config.get("sound_active_high", True)),
                      mock=m)
    cam = Camera(index=int(config.get("cam_index", 0)), mock=m)
    det = Detector(model=str(config.get("yolo_model", "yolov8n.pt")),
                   imgsz=int(config.get("yolo_imgsz", 320)),
                   conf=float(config.get("yolo_conf", 0.5)), mock=m)
    lora = LoraTx(frequency=float(config.get("lora_freq", 433e6)),
                  sf=int(config.get("lora_sf", 9)),
                  bw=int(config.get("lora_bw", 125)),
                  power=int(config.get("lora_power", 17)), mock=m)
    return pir, vib, snd, cam, det, lora


def handle_trigger(pir, vib, snd, cam, det, lora, node_id: str,
                   seq: int, ev_dir: str = "/tmp") -> dict:
    """Single PIR-triggered pipeline. Returns result dict (testable)."""
    if not node_id:
        raise ValueError("node_id must be non-empty")
    frame = cam.capture()
    det_out = det.infer(frame)
    vib_high, vib_n = vib.sample_window(window_s=3.0)
    snd_high, snd_frac = snd.sample_window(window_s=3.0)
    res = fuse(det_out["person"], det_out["vehicle"], vib_high, snd_high)
    pkt = AlertPacket(
        node=node_id, suspicious=res["suspicious"], person=res["person"],
        vibration_high=vib_high, sound_high=snd_high,
        confidence=res["confidence"], hhmm=_hhmm(),
        battery=battery_percent(), seq=seq % 256,
    )
    if res["suspicious"]:
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            cam.save_evidence(frame, os.path.join(ev_dir, f"{node_id}_{ts}.jpg"))
        except Exception as e:
            LOG.warn(f"evidence save failed: {e}")
        lora.send(pkt.encode())
        LOG.info(f"TX {pkt.encode()}")
    else:
        LOG.info(f"normal (score={res['score']} vib={vib_n} snd={snd_frac:.2f})")
    return {"packet": pkt.encode(), "result": res,
            "vib_pulses": vib_n, "snd_frac": snd_frac}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/node.yaml")
    ap.add_argument("--once", action="store_true",
                    help="single iteration (for mock/CI)")
    ap.add_argument("--mock", action="store_true",
                    help="force all sensors mock")
    args = ap.parse_args()

    cfg = load_flat_config(args.config) if os.path.exists(args.config) else {}
    node_id = str(cfg.get("node_id", "F01"))
    mock = args.mock or os.getenv("NODE_MOCK", "0") == "1"
    pir, vib, snd, cam, det, lora = build(cfg, mock_all=mock)
    LOG.info(f"node {node_id} up (mock={mock}). PIR warmup...")
    seq = 0
    try:
        while True:
            if pir.wait_for_motion(timeout_s=5.0 if args.once else 60.0):
                seq += 1
                handle_trigger(pir, vib, snd, cam, det, lora, node_id, seq)
                cooldown(float(cfg.get("cooldown_s", 5.0)))
            elif args.once:
                # CI path: force one trigger with canned mock detection
                if mock:
                    pir.set_mock(True)
                    det.set_mock(0.92, 0.0)
                    vib.set_mock_pulses(5)
                    snd.set_mock_loud(True)
                    seq += 1
                    handle_trigger(pir, vib, snd, cam, det, lora, node_id, seq)
                break
            if args.once:
                break
    except KeyboardInterrupt:
        LOG.info("stopped")
    finally:
        try:
            cam.close()
        except Exception:
            pass
        lora.sleep()


if __name__ == "__main__":
    main()
