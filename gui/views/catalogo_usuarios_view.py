"""Catálogo de usuarios: listado, edición de datos, inscripción a clases y
re-captura de rostro."""

import sqlite3
import tkinter.messagebox as messagebox

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


class CatalogoUsuariosView(BaseView):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.usuario_service = UsuarioService()
        self.clase_service = ClaseService()
        self.inscripcion_service = InscripcionService()

        self.camera = Camera()
        self._ctk_image: ctk.CTkImage | None = None
        self._after_id: str | None = None

        self._tipos_por_nombre: dict[str, int] = {}
        self._nombres_por_tipo: dict[int, str] = {}
        self._checks_clases: dict[int, ctk.BooleanVar] = {}
        self._idUsuario_actual: int | None = None
        self._estado_actual: int = 1

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._construir_ui()

    def _construir_ui(self) -> None:
        self.frame_lista = ctk.CTkScrollableFrame(self, label_text="Usuarios", width=220)
        self.frame_lista.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)

        self.frame_edicion = ctk.CTkScrollableFrame(self, label_text="Editar usuario")
        self.frame_edicion.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)

        self.label_sin_seleccion = ctk.CTkLabel(self.frame_edicion, text="Selecciona un usuario de la lista")
        self.label_sin_seleccion.pack(pady=20)

        self.combo_tipo = ctk.CTkComboBox(self.frame_edicion, values=["Cargando..."])
        self.entry_no_cuenta = ctk.CTkEntry(self.frame_edicion, placeholder_text="No. de cuenta")
        self.entry_nombre = ctk.CTkEntry(self.frame_edicion, placeholder_text="Nombre")
        self.entry_ap_paterno = ctk.CTkEntry(self.frame_edicion, placeholder_text="Apellido paterno")
        self.entry_ap_materno = ctk.CTkEntry(self.frame_edicion, placeholder_text="Apellido materno")
        self.entry_email = ctk.CTkEntry(self.frame_edicion, placeholder_text="Email")
        self.entry_telefono = ctk.CTkEntry(self.frame_edicion, placeholder_text="Teléfono")

        self.label_clases = ctk.CTkLabel(self.frame_edicion, text="Clases inscritas")
        self.frame_clases = ctk.CTkFrame(self.frame_edicion)

        self.label_rostro = ctk.CTkLabel(self.frame_edicion, text="Rostro", font=ctk.CTkFont(size=14, weight="bold"))
        self.video_label = ctk.CTkLabel(self.frame_edicion, text="")
        self.face_widget = FaceEnrollmentWidget(self.frame_edicion)
        self.btn_recapturar = ctk.CTkButton(
            self.frame_edicion, text="Volver a capturar rostro", command=self._iniciar_recaptura
        )

        self.label_mensaje = ctk.CTkLabel(self.frame_edicion, text="")
        self.btn_guardar = ctk.CTkButton(self.frame_edicion, text="Guardar cambios", command=self._guardar_cambios)

        self.frame_acciones = ctk.CTkFrame(self.frame_edicion, fg_color="transparent")
        self.btn_estado = ctk.CTkButton(self.frame_acciones, text="Desactivar usuario", command=self._toggle_estado)
        self.btn_estado.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.btn_eliminar = ctk.CTkButton(
            self.frame_acciones, text="Eliminar usuario", fg_color="#b3261e", hover_color="#8c1d17",
            command=self._eliminar_usuario,
        )
        self.btn_eliminar.pack(side="left", expand=True, fill="x", padx=(5, 0))

        # Orden en el que se muestran al seleccionar un usuario
        self._widgets_formulario = [
            self.combo_tipo,
            self.entry_no_cuenta,
            self.entry_nombre,
            self.entry_ap_paterno,
            self.entry_ap_materno,
            self.entry_email,
            self.entry_telefono,
            self.label_clases,
            self.frame_clases,
            self.label_rostro,
            self.video_label,
            self.face_widget,
            self.btn_recapturar,
            self.label_mensaje,
            self.btn_guardar,
            self.frame_acciones,
        ]

    # --- Ciclo de vida -----------------------------------------------------

    def on_show(self) -> None:
        self._cargar_tipos_usuario()
        self._cargar_lista_usuarios()
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
        self._nombres_por_tipo = {t["idTipoUsuario"]: t["nombreTipoUsuario"] for t in tipos}
        self.combo_tipo.configure(values=list(self._tipos_por_nombre) or ["Sin tipos registrados"])

    def _cargar_lista_usuarios(self) -> None:
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        usuarios = self.usuario_service.listar_usuarios(solo_activos=False)
        if not usuarios:
            ctk.CTkLabel(self.frame_lista, text="No hay usuarios registrados").pack(anchor="w", padx=10, pady=5)
            return

        for usuario in usuarios:
            apellidos = " ".join(filter(None, [usuario["apPaterno"], usuario["apMaterno"]]))
            texto = f"{usuario['nombre']} {apellidos}"
            if not usuario["estado"]:
                texto += " (inactivo)"
            ctk.CTkButton(
                self.frame_lista,
                text=texto,
                anchor="w",
                fg_color="transparent",
                text_color="gray60" if not usuario["estado"] else None,
                command=lambda idUsuario=usuario["idUsuario"]: self._seleccionar_usuario(idUsuario),
            ).pack(fill="x", padx=5, pady=2)

    # --- Selección y edición de usuario ----------------------------------------

    def _seleccionar_usuario(self, idUsuario: int) -> None:
        usuario = self.usuario_service.obtener_usuario(idUsuario)
        if usuario is None:
            return

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

        self._cargar_clases_checkboxes(idUsuario)
        self.face_widget.reset()
        self.label_mensaje.configure(text="")

        self.label_sin_seleccion.pack_forget()
        for widget in self._widgets_formulario:
            widget.pack(pady=5, padx=20, fill="x")

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
        self._cargar_lista_usuarios()

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
        self._cargar_lista_usuarios()

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
        self._ocultar_formulario()
        self._cargar_lista_usuarios()

    def _ocultar_formulario(self) -> None:
        for widget in self._widgets_formulario:
            widget.pack_forget()
        self.label_sin_seleccion.pack(pady=20)
