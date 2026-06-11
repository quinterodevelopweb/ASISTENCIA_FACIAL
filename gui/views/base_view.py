"""Clase base para las vistas de la aplicación."""

import customtkinter as ctk


class BaseView(ctk.CTkFrame):
    """Vista con hooks de ciclo de vida llamados por App al cambiar de vista."""

    def on_show(self) -> None:
        """Se llama cuando la vista se vuelve visible."""

    def on_hide(self) -> None:
        """Se llama cuando la vista deja de ser visible."""
