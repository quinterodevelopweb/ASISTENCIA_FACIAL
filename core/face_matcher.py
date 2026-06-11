"""Comparación de embeddings faciales para identificar usuarios."""

import face_recognition
import numpy as np

from config.settings import FACE_MATCH_TOLERANCE


def find_best_match(
    known_encodings: list[np.ndarray],
    known_ids: list[int],
    encoding_to_check: np.ndarray,
    tolerance: float = FACE_MATCH_TOLERANCE,
) -> tuple[int | None, float]:
    """Compara un embedding contra una lista de embeddings conocidos.

    Devuelve (usuario_id, distancia) del mejor match, o (None, distancia) si
    ninguno está dentro de la tolerancia.
    """
    if not known_encodings:
        return None, 1.0

    distances = face_recognition.face_distance(known_encodings, encoding_to_check)
    best_index = int(np.argmin(distances))
    best_distance = float(distances[best_index])

    if best_distance <= tolerance:
        return known_ids[best_index], best_distance
    return None, best_distance


def distance_to_confidence(distance: float) -> float:
    """Convierte una distancia euclidiana de face_recognition a un valor 0-1
    apto para la columna asistencia.confianza (0 = sin parecido, 1 = match perfecto)."""
    return max(0.0, min(1.0, 1.0 - distance))
