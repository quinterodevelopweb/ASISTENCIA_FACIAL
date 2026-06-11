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

# --- Enrolamiento facial guiado (captura de frente / izquierda / derecha) -----
# Cuántas detecciones válidas seguidas se necesitan para completar cada ángulo
ENROLLMENT_FRAMES_REQUERIDOS = 8
# Cada cuánto tiempo (segundos) se analiza un frame durante el enrolamiento
ENROLLMENT_CHECK_INTERVAL_S = 0.3
# |desplazamiento de la nariz| / (ancho entre ojos / 2) por debajo del cual se
# considera que el rostro está de frente
ENROLLMENT_YAW_FRONTAL = 0.18
# por encima de este valor se considera que el rostro está girado hacia un lado
ENROLLMENT_YAW_GIRO = 0.35

# Metadatos guardados junto con cada embedding en la tabla "encoding"
ENCODING_MODEL_NAME = "face_recognition_resnet_v1"
ENCODING_DIMENSION = 128

# Detección de movimiento (vista de Asistencia)
MOTION_THRESHOLD = 25
MOTION_MIN_AREA_RATIO = 0.02
# Ancho (px) al que se reduce el frame solo para calcular el movimiento (más rápido)
MOTION_DETECTION_WIDTH = 160

# Ancho (px) al que se reduce el frame solo para el reconocimiento facial (más rápido)
RECOGNITION_WIDTH = 320

# Frecuencia de captura de frames (ms) y tiempo que se muestra un resultado
# antes de reanudar el escaneo
SCAN_INTERVAL_MS = 40
RESULT_DISPLAY_MS = 3000

# Cámara
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# Interfaz
APP_TITLE = "Sistema de Asistencia Facial"
APP_THEME = "dark"  # "dark" | "light" | "system"
APP_COLOR_THEME = "blue"

# Contraseña para entrar al panel de administrador desde la pantalla de escaneo.
# IMPORTANTE: cambiar este valor antes de usar el sistema en producción.
ADMIN_PASSWORD = "admin123"
