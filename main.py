"""Punto de entrada de la aplicación."""

from database.db_manager import DBManager
from gui.app import App
from utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    logger.info("Iniciando Sistema de Asistencia Facial")

    db = DBManager()
    db.init_db()

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
