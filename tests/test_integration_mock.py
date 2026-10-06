import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.update({"PIR_MOCK": "1", "VIB_MOCK": "1", "SOUND_MOCK": "1",
                   "CAM_MOCK": "1", "YOLO_MOCK": "1", "LORA_MOCK": "1"})

from src.node.camera import Camera
from src.node.detector_yolo import Detector
from src.node.lora_tx import LoraTx
from src.node.main import handle_trigger
from src.node.sensors_audio import SoundSensor
from src.node.sensors_pir import PirSensor
from src.node.sensors_vibration import VibrationSensor


def _harness(person=0.92, vib_pulses=5, loud=True):
    pir = PirSensor(mock=True, warmup_s=0)
    vib = VibrationSensor(mock=True)
    snd = SoundSensor(mock=True)
    cam = Camera(mock=True)
    det = Detector(mock=True)
    lora = LoraTx(mock=True)
    pir.set_mock(True)
    det.set_mock(person, 0.0)
    vib.set_mock_pulses(vib_pulses)
    snd.set_mock_loud(loud)
    # shrink windows via monkeypatch-free path: sample_window uses time;
    # for speed, pre-seed then call handle with short-circuit not possible,
    # so we accept 6s runtime in CI. Use small pulses for normal case.
    return pir, vib, snd, cam, det, lora


def test_end_to_end_suspicious_sends_lora():
    pir, vib, snd, cam, det, lora = _harness()
    # speed up: directly drive sample via mock pulses exhaustion is 3s each;
    # keep as-is for correctness (CI ~6s).
    out = handle_trigger(pir, vib, snd, cam, det, lora, "F01", 7,
                         ev_dir="/tmp")
    assert out["result"]["suspicious"] is True
    assert len(lora.sent) == 1
    assert lora.sent[0].startswith("F01|S|")


def test_end_to_end_normal_sends_nothing():
    pir, vib, snd, cam, det, lora = _harness(person=0.0, vib_pulses=0,
                                            loud=False)
    out = handle_trigger(pir, vib, snd, cam, det, lora, "F01", 8,
                         ev_dir="/tmp")
    assert out["result"]["suspicious"] is False
    assert lora.sent == []
