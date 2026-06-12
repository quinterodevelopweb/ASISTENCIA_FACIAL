"""Captura de video desde la cámara (USB o módulo de Raspberry Pi vía OpenCV)."""

import threading

import cv2
import numpy as np

from config.settings import CAMERA_FPS, CAMERA_HEIGHT, CAMERA_INDEX, CAMERA_WIDTH


class Camera:
    """Wrapper sobre cv2.VideoCapture que captura en un hilo aparte.

    cv2.VideoCapture.read() puede bloquearse mientras llega el siguiente frame
    de la cámara. Si se llama directamente desde el loop de Tkinter (after()),
    cualquier retraso de la cámara se traduce en lag de toda la interfaz. Por
    eso un hilo de fondo lee continuamente y deja el último frame disponible;
    read_frame_rgb() simplemente devuelve esa última copia sin bloquear.
    """

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
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._frame: np.ndarray | None = None
        self._running = False

    def start(self) -> None:
        self._cap = cv2.VideoCapture(self.index)
        # MJPG reduce el ancho de banda USB necesario, permitiendo más FPS a mayor resolución
        self._cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._cap.set(cv2.CAP_PROP_FPS, self.fps)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self._frame = None
        self._running = True
        self._thread = threading.Thread(target=self._capturar, daemon=True)
        self._thread.start()

    def _capturar(self) -> None:
        while self._running and self._cap is not None:
            ok, frame_bgr = self._cap.read()
            if not ok:
                continue
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            # Efecto espejo: más intuitivo para colocarse frente a la cámara.
            # Se aplica aquí (antes de detección/reconocimiento/enrolamiento)
            # para que todo el pipeline trabaje sobre la misma imagen que ve
            # el usuario en pantalla.
            frame_rgb = cv2.flip(frame_rgb, 1)
            with self._lock:
                self._frame = frame_rgb

    def read_frame_rgb(self) -> np.ndarray | None:
        """Devuelve el último frame capturado en formato RGB (el que espera face_recognition)."""
        with self._lock:
            return self._frame

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self) -> "Camera":
        self.start()
        return self

    def __exit__(self, *_exc_info) -> None:
        self.stop()
