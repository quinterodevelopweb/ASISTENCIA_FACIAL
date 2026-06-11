"""Vista de reconocimiento en vivo: detecta movimiento, escanea el rostro y
registra la asistencia en la clase seleccionada."""

import customtkinter as ctk
from PIL import Image

from config.settings import CAMERA_HEIGHT, CAMERA_WIDTH, RESULT_DISPLAY_MS, SCAN_INTERVAL_MS
from core.camera import Camera
from core.motion_detector import MotionDetector
from gui.views.base_view import BaseView
from services.asistencia_service import AsistenciaService, ResultadoAsistencia
from services.clase_service import ClaseService

MENSAJES_RESULTADO = {
    ResultadoAsistencia.NO_IDENTIFICADO: "Usuario no identificado",
    ResultadoAsistencia.NO_INSCRITO: "El usuario no está inscrito en esta clase",
    ResultadoAsistencia.YA_REGISTRADO: "La asistencia ya fue registrada hoy",
    ResultadoAsistencia.REGISTRADO: "Asistencia registrada",
}


class AsistenciaView(BaseView):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.camera = Camera()
        self.motion_detector = MotionDetector()
        self.asistencia_service = AsistenciaService()
        self.clase_service = ClaseService()

        self._after_id: str | None = None
        self._mostrando_resultado = False
        self._clases_por_nombre: dict[str, int] = {}
        self.idClase: int | None = None

        self.label_titulo = ctk.CTkLabel(self, text="Control de Asistencia", font=ctk.CTkFont(size=20, weight="bold"))
        self.label_titulo.pack(pady=20)

        self.combo_clase = ctk.CTkComboBox(self, values=["Sin clases registradas"], command=self._on_clase_seleccionada)
        self.combo_clase.pack(pady=5, padx=20, fill="x")

        self.video_label = ctk.CTkLabel(self, text="")
        self.video_label.pack(pady=10, expand=True, fill="both")

        self.label_estado = ctk.CTkLabel(self, text="Selecciona una clase para iniciar", font=ctk.CTkFont(size=14))
        self.label_estado.pack(pady=10)

    # --- Ciclo de vida -----------------------------------------------------

    def on_show(self) -> None:
        self._cargar_clases()
        self.motion_detector.reset()
        self._mostrando_resultado = False
        self.camera.start()
        self._actualizar_frame()

    def on_hide(self) -> None:
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        self.camera.stop()

    # --- Selección de clase --------------------------------------------------

    def _cargar_clases(self) -> None:
        clases = self.clase_service.listar_clases()
        self._clases_por_nombre = {f"{c['nombreClase']} ({c['periodoClase']})": c["idClase"] for c in clases}

        valores = list(self._clases_por_nombre) or ["Sin clases registradas"]
        self.combo_clase.configure(values=valores)
        self.combo_clase.set(valores[0])
        self._on_clase_seleccionada(valores[0])

    def _on_clase_seleccionada(self, seleccion: str) -> None:
        self.idClase = self._clases_por_nombre.get(seleccion)
        if self.idClase is None:
            self.label_estado.configure(text="No hay clases registradas")
        else:
            self.label_estado.configure(text="Esperando movimiento...")

    # --- Captura y reconocimiento --------------------------------------------

    def _actualizar_frame(self) -> None:
        frame = self.camera.read_frame_rgb()
        if frame is not None:
            self._mostrar_frame(frame)

            if not self._mostrando_resultado and self.idClase is not None:
                if self.motion_detector.detecta_movimiento(frame):
                    self._procesar(frame)

        self._after_id = self.after(SCAN_INTERVAL_MS, self._actualizar_frame)

    def _mostrar_frame(self, frame_rgb) -> None:
        imagen = ctk.CTkImage(Image.fromarray(frame_rgb), size=(CAMERA_WIDTH, CAMERA_HEIGHT))
        self.video_label.configure(image=imagen, text="")

    def _procesar(self, frame_rgb) -> None:
        resultado, datos = self.asistencia_service.procesar_frame(frame_rgb, self.idClase)
        if resultado == ResultadoAsistencia.SIN_ROSTRO:
            return

        mensaje = MENSAJES_RESULTADO[resultado]
        if datos and datos.get("usuario"):
            usuario = datos["usuario"]
            mensaje += f": {usuario['nombre']} {usuario['apPaterno']}"

        self.label_estado.configure(text=mensaje)
        self._mostrando_resultado = True
        self._after_id = self.after(RESULT_DISPLAY_MS, self._reanudar_escaneo)

    def _reanudar_escaneo(self) -> None:
        self._mostrando_resultado = False
        self.motion_detector.reset()
        self.label_estado.configure(text="Esperando movimiento...")
        self._actualizar_frame()
