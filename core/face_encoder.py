"""Generación de embeddings faciales a partir de imágenes/frames."""

import dlib
import face_recognition
import numpy as np

from config.settings import FACE_DETECTION_MODEL, NUM_JITTERS


def get_face_encodings(frame: np.ndarray) -> list[np.ndarray]:
    """Detecta los rostros en un frame (RGB) y devuelve sus embeddings (128-d)."""
    locations = face_recognition.face_locations(frame, model=FACE_DETECTION_MODEL)
    return face_recognition.face_encodings(frame, known_face_locations=locations, num_jitters=NUM_JITTERS)


def get_single_face_encoding(frame: np.ndarray) -> tuple[np.ndarray | None, tuple[int, int, int, int] | None]:
    """Devuelve (embedding, ubicación) del primer rostro detectado, o (None, None) si no hay rostros.

    La ubicación tiene el formato (top, right, bottom, left) que usa face_recognition,
    en las coordenadas del frame recibido.
    """
    locations = face_recognition.face_locations(frame, model=FACE_DETECTION_MODEL)
    if not locations:
        return None, None

    encodings = face_recognition.face_encodings(frame, known_face_locations=locations[:1], num_jitters=NUM_JITTERS)
    return encodings[0], locations[0]


def get_model_version() -> str:
    """Versión de dlib usada para generar el embedding (se guarda en encodings.modelo_version)."""
    return dlib.__version__
