import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["YOLO_MOCK"] = "1"

from src.node.detector_yolo import Detector


def test_mock_person():
    d = Detector(mock=True)
    d.set_mock(0.92, 0.0)
    out = d.infer(object())
    assert out["person"] == 0.92
    assert out["vehicle"] == 0.0


def test_mock_empty():
    d = Detector(mock=True)
    d.set_mock(0.0, 0.0)
    out = d.infer(object())
    assert out["person"] == 0.0
