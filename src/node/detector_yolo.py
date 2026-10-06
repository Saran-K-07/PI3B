"""YOLOv8n edge detector for Pi 3B.

Pretrained COCO only (no custom training in v1).
Wanted classes: person, car, truck, bus, motorcycle.
Pi 3B tuning: imgsz 320-416, ncnn/onnx export, 1 frame per PIR trigger.

Mock mode (YOLO_MOCK=1) returns canned detections for PC/tests.
"""
from __future__ import annotations

import os

WANTED = {"person", "car", "truck", "bus", "motorcycle"}
VEHICLES = {"car", "truck", "bus", "motorcycle"}


class Detector:
    def __init__(self, model: str = "yolov8n.pt", imgsz: int = 320,
                 conf: float = 0.5, mock: bool | None = None):
        if imgsz not in (320, 416, 640):
            raise ValueError("imgsz must be 320, 416 or 640 (Pi: use 320)")
        if not 0 < conf < 1.0:
            raise ValueError("conf must be in (0, 1)")
        self.model_name, self.imgsz, self.conf = model, imgsz, conf
        self.mock = os.getenv("YOLO_MOCK", "0") == "1" if mock is None else mock
        self._model = None
        self._mock_person = float(os.getenv("YOLO_MOCK_PERSON", "0.0"))
        self._mock_vehicle = float(os.getenv("YOLO_MOCK_VEHICLE", "0.0"))
        if not self.mock:
            try:
                from ultralytics import YOLO  # type: ignore
                self._model = YOLO(model)
            except Exception as e:
                raise RuntimeError(f"ultralytics/YOLO unavailable ({e})") from e

    def set_mock(self, person_conf: float, vehicle_conf: float = 0.0) -> None:
        for v in (person_conf, vehicle_conf):
            if not 0.0 <= v <= 1.0:
                raise ValueError("mock conf must be in [0, 1]")
        self._mock_person, self._mock_vehicle = person_conf, vehicle_conf

    def infer(self, frame) -> dict:
        """Return {person: conf, vehicle: conf, vehicle_cls: str|None}.

        conf is max confidence for that group, 0.0 if absent.
        """
        if frame is None:
            raise ValueError("frame must not be None")
        if self.mock:
            out = {"person": float(self._mock_person),
                   "vehicle": float(self._mock_vehicle),
                   "vehicle_cls": None}
            if self._mock_vehicle >= self.conf:
                out["vehicle_cls"] = "car"
            return out
        assert self._model is not None
        res = self._model.predict(frame, imgsz=self.imgsz,
                                  conf=self.conf, verbose=False)[0]
        person, vehicle, vcls = 0.0, 0.0, None
        names = res.names
        for b in res.boxes:
            cls = names[int(b.cls[0])]
            c = float(b.conf[0])
            if cls not in WANTED:
                continue
            if cls == "person":
                person = max(person, c)
            elif cls in VEHICLES and c > vehicle:
                vehicle, vcls = c, cls
        return {"person": person, "vehicle": vehicle, "vehicle_cls": vcls}
