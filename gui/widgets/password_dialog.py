"""Diálogo modal para solicitar la contraseña de administrador."""

import customtkinter as ctk


class PasswordDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Acceso Administrador")
        self.geometry("300x150")
        self.resizable(False, False)

        self.resultado: str | None = None

        ctk.CTkLabel(self, text="Contraseña de administrador:").pack(pady=(20, 5))

        self.entry = ctk.CTkEntry(self, show="*")
        self.entry.pack(pady=5, padx=20, fill="x")
        self.entry.bind("<Return>", lambda _e: self._aceptar())
        self.entry.focus()

        botones = ctk.CTkFrame(self, fg_color="transparent")
        botones.pack(pady=15)
        ctk.CTkButton(botones, text="Aceptar", command=self._aceptar).pack(side="left", padx=5)
        ctk.CTkButton(botones, text="Cancelar", command=self.destroy).pack(side="left", padx=5)

        self.transient(master)
        self.grab_set()

    def _aceptar(self) -> None:
        self.resultado = self.entry.get()
        self.destroy()

    def pedir_password(self) -> str | None:
        """Muestra el diálogo y bloquea hasta que el usuario acepte o cancele."""
        self.master.wait_window(self)
        return self.resultado
