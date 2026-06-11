"""Ventana principal de la aplicación: pantalla de Usuario (escaneo) y panel
de Administrador, protegido por contraseña."""

import customtkinter as ctk

from config.settings import ADMIN_PASSWORD, APP_COLOR_THEME, APP_THEME, APP_TITLE
from gui.views.admin_panel import AdminPanel
from gui.views.asistencia_view import AsistenciaView
from gui.widgets.password_dialog import PasswordDialog


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode(APP_THEME)
        ctk.set_default_color_theme(APP_COLOR_THEME)

        self.title(APP_TITLE)
        self.geometry("800x480")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._pantalla_activa: str | None = None

        self._crear_pantallas()
        self.mostrar_pantalla("usuario")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _crear_pantallas(self) -> None:
        self.pantallas = {
            "usuario": AsistenciaView(self, on_admin_click=self._solicitar_acceso_admin),
            "admin": AdminPanel(self, on_salir=lambda: self.mostrar_pantalla("usuario")),
        }
        for pantalla in self.pantallas.values():
            pantalla.grid(row=0, column=0, sticky="nsew")

    def mostrar_pantalla(self, nombre: str) -> None:
        if self._pantalla_activa is not None:
            self.pantallas[self._pantalla_activa].on_hide()

        self._pantalla_activa = nombre
        pantalla = self.pantallas[nombre]
        pantalla.tkraise()
        pantalla.on_show()

    def _solicitar_acceso_admin(self) -> None:
        password = PasswordDialog(self).pedir_password()
        if password is None:
            return
        if password == ADMIN_PASSWORD:
            self.mostrar_pantalla("admin")
        else:
            self.pantallas["usuario"].mostrar_mensaje_auth("Contraseña incorrecta")

    def _on_close(self) -> None:
        if self._pantalla_activa is not None:
            self.pantallas[self._pantalla_activa].on_hide()
        self.destroy()
