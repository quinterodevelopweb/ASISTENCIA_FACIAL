"""Configuración general del sistema."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Rutas
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

DB_PATH = DATA_DIR / "asistencia.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"

# Reconocimiento facial
# Modelo de detección: "hog" (rápido, recomendado para Raspberry Pi) o "cnn" (más preciso, requiere GPU)
FACE_DETECTION_MODEL = "hog"

# Umbral de distancia para considerar una coincidencia (menor = más estricto)
FACE_MATCH_TOLERANCE = 0.45

# Cantidad de "jitters" al generar el embedding (más = más preciso pero más lento)
NUM_JITTERS = 1

# Metadatos guardados junto con cada embedding en la tabla "encoding"
ENCODING_MODEL_NAME = "face_recognition_resnet_v1"
ENCODING_DIMENSION = 128

# Detección de movimiento (vista de Asistencia)
MOTION_THRESHOLD = 25
MOTION_MIN_AREA_RATIO = 0.02

# Frecuencia de captura de frames (ms) y tiempo que se muestra un resultado
# antes de reanudar el escaneo
SCAN_INTERVAL_MS = 200
RESULT_DISPLAY_MS = 3000

# Cámara
CAMERA_INDEX = 0
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240

# Interfaz
APP_TITLE = "Sistema de Asistencia Facial"
APP_THEME = "dark"  # "dark" | "light" | "system"
APP_COLOR_THEME = "blue"
