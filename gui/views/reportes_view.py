"""Vista de reportes/historial de asistencia."""

from datetime import datetime

import customtkinter as ctk

from gui.views.base_view import BaseView
from services.asistencia_service import AsistenciaService
from services.clase_service import ClaseService


class ReportesView(BaseView):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.clase_service = ClaseService()
        self.asistencia_service = AsistenciaService()
        self._clases_por_nombre: dict[str, int] = {}

        ctk.CTkLabel(self, text="Reportes de Asistencia", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)

        self.combo_clase = ctk.CTkComboBox(self, values=["Todas las clases"], command=self._on_clase_seleccionada)
        self.combo_clase.pack(pady=5, padx=20, fill="x")

        self.tabla = ctk.CTkScrollableFrame(self)
        self.tabla.pack(pady=10, padx=20, expand=True, fill="both")

    def on_show(self) -> None:
        self._cargar_clases()

    def _cargar_clases(self) -> None:
        clases = self.clase_service.listar_clases()
        self._clases_por_nombre = {f"{c['nombreClase']} ({c['periodoClase']})": c["idClase"] for c in clases}

        valores = ["Todas las clases", *self._clases_por_nombre]
        self.combo_clase.configure(values=valores)
        self.combo_clase.set(valores[0])
        self._cargar_historial()

    def _on_clase_seleccionada(self, _seleccion: str) -> None:
        self._cargar_historial()

    def _cargar_historial(self) -> None:
        for widget in self.tabla.winfo_children():
            widget.destroy()

        idClase = self._clases_por_nombre.get(self.combo_clase.get())
        registros = self.asistencia_service.historial(idClase=idClase)

        if not registros:
            ctk.CTkLabel(self.tabla, text="No hay registros de asistencia").pack(anchor="w", padx=10, pady=5)
            return

        for registro in registros:
            apellidos = " ".join(filter(None, [registro["apPaterno"], registro["apMaterno"]]))
            fecha_hora = self._formatear_fecha_hora(registro["fechaHora"])
            tipo = "Entrada" if registro["tipoRegistro"] == "ENTRADA" else "Salida"
            texto = (
                f"{fecha_hora} | {registro['nombre']} {apellidos} | "
                f"{registro['nombreClase']} ({registro['periodoClase']}) | {tipo}"
            )
            ctk.CTkLabel(self.tabla, text=texto).pack(anchor="w", padx=10, pady=2)

    @staticmethod
    def _formatear_fecha_hora(fecha_hora: str) -> str:
        try:
            dt = datetime.strptime(fecha_hora, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return fecha_hora
        return dt.strftime("%d/%m/%Y %H:%M")
