"""USB camera capture (USB2.0 PC CAM on /dev/video0, YUYV-only).

Verified on Pi: index 0 = capture device (640x480 YUYV), index 1 = metadata
sub-device (not a capture device). Forces V4L2 backend to silence GStreamer
fallback warnings. Runs at 640x480 for YOLO (downscaled to 320 at inference).
Mock mode (CAM_MOCK=1) returns a synthetic image so CI/PC works headless.
"""
from __future__ import annotations

import os
import time

WIDTH, HEIGHT = 640, 480


class Camera:
    def __init__(self, index: int = 0, width: int = WIDTH, height: int = HEIGHT,
                 mock: bool | None = None):
        if index < 0:
            raise ValueError("index must be >= 0")
        if width <= 0 or height <= 0:
            raise ValueError("bad resolution")
        self.index, self.width, self.height = index, width, height
        self.mock = os.getenv("CAM_MOCK", "0") == "1" if mock is None else mock
        self._cap = None
        if not self.mock:
            try:
                import cv2  # type: ignore
            except Exception as e:
                raise RuntimeError(f"opencv required on Pi ({e})") from e
            cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
            try:
                fourcc = cv2.VideoWriter_fourcc(*"YUYV")
                cap.set(cv2.CAP_PROP_FOURCC, fourcc)
            except Exception:
                pass
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            if not cap.isOpened():
                raise RuntimeError(f"cannot open camera {index}")
            self._cap = cap

    def capture(self, retries: int = 3):
        """Return BGR numpy frame (H, W, 3). Raises on failure."""
        if retries < 1:
            raise ValueError("retries must be >= 1")
        if self.mock:
            import numpy as np
            return (np.zeros((self.height, self.width, 3),
                             dtype="uint8") + 60)
        import cv2  # noqa
        assert self._cap is not None
        for _ in range(retries):
            ok, frame = self._cap.read()
            if ok and frame is not None:
                return frame
            time.sleep(0.2)
        raise RuntimeError("camera capture failed")

    def save_evidence(self, frame, path: str) -> str:
        if not path:
            raise ValueError("path must be non-empty")
        import cv2  # type: ignore
        ok = cv2.imwrite(path, frame)
        if not ok:
            raise RuntimeError(f"cannot write {path}")
        return path

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
