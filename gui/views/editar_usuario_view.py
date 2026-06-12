"""Edición de un usuario existente: datos, inscripción a clases y re-captura
de rostro."""

import sqlite3
import tkinter.messagebox as messagebox
from typing import Callable

import cv2
import customtkinter as ctk
from PIL import Image

from config.settings import CAMERA_HEIGHT, CAMERA_WIDTH, RECOGNITION_WIDTH, SCAN_INTERVAL_MS
from core.camera import Camera
from gui.views.base_view import BaseView
from gui.widgets.face_enrollment_widget import FaceEnrollmentWidget
from services.clase_service import ClaseService
from services.inscripcion_service import InscripcionService
from services.usuario_service import UsuarioService


class EditarUsuarioView(BaseView):
    def __init__(self, master, on_volver: Callable[[], None], **kwargs):
        super().__init__(master, **kwargs)

        self.usuario_service = UsuarioService()
        self.clase_service = ClaseService()
        self.inscripcion_service = InscripcionService()

        self.on_volver = on_volver

        self.camera = Camera()
        self._ctk_image: ctk.CTkImage | None = None
        self._after_id: str | None = None

        self._tipos_por_nombre: dict[str, int] = {}
        self._nombres_por_tipo: dict[int, str] = {}
        self._checks_clases: dict[int, ctk.BooleanVar] = {}
        self._idUsuario_actual: int | None = None
        self._estado_actual: int = 1

        self._construir_ui()

    def _construir_ui(self) -> None:
        contenedor = ctk.CTkScrollableFrame(self)
        contenedor.pack(expand=True, fill="both", padx=10, pady=10)

        ctk.CTkButton(
            contenedor, text="< Volver al catálogo", anchor="w",
            fg_color="transparent", border_width=1, command=self.on_volver,
        ).pack(pady=(0, 10), padx=20, fill="x")

        ctk.CTkLabel(contenedor, text="Editar Usuario", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)

        self.combo_tipo = ctk.CTkComboBox(contenedor, values=["Cargando..."], command=self._on_tipo_cambiado)
        self.entry_no_cuenta = ctk.CTkEntry(contenedor, placeholder_text="No. de cuenta")
        self.entry_nombre = ctk.CTkEntry(contenedor, placeholder_text="Nombre")
        self.entry_ap_paterno = ctk.CTkEntry(contenedor, placeholder_text="Apellido paterno")
        self.entry_ap_materno = ctk.CTkEntry(contenedor, placeholder_text="Apellido materno")
        self.entry_email = ctk.CTkEntry(contenedor, placeholder_text="Email")
        self.entry_telefono = ctk.CTkEntry(contenedor, placeholder_text="Teléfono")

        # Solo se muestra cuando el tipo de usuario es "Profesor": contraseña de
        # acceso al panel de Profesor (junto con el no. de cuenta).
        self.entry_password = ctk.CTkEntry(
            contenedor, placeholder_text="Contraseña del panel de Profesor", show="*"
        )

        self.label_clases = ctk.CTkLabel(contenedor, text="Clases inscritas")
        self.frame_clases = ctk.CTkFrame(contenedor)

        self.label_rostro = ctk.CTkLabel(contenedor, text="Rostro", font=ctk.CTkFont(size=14, weight="bold"))
        self.video_label = ctk.CTkLabel(contenedor, text="")
        self.face_widget = FaceEnrollmentWidget(contenedor)
        self.btn_recapturar = ctk.CTkButton(
            contenedor, text="Volver a capturar rostro", command=self._iniciar_recaptura
        )

        self.label_mensaje = ctk.CTkLabel(contenedor, text="")
        self.btn_guardar = ctk.CTkButton(contenedor, text="Guardar cambios", command=self._guardar_cambios)

        self.frame_acciones = ctk.CTkFrame(contenedor, fg_color="transparent")
        self.btn_estado = ctk.CTkButton(self.frame_acciones, text="Desactivar usuario", command=self._toggle_estado)
        self.btn_estado.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.btn_eliminar = ctk.CTkButton(
            self.frame_acciones, text="Eliminar usuario", fg_color="#b3261e", hover_color="#8c1d17",
            command=self._eliminar_usuario,
        )
        self.btn_eliminar.pack(side="left", expand=True, fill="x", padx=(5, 0))

        # Orden visual del formulario; entry_password solo se incluye cuando
        # el tipo de usuario seleccionado es "Profesor" (ver _repack_formulario).
        self._widgets_orden = [
            (self.combo_tipo, {"pady": 5, "padx": 20, "fill": "x"}),
            (self.entry_no_cuenta, {"pady": 5, "padx": 20, "fill": "x"}),
            (self.entry_nombre, {"pady": 5, "padx": 20, "fill": "x"}),
            (self.entry_ap_paterno, {"pady": 5, "padx": 20, "fill": "x"}),
            (self.entry_ap_materno, {"pady": 5, "padx": 20, "fill": "x"}),
            (self.entry_email, {"pady": 5, "padx": 20, "fill": "x"}),
            (self.entry_telefono, {"pady": 5, "padx": 20, "fill": "x"}),
            (self.entry_password, {"pady": 5, "padx": 20, "fill": "x"}),
            (self.label_clases, {"pady": (15, 5)}),
            (self.frame_clases, {"pady": 5, "padx": 20, "fill": "x"}),
            (self.label_rostro, {"pady": (15, 5)}),
            (self.video_label, {"pady": 5}),
            (self.face_widget, {"pady": 5, "padx": 20, "fill": "x"}),
            (self.btn_recapturar, {"pady": 5}),
            (self.label_mensaje, {"pady": 5}),
            (self.btn_guardar, {"pady": 10}),
            (self.frame_acciones, {"pady": (0, 10), "padx": 20, "fill": "x"}),
        ]
        self._repack_formulario()

    def _repack_formulario(self) -> None:
        es_profesor = self.combo_tipo.get() == "Profesor"
        for widget, pack_kwargs in self._widgets_orden:
            widget.pack_forget()
            if widget is self.entry_password and not es_profesor:
                continue
            widget.pack(**pack_kwargs)

    def _on_tipo_cambiado(self, _seleccion: str) -> None:
        if self._idUsuario_actual is None:
            return
        if self.combo_tipo.get() != "Profesor":
            self.entry_password.delete(0, "end")
        self._repack_formulario()

    # --- Ciclo de vida -----------------------------------------------------

    def on_show(self) -> None:
        self.camera.start()
        self._actualizar_frame()

    def on_hide(self) -> None:
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        self.camera.stop()

    # --- Carga del usuario seleccionado -----------------------------------------

    def cargar_usuario(self, idUsuario: int) -> None:
        usuario = self.usuario_service.obtener_usuario(idUsuario)
        if usuario is None:
            return

        self._cargar_tipos_usuario()

        self._idUsuario_actual = idUsuario
        self._estado_actual = usuario["estado"]
        self._actualizar_boton_estado()

        self.combo_tipo.set(self._nombres_por_tipo.get(usuario["tipoUsuario"], ""))
        self._set_entry(self.entry_no_cuenta, usuario["noCuenta"])
        self._set_entry(self.entry_nombre, usuario["nombre"])
        self._set_entry(self.entry_ap_paterno, usuario["apPaterno"])
        self._set_entry(self.entry_ap_materno, usuario["apMaterno"])
        self._set_entry(self.entry_email, usuario["email"])
        self._set_entry(self.entry_telefono, usuario["telefono"])
        self._set_entry(self.entry_password, usuario["password"])

        self._cargar_clases_checkboxes(idUsuario)
        self.face_widget.reset()
        self.label_mensaje.configure(text="")
        self._repack_formulario()

    def _cargar_tipos_usuario(self) -> None:
        tipos = self.usuario_service.listar_tipos_usuario()
        self._tipos_por_nombre = {t["nombreTipoUsuario"]: t["idTipoUsuario"] for t in tipos}
        self._nombres_por_tipo = {t["idTipoUsuario"]: t["nombreTipoUsuario"] for t in tipos}
        self.combo_tipo.configure(values=list(self._tipos_por_nombre) or ["Sin tipos registrados"])

    @staticmethod
    def _set_entry(entry: ctk.CTkEntry, valor) -> None:
        entry.delete(0, "end")
        if valor:
            entry.insert(0, valor)

    def _cargar_clases_checkboxes(self, idUsuario: int) -> None:
        for widget in self.frame_clases.winfo_children():
            widget.destroy()
        self._checks_clases.clear()

        clases = self.clase_service.listar_clases()
        if not clases:
            ctk.CTkLabel(self.frame_clases, text="No hay clases registradas").pack(anchor="w", padx=10, pady=5)
            return

        idsInscritas = {c["idClase"] for c in self.inscripcion_service.listar_clases_de_usuario(idUsuario)}

        for clase in clases:
            var = ctk.BooleanVar(value=clase["idClase"] in idsInscritas)
            ctk.CTkCheckBox(
                self.frame_clases,
                text=f"{clase['nombreClase']} ({clase['periodoClase']})",
                variable=var,
            ).pack(anchor="w", padx=10, pady=2)
            self._checks_clases[clase["idClase"]] = var

    # --- Cámara y re-captura de rostro -----------------------------------------

    def _actualizar_frame(self) -> None:
        frame = self.camera.read_frame_rgb()
        if frame is not None:
            imagen_pil = Image.fromarray(frame)
            if self._ctk_image is None:
                self._ctk_image = ctk.CTkImage(imagen_pil, size=(CAMERA_WIDTH, CAMERA_HEIGHT))
                self.video_label.configure(image=self._ctk_image, text="")
            else:
                self._ctk_image.configure(light_image=imagen_pil)

            height, width = frame.shape[:2]
            scale = RECOGNITION_WIDTH / width
            frame_pequeno = cv2.resize(frame, (RECOGNITION_WIDTH, int(height * scale)), interpolation=cv2.INTER_AREA)
            self.face_widget.procesar_frame(frame_pequeno)

        self._after_id = self.after(SCAN_INTERVAL_MS, self._actualizar_frame)

    def _iniciar_recaptura(self) -> None:
        self.face_widget.iniciar()

    # --- Guardado --------------------------------------------------------------

    def _guardar_cambios(self) -> None:
        if self._idUsuario_actual is None:
            return

        nombre = self.entry_nombre.get().strip()
        ap_paterno = self.entry_ap_paterno.get().strip()

        if not nombre or not ap_paterno:
            self.label_mensaje.configure(text="Nombre y apellido paterno son obligatorios", text_color="red")
            return

        idTipoUsuario = self._tipos_por_nombre.get(self.combo_tipo.get())
        if idTipoUsuario is None:
            self.label_mensaje.configure(text="Selecciona un tipo de usuario válido", text_color="red")
            return

        password = self.entry_password.get().strip() or None
        if self.combo_tipo.get() == "Profesor" and (not self.entry_no_cuenta.get().strip() or not password):
            self.label_mensaje.configure(
                text="Captura no. de cuenta y contraseña para el panel de Profesor", text_color="red"
            )
            return

        if self.face_widget.esta_completo():
            usuario_duplicado = self.usuario_service.buscar_usuario_por_rostro(
                self.face_widget.obtener_encodings(), excluir_idUsuario=self._idUsuario_actual
            )
            if usuario_duplicado is not None:
                nombre_dup = f"{usuario_duplicado['nombre']} {usuario_duplicado['apPaterno']}"
                self.label_mensaje.configure(
                    text=f"Este rostro ya está registrado para {nombre_dup}", text_color="red"
                )
                return

        try:
            self.usuario_service.actualizar_usuario(
                self._idUsuario_actual,
                tipoUsuario=idTipoUsuario,
                noCuenta=self.entry_no_cuenta.get().strip() or None,
                nombre=nombre,
                apPaterno=ap_paterno,
                apMaterno=self.entry_ap_materno.get().strip() or None,
                email=self.entry_email.get().strip() or None,
                telefono=self.entry_telefono.get().strip() or None,
                password=password if self.combo_tipo.get() == "Profesor" else None,
            )
        except sqlite3.IntegrityError:
            self.label_mensaje.configure(text="Ya existe un usuario con ese número de cuenta", text_color="red")
            return

        for idClase, var in self._checks_clases.items():
            inscrito = self.inscripcion_service.esta_inscrito(self._idUsuario_actual, idClase)
            if var.get() and not inscrito:
                self.inscripcion_service.inscribir(self._idUsuario_actual, idClase)
            elif not var.get() and inscrito:
                self.inscripcion_service.desinscribir(self._idUsuario_actual, idClase)

        if self.face_widget.esta_completo():
            self.usuario_service.reemplazar_encodings(self._idUsuario_actual, self.face_widget.obtener_encodings())
            self.face_widget.reset()

        self.label_mensaje.configure(text="Usuario actualizado correctamente", text_color="green")

    # --- Estado y eliminación ---------------------------------------------------

    def _actualizar_boton_estado(self) -> None:
        if self._estado_actual:
            self.btn_estado.configure(text="Desactivar usuario", fg_color=["#3a7ebf", "#1f538d"], hover_color=["#325882", "#14375e"])
        else:
            self.btn_estado.configure(text="Activar usuario", fg_color="#2fa572", hover_color="#218358")

    def _toggle_estado(self) -> None:
        if self._idUsuario_actual is None:
            return

        if self._estado_actual:
            self.usuario_service.desactivar_usuario(self._idUsuario_actual)
            self._estado_actual = 0
            self.label_mensaje.configure(text="Usuario desactivado", text_color="green")
        else:
            self.usuario_service.activar_usuario(self._idUsuario_actual)
            self._estado_actual = 1
            self.label_mensaje.configure(text="Usuario activado", text_color="green")

        self._actualizar_boton_estado()

    def _eliminar_usuario(self) -> None:
        if self._idUsuario_actual is None:
            return

        nombre = f"{self.entry_nombre.get().strip()} {self.entry_ap_paterno.get().strip()}"
        if not messagebox.askyesno(
            "Eliminar usuario",
            f"¿Eliminar permanentemente a {nombre}?\n"
            "Se borrarán también su rostro registrado, sus inscripciones y su historial de asistencia.\n"
            "Esta acción no se puede deshacer.",
        ):
            return

        self.usuario_service.eliminar_usuario(self._idUsuario_actual)
        self._idUsuario_actual = None
        self.face_widget.reset()
        self.on_volver()
