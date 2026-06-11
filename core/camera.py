"""Captura de video desde la cámara (USB o módulo de Raspberry Pi vía OpenCV)."""

import cv2
import numpy as np

from config.settings import CAMERA_FPS, CAMERA_HEIGHT, CAMERA_INDEX, CAMERA_WIDTH


class Camera:
    """Wrapper sobre cv2.VideoCapture con resolución reducida para optimizar la Pi."""

    def __init__(
        self,
        index: int = CAMERA_INDEX,
        width: int = CAMERA_WIDTH,
        height: int = CAMERA_HEIGHT,
        fps: int = CAMERA_FPS,
    ):
        self.index = index
        self.width = width
        self.height = height
        self.fps = fps
        self._cap: cv2.VideoCapture | None = None

    def start(self) -> None:
        self._cap = cv2.VideoCapture(self.index)
        # MJPG reduce el ancho de banda USB necesario, permitiendo más FPS a mayor resolución
        self._cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._cap.set(cv2.CAP_PROP_FPS, self.fps)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def read_frame_rgb(self) -> np.ndarray | None:
        """Devuelve el frame actual en formato RGB (el que espera face_recognition)."""
        if self._cap is None:
            return None
        ok, frame_bgr = self._cap.read()
        if not ok:
            return None
        return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

    def stop(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self) -> "Camera":
        self.start()
        return self

    def __exit__(self, *_exc_info) -> None:
        self.stop()
