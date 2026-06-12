"""Catálogo de clases: listado, alta, edición, activación/desactivación y
eliminación."""

import tkinter.messagebox as messagebox

import customtkinter as ctk

from gui.views.base_view import BaseView
from services.clase_service import ClaseService


class ClasesView(BaseView):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.clase_service = ClaseService()
        self._idClase_actual: int | None = None
        self._estado_actual: int = 1

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._construir_ui()

    def _construir_ui(self) -> None:
        self.frame_lista = ctk.CTkScrollableFrame(self, label_text="Clases", width=220)
        self.frame_lista.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)

        self.frame_edicion = ctk.CTkScrollableFrame(self, label_text="Nueva clase")
        self.frame_edicion.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)

        ctk.CTkButton(self.frame_lista, text="+ Nueva clase", command=self._preparar_nueva_clase).pack(
            fill="x", padx=5, pady=(0, 10)
        )

        self.entry_nombre = ctk.CTkEntry(self.frame_edicion, placeholder_text="Nombre de la clase")
        self.entry_nombre.pack(pady=5, padx=20, fill="x")

        self.entry_periodo = ctk.CTkEntry(self.frame_edicion, placeholder_text="Periodo (ej. enero 2026 - junio 2026)")
        self.entry_periodo.pack(pady=5, padx=20, fill="x")

        self.label_mensaje = ctk.CTkLabel(self.frame_edicion, text="")
        self.label_mensaje.pack(pady=5)

        self.btn_guardar = ctk.CTkButton(self.frame_edicion, text="Guardar clase", command=self._guardar_clase)
        self.btn_guardar.pack(pady=10)

        self.frame_acciones = ctk.CTkFrame(self.frame_edicion, fg_color="transparent")
        self.btn_estado = ctk.CTkButton(self.frame_acciones, text="Desactivar clase", command=self._toggle_estado)
        self.btn_estado.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.btn_eliminar = ctk.CTkButton(
            self.frame_acciones, text="Eliminar clase", fg_color="#b3261e", hover_color="#8c1d17",
            command=self._eliminar_clase,
        )
        self.btn_eliminar.pack(side="left", expand=True, fill="x", padx=(5, 0))

    # --- Ciclo de vida -----------------------------------------------------

    def on_show(self) -> None:
        self._cargar_lista_clases()

    # --- Listado --------------------------------------------------------------

    def _cargar_lista_clases(self) -> None:
        # El primer hijo es el botón "+ Nueva clase" (se conserva); el resto
        # son los botones de clases de la carga anterior.
        for widget in self.frame_lista.winfo_children()[1:]:
            widget.destroy()

        clases = self.clase_service.listar_clases(solo_activas=False)
        if not clases:
            ctk.CTkLabel(self.frame_lista, text="No hay clases registradas").pack(anchor="w", padx=10, pady=5)
            return

        for clase in clases:
            texto = f"{clase['nombreClase']} ({clase['periodoClase']})"
            if not clase["estado"]:
                texto += " (inactiva)"
            ctk.CTkButton(
                self.frame_lista,
                text=texto,
                anchor="w",
                fg_color="transparent",
                text_color="gray60" if not clase["estado"] else None,
                command=lambda idClase=clase["idClase"]: self._seleccionar_clase(idClase),
            ).pack(fill="x", padx=5, pady=2)

    # --- Selección y edición -----------------------------------------------------

    def _preparar_nueva_clase(self) -> None:
        self._idClase_actual = None
        self.entry_nombre.delete(0, "end")
        self.entry_periodo.delete(0, "end")
        self.label_mensaje.configure(text="")
        self.frame_edicion.configure(label_text="Nueva clase")
        self.btn_guardar.configure(text="Guardar clase")
        self.frame_acciones.pack_forget()

    def _seleccionar_clase(self, idClase: int) -> None:
        clase = self.clase_service.obtener_clase(idClase)
        if clase is None:
            return

        self._idClase_actual = idClase
        self._estado_actual = clase["estado"]

        self.entry_nombre.delete(0, "end")
        self.entry_nombre.insert(0, clase["nombreClase"])
        self.entry_periodo.delete(0, "end")
        self.entry_periodo.insert(0, clase["periodoClase"])
        self.label_mensaje.configure(text="")

        self.frame_edicion.configure(label_text="Editar clase")
        self.btn_guardar.configure(text="Guardar cambios")
        self._actualizar_boton_estado()
        self.frame_acciones.pack(pady=(0, 10), fill="x")

    # --- Guardado --------------------------------------------------------------

    def _guardar_clase(self) -> None:
        nombre = self.entry_nombre.get().strip()
        periodo = self.entry_periodo.get().strip()

        if not nombre or not periodo:
            self.label_mensaje.configure(text="Nombre y periodo son obligatorios", text_color="red")
            return

        if self._idClase_actual is None:
            self.clase_service.crear_clase(nombre, periodo)
            self.label_mensaje.configure(text=f"Clase '{nombre}' guardada correctamente", text_color="green")
            self._preparar_nueva_clase()
        else:
            self.clase_service.actualizar_clase(self._idClase_actual, nombreClase=nombre, periodoClase=periodo)
            self.label_mensaje.configure(text="Clase actualizada correctamente", text_color="green")

        self._cargar_lista_clases()

    # --- Estado y eliminación ---------------------------------------------------

    def _actualizar_boton_estado(self) -> None:
        if self._estado_actual:
            self.btn_estado.configure(
                text="Desactivar clase", fg_color=["#3a7ebf", "#1f538d"], hover_color=["#325882", "#14375e"]
            )
        else:
            self.btn_estado.configure(text="Activar clase", fg_color="#2fa572", hover_color="#218358")

    def _toggle_estado(self) -> None:
        if self._idClase_actual is None:
            return

        if self._estado_actual:
            self.clase_service.desactivar_clase(self._idClase_actual)
            self._estado_actual = 0
            self.label_mensaje.configure(text="Clase desactivada", text_color="green")
        else:
            self.clase_service.activar_clase(self._idClase_actual)
            self._estado_actual = 1
            self.label_mensaje.configure(text="Clase activada", text_color="green")

        self._actualizar_boton_estado()
        self._cargar_lista_clases()

    def _eliminar_clase(self) -> None:
        if self._idClase_actual is None:
            return

        nombre = f"{self.entry_nombre.get().strip()} ({self.entry_periodo.get().strip()})"
        if not messagebox.askyesno(
            "Eliminar clase",
            f"¿Eliminar permanentemente la clase {nombre}?\n"
            "Se borrarán también las inscripciones de alumnos y profesores y su\n"
            "historial de asistencia en esta clase.\n"
            "Esta acción no se puede deshacer.",
        ):
            return

        self.clase_service.eliminar_clase(self._idClase_actual)
        self._preparar_nueva_clase()
        self._cargar_lista_clases()
