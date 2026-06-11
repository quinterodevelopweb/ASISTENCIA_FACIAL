"""Widget reutilizable: guía visual y barra de progreso para capturar el rostro
de un usuario desde varios ángulos (frente, izquierda, derecha)."""

import time
from typing import Callable

import customtkinter as ctk
import face_recognition
import numpy as np

from config.settings import (
    ENROLLMENT_CHECK_INTERVAL_S,
    ENROLLMENT_FRAMES_REQUERIDOS,
    ENROLLMENT_YAW_FRONTAL,
    ENROLLMENT_YAW_GIRO,
    FACE_DETECTION_MODEL,
    NUM_JITTERS,
)

FASES = ["FRENTE", "IZQUIERDA", "DERECHA"]

INSTRUCCIONES = {
    "FRENTE": "Mira de frente a la cámara",
    "IZQUIERDA": "Gira lentamente tu rostro hacia la izquierda",
    "DERECHA": "Gira lentamente tu rostro hacia la derecha",
}


class FaceEnrollmentWidget(ctk.CTkFrame):
    """Procesa frames y guía al usuario para capturar un encoding por cada ángulo."""

    def __init__(self, master, on_completado: Callable[[], None] | None = None, **kwargs):
        super().__init__(master, **kwargs)
        self._on_completado = on_completado

        self.label_instruccion = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.label_instruccion.pack(pady=(5, 2))

        self.progressbar = ctk.CTkProgressBar(self)
        self.progressbar.pack(pady=2, padx=20, fill="x")
        self.progressbar.set(0)

        self.label_estado = ctk.CTkLabel(self, text="", text_color="gray")
        self.label_estado.pack(pady=(2, 5))

        self._fase_idx = 0
        self._progreso = 0
        self._encodings: list[np.ndarray] = []
        self._activo = False
        self._ultimo_check = 0.0

        self._mostrar_inactivo()

    # --- Control -------------------------------------------------------------

    def iniciar(self) -> None:
        self._fase_idx = 0
        self._progreso = 0
        self._encodings = []
        self._activo = True
        self._ultimo_check = 0.0
        self._actualizar_ui()

    def reset(self) -> None:
        self._activo = False
        self._fase_idx = 0
        self._progreso = 0
        self._encodings = []
        self._mostrar_inactivo()

    def esta_completo(self) -> bool:
        return self._fase_idx >= len(FASES)

    def obtener_encodings(self) -> list[np.ndarray]:
        return list(self._encodings)

    # --- Procesamiento de frames ----------------------------------------------

    def procesar_frame(self, frame_rgb: np.ndarray) -> None:
        if not self._activo or self.esta_completo():
            return

        ahora = time.monotonic()
        if ahora - self._ultimo_check < ENROLLMENT_CHECK_INTERVAL_S:
            return
        self._ultimo_check = ahora

        ubicaciones = face_recognition.face_locations(frame_rgb, model=FACE_DETECTION_MODEL)
        if len(ubicaciones) != 1:
            mensaje = "No se detecta un rostro" if not ubicaciones else "Solo debe haber una persona frente a la cámara"
            self.label_estado.configure(text=mensaje)
            return

        landmarks_lista = face_recognition.face_landmarks(frame_rgb, ubicaciones)
        if not landmarks_lista:
            self.label_estado.configure(text="No se detecta un rostro")
            return

        yaw = self._calcular_yaw(landmarks_lista[0])
        fase = FASES[self._fase_idx]

        if not self._yaw_corresponde(fase, yaw):
            self.label_estado.configure(text=self._mensaje_ajuste(fase))
            return

        self.label_estado.configure(text="Mantén la posición...")
        self._progreso += 1
        self.progressbar.set(self._progreso / ENROLLMENT_FRAMES_REQUERIDOS)

        if self._progreso >= ENROLLMENT_FRAMES_REQUERIDOS:
            encodings = face_recognition.face_encodings(
                frame_rgb, known_face_locations=ubicaciones, num_jitters=NUM_JITTERS
            )
            if encodings:
                self._encodings.append(encodings[0])

            self._fase_idx += 1
            self._progreso = 0

            if self.esta_completo():
                self._activo = False
                self.label_instruccion.configure(text="¡Captura completa!")
                self.label_estado.configure(text="")
                self.progressbar.set(1.0)
                if self._on_completado:
                    self._on_completado()
            else:
                self._actualizar_ui()

    # --- Estimación de orientación ---------------------------------------------

    @staticmethod
    def _calcular_yaw(landmarks: dict) -> float:
        """Aproxima el giro horizontal del rostro a partir de los puntos de
        referencia: ~0 de frente, y se aleja de 0 hacia cada lado conforme el
        rostro gira (la nariz se desplaza respecto al centro de los ojos)."""
        ojo_izq = np.mean(landmarks["left_eye"], axis=0)
        ojo_der = np.mean(landmarks["right_eye"], axis=0)
        nariz = np.mean(landmarks["nose_bridge"], axis=0)

        centro_ojos_x = (ojo_izq[0] + ojo_der[0]) / 2
        distancia_ojos = abs(ojo_izq[0] - ojo_der[0])
        if distancia_ojos == 0:
            return 0.0

        return float((nariz[0] - centro_ojos_x) / (distancia_ojos / 2))

    @staticmethod
    def _yaw_corresponde(fase: str, yaw: float) -> bool:
        if fase == "FRENTE":
            return abs(yaw) < ENROLLMENT_YAW_FRONTAL
        if fase == "IZQUIERDA":
            return yaw < -ENROLLMENT_YAW_GIRO
        if fase == "DERECHA":
            return yaw > ENROLLMENT_YAW_GIRO
        return False

    @staticmethod
    def _mensaje_ajuste(fase: str) -> str:
        if fase == "FRENTE":
            return "Coloca tu rostro de frente a la cámara"
        if fase == "IZQUIERDA":
            return "Gira un poco más tu rostro hacia la izquierda"
        return "Gira un poco más tu rostro hacia la derecha"

    # --- UI --------------------------------------------------------------------

    def _actualizar_ui(self) -> None:
        fase = FASES[self._fase_idx]
        self.label_instruccion.configure(text=INSTRUCCIONES[fase])
        self.label_estado.configure(text="")
        self.progressbar.set(0)

    def _mostrar_inactivo(self) -> None:
        self.label_instruccion.configure(text='Presiona "Iniciar captura" para comenzar')
        self.label_estado.configure(text="")
        self.progressbar.set(0)
