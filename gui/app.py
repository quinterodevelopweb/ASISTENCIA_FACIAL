"""Ventana principal de la aplicación: navegación entre vistas."""

import customtkinter as ctk

from config.settings import APP_COLOR_THEME, APP_THEME, APP_TITLE
from gui.views.asistencia_view import AsistenciaView
from gui.views.clases_view import ClasesView
from gui.views.reportes_view import ReportesView
from gui.views.usuarios_view import UsuariosView


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode(APP_THEME)
        ctk.set_default_color_theme(APP_COLOR_THEME)

        self.title(APP_TITLE)
        self.geometry("800x480")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._vista_activa: str | None = None

        self._crear_sidebar()
        self._crear_vistas()
        self.mostrar_vista("asistencia")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _crear_sidebar(self) -> None:
        self.sidebar = ctk.CTkFrame(self, width=160, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar, text=APP_TITLE, font=ctk.CTkFont(size=14, weight="bold"), wraplength=140).pack(
            pady=20, padx=10
        )

        ctk.CTkButton(self.sidebar, text="Asistencia", command=lambda: self.mostrar_vista("asistencia")).pack(
            pady=5, padx=10, fill="x"
        )
        ctk.CTkButton(self.sidebar, text="Usuarios", command=lambda: self.mostrar_vista("usuarios")).pack(
            pady=5, padx=10, fill="x"
        )
        ctk.CTkButton(self.sidebar, text="Clases", command=lambda: self.mostrar_vista("clases")).pack(
            pady=5, padx=10, fill="x"
        )
        ctk.CTkButton(self.sidebar, text="Reportes", command=lambda: self.mostrar_vista("reportes")).pack(
            pady=5, padx=10, fill="x"
        )

    def _crear_vistas(self) -> None:
        self.vistas = {
            "asistencia": AsistenciaView(self),
            "usuarios": UsuariosView(self),
            "clases": ClasesView(self),
            "reportes": ReportesView(self),
        }
        for vista in self.vistas.values():
            vista.grid(row=0, column=1, sticky="nsew")

    def mostrar_vista(self, nombre: str) -> None:
        if self._vista_activa is not None:
            self.vistas[self._vista_activa].on_hide()

        self._vista_activa = nombre
        vista = self.vistas[nombre]
        vista.tkraise()
        vista.on_show()

    def _on_close(self) -> None:
        if self._vista_activa is not None:
            self.vistas[self._vista_activa].on_hide()
        self.destroy()
