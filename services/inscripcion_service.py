"""Inscripción de usuarios a clases (relación muchos a muchos)."""

import sqlite3

from database.db_manager import DBManager


class InscripcionService:
    def __init__(self, db_manager: DBManager | None = None):
        self.db = db_manager or DBManager()

    def inscribir(self, idUsuario: int, idClase: int) -> bool:
        """Inscribe a un usuario en una clase. Devuelve False si ya estaba inscrito."""
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    "INSERT INTO usuario_clase (idUsuario, idClase) VALUES (?, ?)",
                    (idUsuario, idClase),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def desinscribir(self, idUsuario: int, idClase: int) -> None:
        with self.db.get_connection() as conn:
            conn.execute(
                "DELETE FROM usuario_clase WHERE idUsuario = ? AND idClase = ?",
                (idUsuario, idClase),
            )

    def esta_inscrito(self, idUsuario: int, idClase: int) -> bool:
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM usuario_clase WHERE idUsuario = ? AND idClase = ? AND estado = 1",
                (idUsuario, idClase),
            ).fetchone()
            return row is not None

    def listar_clases_de_usuario(self, idUsuario: int) -> list[dict]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """SELECT c.* FROM clases c
                   JOIN usuario_clase uc ON uc.idClase = c.idClase
                   WHERE uc.idUsuario = ? AND uc.estado = 1""",
                (idUsuario,),
            ).fetchall()
            return [dict(row) for row in rows]

    def listar_usuarios_de_clase(self, idClase: int) -> list[dict]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """SELECT u.* FROM usuarios u
                   JOIN usuario_clase uc ON uc.idUsuario = u.idUsuario
                   WHERE uc.idClase = ? AND uc.estado = 1""",
                (idClase,),
            ).fetchall()
            return [dict(row) for row in rows]
