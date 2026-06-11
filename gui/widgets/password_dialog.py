"""Diálogo modal para solicitar la contraseña de administrador."""

import customtkinter as ctk


class PasswordDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Acceso Administrador")
        self.resizable(False, False)

        self.resultado: str | None = None

        ctk.CTkLabel(self, text="Contraseña de administrador:").pack(pady=(20, 5))

        self.entry = ctk.CTkEntry(self, show="*")
        self.entry.pack(pady=5, padx=20, fill="x")
        self.entry.bind("<Return>", lambda _e: self._aceptar())

        botones = ctk.CTkFrame(self, fg_color="transparent")
        botones.pack(pady=15)
        ctk.CTkButton(botones, text="Aceptar", command=self._aceptar).pack(side="left", padx=5)
        ctk.CTkButton(botones, text="Cancelar", command=self.destroy).pack(side="left", padx=5)

        self._centrar(master)

        self.transient(master)
        self.lift()
        self.attributes("-topmost", True)
        self.after(100, self._enfocar)
        self.grab_set()

    def _centrar(self, master) -> None:
        ancho, alto = 300, 150
        x = master.winfo_rootx() + (master.winfo_width() - ancho) // 2
        y = master.winfo_rooty() + (master.winfo_height() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    def _enfocar(self) -> None:
        self.lift()
        self.focus_force()
        self.entry.focus_set()

    def _aceptar(self) -> None:
        self.resultado = self.entry.get()
        self.destroy()

    def pedir_password(self) -> str | None:
        """Muestra el diálogo y bloquea hasta que el usuario acepte o cancele."""
        self.master.wait_window(self)
        return self.resultado
