"""Panel de administrador: catálogos y consultas (Usuarios, Clases, Reportes)."""

from typing import Callable

import customtkinter as ctk

from gui.views.base_view import BaseView
from gui.views.clases_view import ClasesView
from gui.views.reportes_view import ReportesView
from gui.views.usuarios_view import UsuariosView


class AdminPanel(BaseView):
    def __init__(self, master, on_salir: Callable[[], None], **kwargs):
        super().__init__(master, **kwargs)

        self.on_salir = on_salir
        self._vista_activa: str | None = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._crear_sidebar()
        self._crear_vistas()
        self._mostrar_vista("usuarios")

    def _crear_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=160, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(sidebar, text="Panel Administrador", font=ctk.CTkFont(size=14, weight="bold"), wraplength=140).pack(
            pady=20, padx=10
        )

        ctk.CTkButton(sidebar, text="Usuarios", command=lambda: self._mostrar_vista("usuarios")).pack(
            pady=5, padx=10, fill="x"
        )
        ctk.CTkButton(sidebar, text="Clases", command=lambda: self._mostrar_vista("clases")).pack(
            pady=5, padx=10, fill="x"
        )
        ctk.CTkButton(sidebar, text="Reportes", command=lambda: self._mostrar_vista("reportes")).pack(
            pady=5, padx=10, fill="x"
        )

        ctk.CTkButton(sidebar, text="Cerrar sesión", fg_color="transparent", border_width=1, command=self.on_salir).pack(
            side="bottom", pady=10, padx=10, fill="x"
        )

    def _crear_vistas(self) -> None:
        self.vistas: dict[str, BaseView] = {
            "usuarios": UsuariosView(self),
            "clases": ClasesView(self),
            "reportes": ReportesView(self),
        }
        for vista in self.vistas.values():
            vista.grid(row=0, column=1, sticky="nsew")

    def _mostrar_vista(self, nombre: str) -> None:
        if self._vista_activa is not None:
            self.vistas[self._vista_activa].on_hide()

        self._vista_activa = nombre
        vista = self.vistas[nombre]
        vista.tkraise()
        vista.on_show()

    # --- Ciclo de vida (llamado por App al cambiar de pantalla) ----------------

    def on_show(self) -> None:
        if self._vista_activa is not None:
            self.vistas[self._vista_activa].on_show()

    def on_hide(self) -> None:
        if self._vista_activa is not None:
            self.vistas[self._vista_activa].on_hide()
