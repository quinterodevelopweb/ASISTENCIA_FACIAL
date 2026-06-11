"""Catálogo de usuarios: alta de usuarios, captura de rostro e inscripción a clases."""

import sqlite3

import customtkinter as ctk
from PIL import Image

from config.settings import CAMERA_HEIGHT, CAMERA_WIDTH, SCAN_INTERVAL_MS
from core.camera import Camera
from core.face_encoder import get_single_face_encoding
from gui.views.base_view import BaseView
from services.clase_service import ClaseService
from services.inscripcion_service import InscripcionService
from services.usuario_service import UsuarioService


class UsuariosView(BaseView):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.usuario_service = UsuarioService()
        self.clase_service = ClaseService()
        self.inscripcion_service = InscripcionService()

        self.camera = Camera()
        self._ctk_image: ctk.CTkImage | None = None
        self._after_id: str | None = None
        self._ultimo_frame = None
        self._encoding_capturado = None

        self._tipos_por_nombre: dict[str, int] = {}
        self._checks_clases: dict[int, ctk.BooleanVar] = {}

        self._construir_ui()

    def _construir_ui(self) -> None:
        contenedor = ctk.CTkScrollableFrame(self)
        contenedor.pack(expand=True, fill="both", padx=10, pady=10)

        ctk.CTkLabel(contenedor, text="Registro de Usuarios", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)

        self.combo_tipo = ctk.CTkComboBox(contenedor, values=["Cargando..."])
        self.combo_tipo.pack(pady=5, padx=20, fill="x")

        self.entry_no_cuenta = ctk.CTkEntry(contenedor, placeholder_text="No. de cuenta")
        self.entry_no_cuenta.pack(pady=5, padx=20, fill="x")

        self.entry_nombre = ctk.CTkEntry(contenedor, placeholder_text="Nombre")
        self.entry_nombre.pack(pady=5, padx=20, fill="x")

        self.entry_ap_paterno = ctk.CTkEntry(contenedor, placeholder_text="Apellido paterno")
        self.entry_ap_paterno.pack(pady=5, padx=20, fill="x")

        self.entry_ap_materno = ctk.CTkEntry(contenedor, placeholder_text="Apellido materno")
        self.entry_ap_materno.pack(pady=5, padx=20, fill="x")

        self.entry_email = ctk.CTkEntry(contenedor, placeholder_text="Email")
        self.entry_email.pack(pady=5, padx=20, fill="x")

        self.entry_telefono = ctk.CTkEntry(contenedor, placeholder_text="Teléfono")
        self.entry_telefono.pack(pady=5, padx=20, fill="x")

        ctk.CTkLabel(contenedor, text="Clases inscritas").pack(pady=(15, 5))
        self.frame_clases = ctk.CTkFrame(contenedor)
        self.frame_clases.pack(pady=5, padx=20, fill="x")

        ctk.CTkLabel(contenedor, text="Captura de rostro").pack(pady=(15, 5))
        self.video_label = ctk.CTkLabel(contenedor, text="")
        self.video_label.pack(pady=5)

        self.label_captura = ctk.CTkLabel(contenedor, text="Rostro no capturado")
        self.label_captura.pack(pady=5)

        ctk.CTkButton(contenedor, text="Capturar rostro", command=self._capturar_rostro).pack(pady=5)

        self.label_mensaje = ctk.CTkLabel(contenedor, text="")
        self.label_mensaje.pack(pady=5)

        ctk.CTkButton(contenedor, text="Guardar usuario", command=self._guardar_usuario).pack(pady=10)

        ctk.CTkLabel(contenedor, text="Usuarios registrados", font=ctk.CTkFont(size=16, weight="bold")).pack(
            pady=(20, 5)
        )
        self.frame_lista = ctk.CTkFrame(contenedor)
        self.frame_lista.pack(pady=5, padx=20, fill="x")

    # --- Ciclo de vida -----------------------------------------------------

    def on_show(self) -> None:
        self._cargar_tipos_usuario()
        self._cargar_clases()
        self._cargar_usuarios()
        self.camera.start()
        self._actualizar_frame()

    def on_hide(self) -> None:
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        self.camera.stop()

    # --- Carga de catálogos --------------------------------------------------

    def _cargar_tipos_usuario(self) -> None:
        tipos = self.usuario_service.listar_tipos_usuario()
        self._tipos_por_nombre = {t["nombreTipoUsuario"]: t["idTipoUsuario"] for t in tipos}

        valores = list(self._tipos_por_nombre) or ["Sin tipos registrados"]
        self.combo_tipo.configure(values=valores)
        self.combo_tipo.set(valores[0])

    def _cargar_clases(self) -> None:
        for widget in self.frame_clases.winfo_children():
            widget.destroy()
        self._checks_clases.clear()

        clases = self.clase_service.listar_clases()
        if not clases:
            ctk.CTkLabel(self.frame_clases, text="No hay clases registradas").pack(anchor="w", padx=10, pady=5)
            return

        for clase in clases:
            var = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(
                self.frame_clases,
                text=f"{clase['nombreClase']} ({clase['periodoClase']})",
                variable=var,
            ).pack(anchor="w", padx=10, pady=2)
            self._checks_clases[clase["idClase"]] = var

    def _cargar_usuarios(self) -> None:
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        usuarios = self.usuario_service.listar_usuarios()
        if not usuarios:
            ctk.CTkLabel(self.frame_lista, text="No hay usuarios registrados").pack(anchor="w", padx=10, pady=5)
            return

        for usuario in usuarios:
            apellidos = " ".join(filter(None, [usuario["apPaterno"], usuario["apMaterno"]]))
            texto = f"{usuario['nombre']} {apellidos} - {usuario['noCuenta'] or 's/n'}"
            ctk.CTkLabel(self.frame_lista, text=texto).pack(anchor="w", padx=10, pady=2)

    # --- Cámara y captura de rostro -------------------------------------------

    def _actualizar_frame(self) -> None:
        frame = self.camera.read_frame_rgb()
        if frame is not None:
            self._ultimo_frame = frame
            imagen_pil = Image.fromarray(frame)
            if self._ctk_image is None:
                self._ctk_image = ctk.CTkImage(imagen_pil, size=(CAMERA_WIDTH, CAMERA_HEIGHT))
                self.video_label.configure(image=self._ctk_image, text="")
            else:
                self._ctk_image.configure(light_image=imagen_pil)

        self._after_id = self.after(SCAN_INTERVAL_MS, self._actualizar_frame)

    def _capturar_rostro(self) -> None:
        if self._ultimo_frame is None:
            self.label_captura.configure(text="Cámara no disponible")
            return

        encoding = get_single_face_encoding(self._ultimo_frame)
        if encoding is None:
            self.label_captura.configure(text="No se detectó ningún rostro, intenta de nuevo")
            return

        self._encoding_capturado = encoding
        self.label_captura.configure(text="Rostro capturado correctamente")

    # --- Guardado --------------------------------------------------------------

    def _guardar_usuario(self) -> None:
        nombre = self.entry_nombre.get().strip()
        ap_paterno = self.entry_ap_paterno.get().strip()

        if not nombre or not ap_paterno:
            self.label_mensaje.configure(text="Nombre y apellido paterno son obligatorios", text_color="red")
            return

        if self._encoding_capturado is None:
            self.label_mensaje.configure(text="Captura el rostro del usuario antes de guardar", text_color="red")
            return

        idTipoUsuario = self._tipos_por_nombre.get(self.combo_tipo.get())
        if idTipoUsuario is None:
            self.label_mensaje.configure(text="Selecciona un tipo de usuario válido", text_color="red")
            return

        try:
            idUsuario = self.usuario_service.crear_usuario(
                tipoUsuario=idTipoUsuario,
                nombre=nombre,
                apPaterno=ap_paterno,
                apMaterno=self.entry_ap_materno.get().strip() or None,
                noCuenta=self.entry_no_cuenta.get().strip() or None,
                email=self.entry_email.get().strip() or None,
                telefono=self.entry_telefono.get().strip() or None,
            )
        except sqlite3.IntegrityError:
            self.label_mensaje.configure(text="Ya existe un usuario con ese número de cuenta", text_color="red")
            return

        self.usuario_service.guardar_encoding(idUsuario, self._encoding_capturado)

        for idClase, var in self._checks_clases.items():
            if var.get():
                self.inscripcion_service.inscribir(idUsuario, idClase)

        self.label_mensaje.configure(text=f"Usuario {nombre} {ap_paterno} guardado correctamente", text_color="green")
        self._limpiar_formulario()
        self._cargar_usuarios()

    def _limpiar_formulario(self) -> None:
        for entry in (
            self.entry_no_cuenta,
            self.entry_nombre,
            self.entry_ap_paterno,
            self.entry_ap_materno,
            self.entry_email,
            self.entry_telefono,
        ):
            entry.delete(0, "end")

        for var in self._checks_clases.values():
            var.set(False)

        self._encoding_capturado = None
        self.label_captura.configure(text="Rostro no capturado")
