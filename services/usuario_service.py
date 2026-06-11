"""Operaciones sobre usuarios, tipos de usuario y sus encodings faciales."""

import numpy as np

from config.settings import ENCODING_DIMENSION, ENCODING_MODEL_NAME
from core.face_encoder import get_model_version
from database.db_manager import DBManager

CAMPOS_ACTUALIZABLES_USUARIO = {
    "tipoUsuario",
    "noCuenta",
    "nombre",
    "apPaterno",
    "apMaterno",
    "email",
    "telefono",
    "estado",
}


class UsuarioService:
    def __init__(self, db_manager: DBManager | None = None):
        self.db = db_manager or DBManager()

    # --- Tipos de usuario -----------------------------------------------------

    def listar_tipos_usuario(self) -> list[dict]:
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM tipo_usuario WHERE estado = 1").fetchall()
            return [dict(row) for row in rows]

    # --- Usuarios ---------------------------------------------------------------

    def crear_usuario(
        self,
        tipoUsuario: int,
        nombre: str,
        apPaterno: str,
        apMaterno: str | None = None,
        noCuenta: str | None = None,
        email: str | None = None,
        telefono: str | None = None,
    ) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO usuarios
                   (tipoUsuario, noCuenta, nombre, apPaterno, apMaterno, email, telefono)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (tipoUsuario, noCuenta, nombre, apPaterno, apMaterno, email, telefono),
            )
            return cursor.lastrowid

    def actualizar_usuario(self, idUsuario: int, **campos) -> None:
        campos = {k: v for k, v in campos.items() if k in CAMPOS_ACTUALIZABLES_USUARIO}
        if not campos:
            return

        sets = ", ".join(f"{campo} = ?" for campo in campos)
        with self.db.get_connection() as conn:
            conn.execute(f"UPDATE usuarios SET {sets} WHERE idUsuario = ?", [*campos.values(), idUsuario])

    def desactivar_usuario(self, idUsuario: int) -> None:
        self.actualizar_usuario(idUsuario, estado=0)

    def obtener_usuario(self, idUsuario: int) -> dict | None:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM usuarios WHERE idUsuario = ?", (idUsuario,)).fetchone()
            return dict(row) if row else None

    def listar_usuarios(self, solo_activos: bool = True) -> list[dict]:
        query = "SELECT * FROM usuarios"
        if solo_activos:
            query += " WHERE estado = 1"
        query += " ORDER BY apPaterno, apMaterno, nombre"

        with self.db.get_connection() as conn:
            rows = conn.execute(query).fetchall()
            return [dict(row) for row in rows]

    # --- Encodings faciales --------------------------------------------------

    def guardar_encoding(self, idUsuario: int, vector: np.ndarray) -> None:
        with self.db.get_connection() as conn:
            conn.execute(
                """INSERT INTO encoding (idUsuario, vector, modelo, modeloVersion, dimension)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    idUsuario,
                    self.db.encoding_to_blob(vector),
                    ENCODING_MODEL_NAME,
                    get_model_version(),
                    ENCODING_DIMENSION,
                ),
            )

    def obtener_encodings_activos(self) -> tuple[list[np.ndarray], list[int]]:
        """Devuelve los embeddings activos junto con el id de usuario asociado,
        listos para comparar con find_best_match()."""
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT idUsuario, vector FROM encoding WHERE estado = 1").fetchall()

        vectores = [self.db.blob_to_encoding(row["vector"]) for row in rows]
        ids = [row["idUsuario"] for row in rows]
        return vectores, ids
