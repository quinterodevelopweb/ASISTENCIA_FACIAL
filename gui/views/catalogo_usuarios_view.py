"""Catálogo de usuarios: listado y acceso a la edición de cada usuario."""

from typing import Callable

import customtkinter as ctk

from gui.views.base_view import BaseView
from gui.widgets.scrollable_table import ScrollableTable
from services.usuario_service import UsuarioService


class CatalogoUsuariosView(BaseView):
    def __init__(self, master, on_seleccionar: Callable[[int], None], **kwargs):
        super().__init__(master, **kwargs)

        self.usuario_service = UsuarioService()
        self.on_seleccionar = on_seleccionar

        self._construir_ui()

    def _construir_ui(self) -> None:
        self.frame_lista = ScrollableTable(self, label_text="Usuarios")
        self.frame_lista.pack(expand=True, fill="both", padx=10, pady=10)

    # --- Ciclo de vida -----------------------------------------------------

    def on_show(self) -> None:
        self.cargar_lista_usuarios()

    # --- Listado --------------------------------------------------------------

    def cargar_lista_usuarios(self) -> None:
        self.frame_lista.limpiar()

        usuarios = self.usuario_service.listar_usuarios(solo_activos=False)
        if not usuarios:
            ctk.CTkLabel(self.frame_lista.inner, text="No hay usuarios registrados").pack(anchor="w", padx=10, pady=5)
            return

        for usuario in usuarios:
            apellidos = " ".join(filter(None, [usuario["apPaterno"], usuario["apMaterno"]]))
            texto = f"{usuario['nombre']} {apellidos}"
            if not usuario["estado"]:
                texto += " (inactivo)"
            ctk.CTkButton(
                self.frame_lista.inner,
                text=texto,
                anchor="w",
                fg_color="transparent",
                text_color="gray60" if not usuario["estado"] else None,
                command=lambda idUsuario=usuario["idUsuario"]: self.on_seleccionar(idUsuario),
            ).pack(padx=5, pady=2, fill="x")
