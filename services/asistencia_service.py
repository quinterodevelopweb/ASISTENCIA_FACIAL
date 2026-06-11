"""Lógica de reconocimiento facial y registro de asistencia."""

import sqlite3

import numpy as np

from core.face_encoder import get_single_face_encoding
from core.face_matcher import distance_to_confidence, find_best_match
from database.db_manager import DBManager
from services.inscripcion_service import InscripcionService
from services.usuario_service import UsuarioService


class ResultadoAsistencia:
    SIN_ROSTRO = "SIN_ROSTRO"  # no se detectó ningún rostro en el frame, seguir escaneando
    NO_IDENTIFICADO = "NO_IDENTIFICADO"  # rostro detectado pero no coincide con ningún usuario
    NO_INSCRITO = "NO_INSCRITO"  # usuario reconocido pero no pertenece a esta clase
    YA_REGISTRADO = "YA_REGISTRADO"  # ya existe un registro de hoy para usuario+clase
    REGISTRADO = "REGISTRADO"  # asistencia registrada con éxito


class AsistenciaService:
    def __init__(
        self,
        db_manager: DBManager | None = None,
        usuario_service: UsuarioService | None = None,
        inscripcion_service: InscripcionService | None = None,
    ):
        self.db = db_manager or DBManager()
        self.usuarios = usuario_service or UsuarioService(self.db)
        self.inscripciones = inscripcion_service or InscripcionService(self.db)

    def procesar_frame(self, frame_rgb: np.ndarray, idClase: int) -> tuple[str, dict | None]:
        """Procesa un frame de cámara: busca un rostro, lo identifica contra los
        encodings registrados y, si pertenece a la clase indicada, registra su
        asistencia.

        Devuelve (resultado, datos):
          - SIN_ROSTRO: no hay rostro en el frame -> seguir escaneando, sin error.
          - NO_IDENTIFICADO: hay un rostro pero no coincide con ningún usuario.
          - NO_INSCRITO: el usuario reconocido no está dado de alta en esta clase.
          - YA_REGISTRADO: el usuario ya tiene asistencia registrada hoy en esta clase.
          - REGISTRADO: asistencia registrada correctamente.
        """
        encoding = get_single_face_encoding(frame_rgb)
        if encoding is None:
            return ResultadoAsistencia.SIN_ROSTRO, None

        known_encodings, known_ids = self.usuarios.obtener_encodings_activos()
        idUsuario, distance = find_best_match(known_encodings, known_ids, encoding)
        confianza = distance_to_confidence(distance)

        if idUsuario is None:
            return ResultadoAsistencia.NO_IDENTIFICADO, {"confianza": confianza}

        usuario = self.usuarios.obtener_usuario(idUsuario)

        if not self.inscripciones.esta_inscrito(idUsuario, idClase):
            return ResultadoAsistencia.NO_INSCRITO, {"usuario": usuario, "confianza": confianza}

        if self._registrar_asistencia(idUsuario, idClase, confianza):
            return ResultadoAsistencia.REGISTRADO, {"usuario": usuario, "confianza": confianza}

        return ResultadoAsistencia.YA_REGISTRADO, {"usuario": usuario, "confianza": confianza}

    def _registrar_asistencia(self, idUsuario: int, idClase: int, confianza: float, estado: str = "PRESENTE") -> bool:
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    "INSERT INTO asistencia (idUsuario, idClase, confianza, estado) VALUES (?, ?, ?, ?)",
                    (idUsuario, idClase, confianza, estado),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def historial(self, idUsuario: int | None = None, idClase: int | None = None) -> list[dict]:
        query = "SELECT * FROM asistencia"
        condiciones = []
        params: list = []

        if idUsuario is not None:
            condiciones.append("idUsuario = ?")
            params.append(idUsuario)
        if idClase is not None:
            condiciones.append("idClase = ?")
            params.append(idClase)

        if condiciones:
            query += " WHERE " + " AND ".join(condiciones)
        query += " ORDER BY fechaHora DESC"

        with self.db.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
