"""Contenedor con scroll vertical y horizontal para tablas de texto (filas de
registros) que pueden ser más anchas que la pantalla."""

import tkinter

import customtkinter as ctk


class ScrollableTable(ctk.CTkFrame):
    def __init__(self, master, label_text: str | None = None, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)

        fila_canvas = 0
        if label_text:
            ctk.CTkLabel(
                self,
                text=label_text,
                fg_color=ctk.ThemeManager.theme["CTkScrollableFrame"]["label_fg_color"],
                corner_radius=6,
            ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=3, pady=(3, 0))
            fila_canvas = 1

        self.grid_rowconfigure(fila_canvas, weight=1)
        self.grid_columnconfigure(0, weight=1)

        color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        self._canvas = tkinter.Canvas(self, highlightthickness=0, bg=color)
        self._canvas.grid(row=fila_canvas, column=0, sticky="nsew")

        self._scrollbar_v = ctk.CTkScrollbar(self, orientation="vertical", command=self._canvas.yview)
        self._scrollbar_v.grid(row=fila_canvas, column=1, sticky="ns")

        self._scrollbar_h = ctk.CTkScrollbar(self, orientation="horizontal", command=self._canvas.xview)
        self._scrollbar_h.grid(row=fila_canvas + 1, column=0, sticky="ew")

        self._canvas.configure(yscrollcommand=self._scrollbar_v.set, xscrollcommand=self._scrollbar_h.set)

        # Frame donde se agregan las filas de la tabla.
        self.inner = ctk.CTkFrame(self._canvas, fg_color="transparent")
        self._window_id = self._canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._actualizar_scrollregion)
        self._canvas.bind("<Configure>", self._ajustar_alto_minimo)

    def _actualizar_scrollregion(self, _event=None) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _ajustar_alto_minimo(self, event) -> None:
        # Si el contenido es más bajo que el área visible, estira el frame
        # interno para que ocupe el alto disponible; si es más alto, lo deja
        # con su tamaño natural (aparece el scroll vertical).
        alto = max(event.height, self.inner.winfo_reqheight())
        self._canvas.itemconfigure(self._window_id, height=alto)

    def limpiar(self) -> None:
        for widget in self.inner.winfo_children():
            widget.destroy()
        self._canvas.xview_moveto(0)
        self._canvas.yview_moveto(0)
