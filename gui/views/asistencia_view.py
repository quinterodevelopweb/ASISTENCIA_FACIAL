"""Pantalla principal (modo Usuario): identifica al usuario por su rostro y,
si lo reconoce, le permite elegir su clase para registrar asistencia."""

import threading
import time
from typing import Callable

import cv2
import customtkinter as ctk
from PIL import Image

from config.settings import (
    APP_TITLE,
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
    RECOGNITION_INTERVAL_S,
    RECOGNITION_WIDTH,
    RESULT_DISPLAY_MS,
    SCAN_INTERVAL_MS,
)
from core.camera import Camera
from gui.views.base_view import BaseView
from services.asistencia_service import AsistenciaService, ResultadoAsistencia
from utils.logger import get_logger

logger = get_logger(__name__)

ESCANEANDO = "ESCANEANDO"
MOSTRANDO_RESULTADO = "MOSTRANDO_RESULTADO"
SELECCIONANDO_CLASE = "SELECCIONANDO_CLASE"


class AsistenciaView(BaseView):
    def __init__(self, master, on_admin_click: Callable[[], None], **kwargs):
        super().__init__(master, **kwargs)

        self.camera = Camera()
        self.asistencia_service = AsistenciaService()

        self._ctk_image: ctk.CTkImage | None = None
        self._after_id_frame: str | None = None
        self._after_id_resultado: str | None = None
        self._estado = ESCANEANDO
        self._usuario_actual: dict | None = None
        self._confianza_actual: float = 0.0
        self._ultimo_intento: float = 0.0

        # Recuadro que se dibuja sobre el rostro detectado (coordenadas del
        # frame mostrado) y su color, junto con la escala usada para
        # convertir las ubicaciones del frame reducido al frame completo.
        self._ultima_ubicacion: tuple[int, int, int, int] | None = None
        self._color_caja: tuple[int, int, int] = (0, 255, 0)
        self._escala_reconocimiento: float = 1.0

        # El reconocimiento facial se ejecuta en un hilo aparte para no
        # bloquear ni romper el ciclo de actualización de video de Tkinter.
        self._reconocimiento_lock = threading.Lock()
        self._reconociendo = False
        self._resultado_pendiente: tuple[str, dict | None] | None = None

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

        self.label_estado = ctk.CTkLabel(
            self, text="Colócate frente a la cámara para registrar tu asistencia", font=ctk.CTkFont(size=14)
        )
        self.label_estado.pack(pady=5)

        # Panel mostrado al identificar a un usuario: confirmación, sus datos
        # y la lista de clases en las que está inscrito para elegir una.
        self.panel_identificacion = ctk.CTkFrame(self)

        ctk.CTkLabel(
            self.panel_identificacion,
            text="Usuario identificado con éxito",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#2fa572",
        ).pack(pady=(10, 5))

        self.label_nombre_usuario = ctk.CTkLabel(
            self.panel_identificacion, text="", font=ctk.CTkFont(size=15, weight="bold")
        )
        self.label_nombre_usuario.pack(pady=2)

        self.label_cuenta_usuario = ctk.CTkLabel(self.panel_identificacion, text="", text_color="gray")
        self.label_cuenta_usuario.pack(pady=2)

        ctk.CTkLabel(self.panel_identificacion, text="Selecciona tu clase para registrar asistencia:").pack(
            pady=(10, 5)
        )

        self.frame_clases = ctk.CTkFrame(self.panel_identificacion, fg_color="transparent")
        self.frame_clases.pack(pady=(0, 10), padx=20, fill="x")

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
        self._ultimo_intento = 0.0
        self._ultima_ubicacion = None
        with self._reconocimiento_lock:
            self._resultado_pendiente = None
        self.panel_identificacion.pack_forget()
        self.label_estado.configure(text="Colócate frente a la cámara para registrar tu asistencia")
        if not self.label_estado.winfo_ismapped():
            self.label_estado.pack(pady=5)
        self._limpiar_botones_clases()

    def _actualizar_frame(self) -> None:
        frame = self.camera.read_frame_rgb()
        if frame is not None:
            self._mostrar_frame(frame)

            if self._estado == ESCANEANDO:
                ahora = time.monotonic()
                if not self._reconociendo and ahora - self._ultimo_intento >= RECOGNITION_INTERVAL_S:
                    self._ultimo_intento = ahora
                    self._lanzar_reconocimiento(frame)

        self._procesar_resultado_pendiente()
        self._after_id_frame = self.after(SCAN_INTERVAL_MS, self._actualizar_frame)

    def _mostrar_frame(self, frame_rgb) -> None:
        if self._ultima_ubicacion is not None:
            top, right, bottom, left = self._ultima_ubicacion
            cv2.rectangle(frame_rgb, (left, top), (right, bottom), self._color_caja, 2)

        imagen_pil = Image.fromarray(frame_rgb)
        if self._ctk_image is None:
            self._ctk_image = ctk.CTkImage(imagen_pil, size=(CAMERA_WIDTH, CAMERA_HEIGHT))
            self.video_label.configure(image=self._ctk_image, text="")
        else:
            self._ctk_image.configure(light_image=imagen_pil)

    # --- Reconocimiento (en hilo aparte) ---------------------------------------

    def _lanzar_reconocimiento(self, frame_rgb) -> None:
        height, width = frame_rgb.shape[:2]
        scale = RECOGNITION_WIDTH / width
        self._escala_reconocimiento = 1.0 / scale
        frame_pequeno = cv2.resize(frame_rgb, (RECOGNITION_WIDTH, int(height * scale)), interpolation=cv2.INTER_AREA)

        self._reconociendo = True

        def trabajo() -> None:
            try:
                resultado, datos = self.asistencia_service.identificar(frame_pequeno)
            except Exception:
                logger.exception("Error al identificar rostro")
                resultado, datos = ResultadoAsistencia.ERROR, None
            with self._reconocimiento_lock:
                self._resultado_pendiente = (resultado, datos)
            self._reconociendo = False

        threading.Thread(target=trabajo, daemon=True).start()

    def _procesar_resultado_pendiente(self) -> None:
        with self._reconocimiento_lock:
            pendiente = self._resultado_pendiente
            self._resultado_pendiente = None

        if pendiente is None or self._estado != ESCANEANDO:
            return

        resultado, datos = pendiente

        if datos is not None and datos.get("location") is not None:
            self._ultima_ubicacion = self._escalar_ubicacion(datos["location"])
            self._color_caja = (
                (0, 255, 0) if resultado == ResultadoAsistencia.IDENTIFICADO else (255, 140, 0)
            )
        else:
            self._ultima_ubicacion = None

        if resultado == ResultadoAsistencia.SIN_ROSTRO:
            self.label_estado.configure(text="Buscando rostro... acércate y mira a la cámara")
        elif resultado == ResultadoAsistencia.ERROR:
            self.label_estado.configure(text="Error al procesar el rostro, intenta de nuevo")
        elif resultado == ResultadoAsistencia.NO_IDENTIFICADO:
            self._mostrar_resultado_temporal("Rostro detectado, pero no coincide con ningún usuario registrado")
        elif resultado == ResultadoAsistencia.SIN_CLASES:
            usuario = datos["usuario"]
            self._mostrar_resultado_temporal(f"{usuario['nombre']}: no tienes clases asignadas")
        elif resultado == ResultadoAsistencia.IDENTIFICADO:
            self._mostrar_seleccion_clase(datos)

    def _escalar_ubicacion(self, location: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        top, right, bottom, left = location
        e = self._escala_reconocimiento
        return (int(top * e), int(right * e), int(bottom * e), int(left * e))

    # --- Resultados temporales -----------------------------------------------

    def _mostrar_resultado_temporal(self, mensaje: str) -> None:
        self._estado = MOSTRANDO_RESULTADO
        self.panel_identificacion.pack_forget()
        self._limpiar_botones_clases()
        if not self.label_estado.winfo_ismapped():
            self.label_estado.pack(pady=5)
        self.label_estado.configure(text=mensaje)
        self._after_id_resultado = self.after(RESULT_DISPLAY_MS, self._reset)

    # --- Selección de clase -----------------------------------------------------

    def _mostrar_seleccion_clase(self, datos: dict) -> None:
        self._estado = SELECCIONANDO_CLASE
        usuario = datos["usuario"]
        self._usuario_actual = usuario
        self._confianza_actual = datos["confianza"]

        apellidos = " ".join(filter(None, [usuario["apPaterno"], usuario["apMaterno"]]))
        self.label_nombre_usuario.configure(text=f"{usuario['nombre']} {apellidos}")
        self.label_cuenta_usuario.configure(text=f"No. de cuenta: {usuario['noCuenta'] or 'N/A'}")

        self._limpiar_botones_clases()
        for clase in datos["clases"]:
            ctk.CTkButton(
                self.frame_clases,
                text=f"{clase['nombreClase']} ({clase['periodoClase']})",
                command=lambda idClase=clase["idClase"]: self._registrar(idClase),
            ).pack(pady=2, fill="x")

        self.label_estado.pack_forget()
        self.panel_identificacion.pack(pady=10, padx=20, fill="x")

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
