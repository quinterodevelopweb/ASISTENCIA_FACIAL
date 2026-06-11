"""Generación de embeddings faciales a partir de imágenes/frames."""

import dlib
import face_recognition
import numpy as np

from config.settings import FACE_DETECTION_MODEL, NUM_JITTERS


def get_face_encodings(frame: np.ndarray) -> list[np.ndarray]:
    """Detecta los rostros en un frame (RGB) y devuelve sus embeddings (128-d)."""
    locations = face_recognition.face_locations(frame, model=FACE_DETECTION_MODEL)
    return face_recognition.face_encodings(frame, known_face_locations=locations, num_jitters=NUM_JITTERS)


def get_single_face_encoding(frame: np.ndarray) -> np.ndarray | None:
    """Devuelve el embedding del primer rostro detectado, o None si no hay rostros."""
    encodings = get_face_encodings(frame)
    return encodings[0] if encodings else None


def get_model_version() -> str:
    """Versión de dlib usada para generar el embedding (se guarda en encodings.modelo_version)."""
    return dlib.__version__
