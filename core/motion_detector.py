"""Detección simple de movimiento por diferencia entre frames consecutivos."""

import cv2
import numpy as np

from config.settings import MOTION_MIN_AREA_RATIO, MOTION_THRESHOLD


class MotionDetector:
    """Compara cada frame contra el anterior para decidir si hubo movimiento."""

    def __init__(self, threshold: int = MOTION_THRESHOLD, min_area_ratio: float = MOTION_MIN_AREA_RATIO):
        self.threshold = threshold
        self.min_area_ratio = min_area_ratio
        self._prev_gray: np.ndarray | None = None

    def detecta_movimiento(self, frame_rgb: np.ndarray) -> bool:
        gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self._prev_gray is None:
            self._prev_gray = gray
            return False

        diff = cv2.absdiff(self._prev_gray, gray)
        self._prev_gray = gray

        _, thresh = cv2.threshold(diff, self.threshold, 255, cv2.THRESH_BINARY)
        moved_ratio = np.count_nonzero(thresh) / thresh.size
        return moved_ratio > self.min_area_ratio

    def reset(self) -> None:
        self._prev_gray = None
