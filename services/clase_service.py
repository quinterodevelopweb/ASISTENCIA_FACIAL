"""Operaciones sobre clases (grupos/periodos a los que se les toma asistencia)."""

from database.db_manager import DBManager

CAMPOS_ACTUALIZABLES_CLASE = {"nombreClase", "periodoClase", "estado"}


class ClaseService:
    def __init__(self, db_manager: DBManager | None = None):
        self.db = db_manager or DBManager()

    def crear_clase(self, nombreClase: str, periodoClase: str) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO clases (nombreClase, periodoClase) VALUES (?, ?)",
                (nombreClase, periodoClase),
            )
            return cursor.lastrowid

    def actualizar_clase(self, idClase: int, **campos) -> None:
        campos = {k: v for k, v in campos.items() if k in CAMPOS_ACTUALIZABLES_CLASE}
        if not campos:
            return

        sets = ", ".join(f"{campo} = ?" for campo in campos)
        with self.db.get_connection() as conn:
            conn.execute(f"UPDATE clases SET {sets} WHERE idClase = ?", [*campos.values(), idClase])

    def desactivar_clase(self, idClase: int) -> None:
        self.actualizar_clase(idClase, estado=0)

    def obtener_clase(self, idClase: int) -> dict | None:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM clases WHERE idClase = ?", (idClase,)).fetchone()
            return dict(row) if row else None

    def listar_clases(self, solo_activas: bool = True) -> list[dict]:
        query = "SELECT * FROM clases"
        if solo_activas:
            query += " WHERE estado = 1"
        query += " ORDER BY periodoClase DESC, nombreClase"

        with self.db.get_connection() as conn:
            rows = conn.execute(query).fetchall()
            return [dict(row) for row in rows]
