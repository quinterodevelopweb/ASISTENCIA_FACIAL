"""Lóoogica de reconocimiento facial y registro de asistencia."""

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
    SIN_CLASES = "SIN_CLASES"  # usuario reconocido pero no inscrito en ninguna clase
    IDENTIFICADO = "IDENTIFICADO"  # usuario reconocido, debe elegir su clase
    YA_REGISTRADO = "YA_REGISTRADO"  # ya existe un registro de ese tipo hoy para usuario+clase
    REGISTRADO = "REGISTRADO"  # asistencia registrada con éxito
    ERROR = "ERROR"  # ocurrió un error inesperado al procesar el frame


class TipoRegistro:
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"


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

    def identificar(self, frame_rgb: np.ndarray) -> tuple[str, dict | None]:
        """Busca un rostro en el frame y lo identifica contra los encodings registrados.

        Devuelve (resultado, datos):
          - SIN_ROSTRO: no hay rostro en el frame -> seguir escaneando, sin error.
          - NO_IDENTIFICADO: hay un rostro pero no coincide con ningún usuario.
          - SIN_CLASES: el usuario fue reconocido pero no está inscrito en ninguna clase.
          - IDENTIFICADO: usuario reconocido; datos incluye "usuario", "confianza" y "clases"
            (las clases en las que está inscrito, para que elija una).
        """
        encoding, location = get_single_face_encoding(frame_rgb)
        if encoding is None:
            return ResultadoAsistencia.SIN_ROSTRO, None

        known_encodings, known_ids = self.usuarios.obtener_encodings_activos()
        idUsuario, distance = find_best_match(known_encodings, known_ids, encoding)
        confianza = distance_to_confidence(distance)

        if idUsuario is None:
            return ResultadoAsistencia.NO_IDENTIFICADO, {"confianza": confianza, "location": location}

        usuario = self.usuarios.obtener_usuario(idUsuario)
        clases = self.inscripciones.listar_clases_de_usuario(idUsuario)

        if not clases:
            return ResultadoAsistencia.SIN_CLASES, {"usuario": usuario, "confianza": confianza, "location": location}

        return ResultadoAsistencia.IDENTIFICADO, {
            "usuario": usuario,
            "confianza": confianza,
            "clases": clases,
            "location": location,
        }

    def registrar_asistencia(self, idUsuario: int, idClase: int, confianza: float, tipo: str) -> str:
        """Registra una entrada o salida (tipo: TipoRegistro.ENTRADA/SALIDA) de un
        usuario ya identificado en la clase elegida.

        Devuelve REGISTRADO o YA_REGISTRADO (si ya existía un registro de ese tipo
        hoy para ese usuario y clase, restricción idx_asistencia_unica).
        """
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    "INSERT INTO asistencia (idUsuario, idClase, fechaHora, confianza, tipoRegistro) "
                    "VALUES (?, ?, datetime('now', 'localtime'), ?, ?)",
                    (idUsuario, idClase, confianza, tipo),
                )
            return ResultadoAsistencia.REGISTRADO
        except sqlite3.IntegrityError:
            return ResultadoAsistencia.YA_REGISTRADO

    def registros_hoy(self, idUsuario: int, idClase: int) -> set[str]:
        """Tipos de registro (ENTRADA/SALIDA) que el usuario ya hizo hoy en esta clase."""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT tipoRegistro FROM asistencia "
                "WHERE idUsuario = ? AND idClase = ? AND DATE(fechaHora) = DATE('now', 'localtime')",
                (idUsuario, idClase),
            ).fetchall()
        return {row["tipoRegistro"] for row in rows}

    def historial(self, idUsuario: int | None = None, idClase: int | None = None) -> list[dict]:
        query = """
            SELECT
                a.idAsistencia,
                a.fechaHora,
                a.tipoRegistro,
                a.idUsuario,
                a.idClase,
                u.nombre,
                u.apPaterno,
                u.apMaterno,
                c.nombreClase,
                c.periodoClase
            FROM asistencia a
            JOIN usuarios u ON u.idUsuario = a.idUsuario
            JOIN clases c ON c.idClase = a.idClase
        """
        condiciones = []
        params: list = []

        if idUsuario is not None:
            condiciones.append("a.idUsuario = ?")
            params.append(idUsuario)
        if idClase is not None:
            condiciones.append("a.idClase = ?")
            params.append(idClase)

        if condiciones:
            query += " WHERE " + " AND ".join(condiciones)
        query += " ORDER BY a.fechaHora DESC"

        with self.db.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
