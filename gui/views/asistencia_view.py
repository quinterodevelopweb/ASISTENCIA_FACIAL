"""Pantalla principal (modo Usuario): detecta movimiento, identifica al usuario
por su rostro y, si lo reconoce, le permite elegir su clase para registrar
asistencia."""

from typing import Callable

import customtkinter as ctk
from PIL import Image

from config.settings import APP_TITLE, CAMERA_HEIGHT, CAMERA_WIDTH, RESULT_DISPLAY_MS, SCAN_INTERVAL_MS
from core.camera import Camera
from core.motion_detector import MotionDetector
from gui.views.base_view import BaseView
from services.asistencia_service import AsistenciaService, ResultadoAsistencia

ESCANEANDO = "ESCANEANDO"
MOSTRANDO_RESULTADO = "MOSTRANDO_RESULTADO"
SELECCIONANDO_CLASE = "SELECCIONANDO_CLASE"


class AsistenciaView(BaseView):
    def __init__(self, master, on_admin_click: Callable[[], None], **kwargs):
        super().__init__(master, **kwargs)

        self.camera = Camera()
        self.motion_detector = MotionDetector()
        self.asistencia_service = AsistenciaService()

        self._after_id_frame: str | None = None
        self._after_id_resultado: str | None = None
        self._estado = ESCANEANDO
        self._usuario_actual: dict | None = None
        self._confianza_actual: float = 0.0

        self._construir_ui(on_admin_click)

    def _construir_ui(self, on_admin_click: Callable[[], None]) -> None:
        barra_superior = ctk.CTkFrame(self, fg_color="transparent")
        barra_superior.pack(fill="x")

        self.label_auth = ctk.CTkLabel(barra_superior, text="", text_color="red")
        self.label_auth.pack(side="left", padx=10, pady=5)

        ctk.CTkButton(barra_superior, text="Administrador", width=120, command=on_admin_click).pack(
            side="right", padx=10, pady=5
        )

        ctk.CTkLabel(self, text=APP_TITLE, font=ctk.CTkFont(size=20, weight="bold")).pack(pady=5)

        self.video_label = ctk.CTkLabel(self, text="")
        self.video_label.pack(pady=5, expand=True, fill="both")

        self.label_estado = ctk.CTkLabel(self, text="Esperando movimiento...", font=ctk.CTkFont(size=14))
        self.label_estado.pack(pady=5)

        self.frame_clases = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_clases.pack(pady=5, padx=20, fill="x")

    # --- Ciclo de vida -----------------------------------------------------

    def on_show(self) -> None:
        self._reset()
        self.camera.start()
        self._actualizar_frame()

    def on_hide(self) -> None:
        if self._after_id_frame is not None:
            self.after_cancel(self._after_id_frame)
            self._after_id_frame = None
        if self._after_id_resultado is not None:
            self.after_cancel(self._after_id_resultado)
            self._after_id_resultado = None
        self.camera.stop()

    # --- Mensajes de autenticación -------------------------------------------

    def mostrar_mensaje_auth(self, mensaje: str) -> None:
        self.label_auth.configure(text=mensaje)
        self.after(RESULT_DISPLAY_MS, lambda: self.label_auth.configure(text=""))

    # --- Estado / escaneo ------------------------------------------------------

    def _reset(self) -> None:
        self._estado = ESCANEANDO
        self._usuario_actual = None
        self.motion_detector.reset()
        self.label_estado.configure(text="Esperando movimiento...")
        self._limpiar_botones_clases()

    def _actualizar_frame(self) -> None:
        frame = self.camera.read_frame_rgb()
        if frame is not None:
            self._mostrar_frame(frame)

            if self._estado == ESCANEANDO and self.motion_detector.detecta_movimiento(frame):
                self._procesar(frame)

        self._after_id_frame = self.after(SCAN_INTERVAL_MS, self._actualizar_frame)

    def _mostrar_frame(self, frame_rgb) -> None:
        imagen = ctk.CTkImage(Image.fromarray(frame_rgb), size=(CAMERA_WIDTH, CAMERA_HEIGHT))
        self.video_label.configure(image=imagen, text="")

    def _procesar(self, frame_rgb) -> None:
        resultado, datos = self.asistencia_service.identificar(frame_rgb)

        if resultado == ResultadoAsistencia.SIN_ROSTRO:
            return

        if resultado == ResultadoAsistencia.NO_IDENTIFICADO:
            self._mostrar_resultado_temporal("Usuario no identificado")
        elif resultado == ResultadoAsistencia.SIN_CLASES:
            usuario = datos["usuario"]
            self._mostrar_resultado_temporal(f"{usuario['nombre']}: no tienes clases asignadas")
        elif resultado == ResultadoAsistencia.IDENTIFICADO:
            self._mostrar_seleccion_clase(datos)

    # --- Resultados temporales -----------------------------------------------

    def _mostrar_resultado_temporal(self, mensaje: str) -> None:
        self._estado = MOSTRANDO_RESULTADO
        self.label_estado.configure(text=mensaje)
        self._after_id_resultado = self.after(RESULT_DISPLAY_MS, self._reset)

    # --- Selección de clase -----------------------------------------------------

    def _mostrar_seleccion_clase(self, datos: dict) -> None:
        self._estado = SELECCIONANDO_CLASE
        usuario = datos["usuario"]
        self._usuario_actual = usuario
        self._confianza_actual = datos["confianza"]

        self.label_estado.configure(text=f"Hola {usuario['nombre']}, selecciona tu clase:")

        for clase in datos["clases"]:
            ctk.CTkButton(
                self.frame_clases,
                text=f"{clase['nombreClase']} ({clase['periodoClase']})",
                command=lambda idClase=clase["idClase"]: self._registrar(idClase),
            ).pack(pady=2, fill="x")

    def _registrar(self, idClase: int) -> None:
        resultado = self.asistencia_service.registrar_asistencia(
            self._usuario_actual["idUsuario"], idClase, self._confianza_actual
        )
        mensaje = (
            "Asistencia registrada"
            if resultado == ResultadoAsistencia.REGISTRADO
            else "La asistencia ya fue registrada hoy"
        )
        self._limpiar_botones_clases()
        self._mostrar_resultado_temporal(mensaje)

    def _limpiar_botones_clases(self) -> None:
        for widget in self.frame_clases.winfo_children():
            widget.destroy()
