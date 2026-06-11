"""Catálogo de clases (alta y listado)."""

import customtkinter as ctk

from gui.views.base_view import BaseView
from services.clase_service import ClaseService


class ClasesView(BaseView):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.clase_service = ClaseService()

        ctk.CTkLabel(self, text="Catálogo de Clases", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)

        self.entry_nombre = ctk.CTkEntry(self, placeholder_text="Nombre de la clase")
        self.entry_nombre.pack(pady=5, padx=20, fill="x")

        self.entry_periodo = ctk.CTkEntry(self, placeholder_text="Periodo (ej. 2026-1)")
        self.entry_periodo.pack(pady=5, padx=20, fill="x")

        self.label_mensaje = ctk.CTkLabel(self, text="")
        self.label_mensaje.pack(pady=5)

        ctk.CTkButton(self, text="Guardar clase", command=self._guardar_clase).pack(pady=10)

        ctk.CTkLabel(self, text="Clases registradas", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        self.frame_lista = ctk.CTkScrollableFrame(self)
        self.frame_lista.pack(pady=5, padx=20, expand=True, fill="both")

    def on_show(self) -> None:
        self._cargar_clases()

    def _cargar_clases(self) -> None:
        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        clases = self.clase_service.listar_clases()
        if not clases:
            ctk.CTkLabel(self.frame_lista, text="No hay clases registradas").pack(anchor="w", padx=10, pady=5)
            return

        for clase in clases:
            ctk.CTkLabel(self.frame_lista, text=f"{clase['nombreClase']} ({clase['periodoClase']})").pack(
                anchor="w", padx=10, pady=2
            )

    def _guardar_clase(self) -> None:
        nombre = self.entry_nombre.get().strip()
        periodo = self.entry_periodo.get().strip()

        if not nombre or not periodo:
            self.label_mensaje.configure(text="Nombre y periodo son obligatorios", text_color="red")
            return

        self.clase_service.crear_clase(nombre, periodo)
        self.label_mensaje.configure(text=f"Clase '{nombre}' guardada correctamente", text_color="green")

        self.entry_nombre.delete(0, "end")
        self.entry_periodo.delete(0, "end")
        self._cargar_clases()
