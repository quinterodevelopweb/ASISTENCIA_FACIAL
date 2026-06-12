"""Operaciones sobre usuarios, tipos de usuario y sus encodings faciales."""

import numpy as np

from config.settings import ENCODING_DIMENSION, ENCODING_MODEL_NAME
from core.face_encoder import get_model_version
from core.face_matcher import find_best_match
from database.db_manager import DBManager

CAMPOS_ACTUALIZABLES_USUARIO = {
    "tipoUsuario",
    "noCuenta",
    "nombre",
    "apPaterno",
    "apMaterno",
    "email",
    "telefono",
    "password",
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
        password: str | None = None,
    ) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO usuarios
                   (tipoUsuario, noCuenta, nombre, apPaterno, apMaterno, email, telefono, password)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (tipoUsuario, noCuenta, nombre, apPaterno, apMaterno, email, telefono, password),
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

    def activar_usuario(self, idUsuario: int) -> None:
        self.actualizar_usuario(idUsuario, estado=1)

    def eliminar_usuario(self, idUsuario: int) -> None:
        """Elimina al usuario de forma permanente junto con sus encodings,
        inscripciones y registros de asistencia (ON DELETE CASCADE)."""
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM usuarios WHERE idUsuario = ?", (idUsuario,))

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

    def guardar_encodings(self, idUsuario: int, vectores: list[np.ndarray]) -> None:
        for vector in vectores:
            self.guardar_encoding(idUsuario, vector)

    def reemplazar_encodings(self, idUsuario: int, vectores: list[np.ndarray]) -> None:
        """Desactiva los encodings activos del usuario y guarda los nuevos."""
        with self.db.get_connection() as conn:
            conn.execute("UPDATE encoding SET estado = 0 WHERE idUsuario = ? AND estado = 1", (idUsuario,))
        self.guardar_encodings(idUsuario, vectores)

    def obtener_encodings_activos(self) -> tuple[list[np.ndarray], list[int]]:
        """Devuelve los embeddings activos junto con el id de usuario asociado,
        listos para comparar con find_best_match()."""
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT idUsuario, vector FROM encoding WHERE estado = 1").fetchall()

        vectores = [self.db.blob_to_encoding(row["vector"]) for row in rows]
        ids = [row["idUsuario"] for row in rows]
        return vectores, ids

    def autenticar_profesor(self, noCuenta: str, password: str) -> dict | None:
        """Verifica las credenciales (no. de cuenta + contraseña) de un profesor
        para entrar al panel de Profesor. Devuelve el usuario si coinciden y
        está activo, o None si no."""
        with self.db.get_connection() as conn:
            row = conn.execute(
                """SELECT u.* FROM usuarios u
                   JOIN tipo_usuario tu ON tu.idTipoUsuario = u.tipoUsuario
                   WHERE u.noCuenta = ? AND u.password = ? AND u.estado = 1
                     AND tu.nombreTipoUsuario = 'Profesor'""",
                (noCuenta, password),
            ).fetchone()
            return dict(row) if row else None

    def buscar_usuario_por_rostro(
        self, encodings: list[np.ndarray], excluir_idUsuario: int | None = None
    ) -> dict | None:
        """Busca si alguno de los encodings dados coincide con el rostro de OTRO
        usuario ya registrado (p. ej. al recapturar el rostro durante una
        edición). Devuelve ese usuario, o None si no hay coincidencia."""
        known_encodings, known_ids = self.obtener_encodings_activos()
        if excluir_idUsuario is not None:
            pares = [(e, uid) for e, uid in zip(known_encodings, known_ids) if uid != excluir_idUsuario]
            known_encodings = [e for e, _ in pares]
            known_ids = [uid for _, uid in pares]

        for encoding in encodings:
            idUsuario, _ = find_best_match(known_encodings, known_ids, encoding)
            if idUsuario is not None:
                return self.obtener_usuario(idUsuario)
        return None
