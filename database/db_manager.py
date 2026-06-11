"""Gestión de la conexión y operaciones básicas sobre la base de datos SQLite."""

import sqlite3
from pathlib import Path

import numpy as np

from config.settings import DB_PATH, SCHEMA_PATH


class DBManager:
    """Encapsula la conexión a SQLite y la inicialización del esquema."""

    def __init__(self, db_path: Path = DB_PATH, schema_path: Path = SCHEMA_PATH):
        self.db_path = db_path
        self.schema_path = schema_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self) -> None:
        """Crea las tablas definidas en schema.sql si la base de datos aún no existe."""
        with self.get_connection() as conn:
            existe = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='tipo_usuario'"
            ).fetchone()
            if existe is None:
                with open(self.schema_path, "r", encoding="utf-8") as f:
                    conn.executescript(f.read())

    @staticmethod
    def encoding_to_blob(encoding: np.ndarray) -> bytes:
        """Serializa un embedding (float64[128]) a bytes para guardarlo en SQLite."""
        return encoding.astype(np.float64).tobytes()

    @staticmethod
    def blob_to_encoding(blob: bytes) -> np.ndarray:
        """Reconstruye un embedding a partir de los bytes guardados en SQLite."""
        return np.frombuffer(blob, dtype=np.float64)
