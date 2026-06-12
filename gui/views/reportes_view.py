"""Vista de reportes/historial de asistencia."""

from datetime import datetime

import customtkinter as ctk

from gui.views.base_view import BaseView
from services.asistencia_service import AsistenciaService
from services.clase_service import ClaseService
from services.usuario_service import UsuarioService


class ReportesView(BaseView):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.clase_service = ClaseService()
        self.usuario_service = UsuarioService()
        self.asistencia_service = AsistenciaService()
        self._clases_por_nombre: dict[str, int] = {}
        self._roles_por_nombre: dict[str, int] = {}

        ctk.CTkLabel(self, text="Reportes de Asistencia", font=ctk.CTkFont(size=20, weight="bold")).pack(
            pady=(15, 10)
        )

        frame_filtros = ctk.CTkFrame(self, fg_color="transparent")
        frame_filtros.pack(pady=5, padx=20, fill="x")
        frame_filtros.grid_columnconfigure((0, 1), weight=1)

        self.combo_clase = ctk.CTkComboBox(
            frame_filtros, values=["Todas las clases"], command=self._on_filtro_cambiado
        )
        self.combo_clase.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.combo_rol = ctk.CTkComboBox(
            frame_filtros, values=["Todos los roles"], command=self._on_filtro_cambiado
        )
        self.combo_rol.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(pady=10, padx=20, expand=True, fill="both")

        self.tab_historial = self.tabview.add("Historial")
        self.tab_metricas = self.tabview.add("Totales por usuario")

        self.tabla_historial = ctk.CTkScrollableFrame(self.tab_historial, fg_color="transparent")
        self.tabla_historial.pack(expand=True, fill="both")

        self.tabla_metricas = ctk.CTkScrollableFrame(self.tab_metricas, fg_color="transparent")
        self.tabla_metricas.pack(expand=True, fill="both")

    def on_show(self) -> None:
        self._cargar_filtros()

    def _cargar_filtros(self) -> None:
        clases = self.clase_service.listar_clases()
        self._clases_por_nombre = {f"{c['nombreClase']} ({c['periodoClase']})": c["idClase"] for c in clases}

        valores_clase = ["Todas las clases", *self._clases_por_nombre]
        self.combo_clase.configure(values=valores_clase)
        if self.combo_clase.get() not in valores_clase:
            self.combo_clase.set(valores_clase[0])

        tipos = self.usuario_service.listar_tipos_usuario()
        self._roles_por_nombre = {t["nombreTipoUsuario"]: t["idTipoUsuario"] for t in tipos}

        valores_rol = ["Todos los roles", *self._roles_por_nombre]
        self.combo_rol.configure(values=valores_rol)
        if self.combo_rol.get() not in valores_rol:
            self.combo_rol.set(valores_rol[0])

        self._cargar_reportes()

    def _on_filtro_cambiado(self, _seleccion: str) -> None:
        self._cargar_reportes()

    def _cargar_reportes(self) -> None:
        idClase = self._clases_por_nombre.get(self.combo_clase.get())
        idTipoUsuario = self._roles_por_nombre.get(self.combo_rol.get())
        self._cargar_historial(idClase, idTipoUsuario)
        self._cargar_metricas(idClase, idTipoUsuario)

    def _cargar_historial(self, idClase: int | None, idTipoUsuario: int | None) -> None:
        for widget in self.tabla_historial.winfo_children():
            widget.destroy()

        registros = self.asistencia_service.historial(idClase=idClase, idTipoUsuario=idTipoUsuario)
        if not registros:
            ctk.CTkLabel(self.tabla_historial, text="No hay registros de asistencia").pack(
                anchor="w", padx=10, pady=5
            )
            return

        for registro in registros:
            apellidos = " ".join(filter(None, [registro["apPaterno"], registro["apMaterno"]]))
            fecha_hora = self._formatear_fecha_hora(registro["fechaHora"])
            tipo = "Entrada" if registro["tipoRegistro"] == "ENTRADA" else "Salida"
            texto = (
                f"{fecha_hora} | {registro['nombre']} {apellidos} | "
                f"{registro['nombreClase']} ({registro['periodoClase']}) | {tipo}"
            )
            ctk.CTkLabel(self.tabla_historial, text=texto).pack(anchor="w", padx=10, pady=2)

    def _cargar_metricas(self, idClase: int | None, idTipoUsuario: int | None) -> None:
        for widget in self.tabla_metricas.winfo_children():
            widget.destroy()

        metricas = self.asistencia_service.metricas_por_usuario(idClase=idClase, idTipoUsuario=idTipoUsuario)
        if not metricas:
            ctk.CTkLabel(self.tabla_metricas, text="No hay registros de asistencia").pack(
                anchor="w", padx=10, pady=5
            )
            return

        for fila in metricas:
            apellidos = " ".join(filter(None, [fila["apPaterno"], fila["apMaterno"]]))
            texto = (
                f"{fila['nombre']} {apellidos} ({fila['nombreTipoUsuario']}) | "
                f"Entradas: {fila['totalEntradas']} | Salidas: {fila['totalSalidas']} | Total: {fila['total']}"
            )
            ctk.CTkLabel(self.tabla_metricas, text=texto).pack(anchor="w", padx=10, pady=2)

    @staticmethod
    def _formatear_fecha_hora(fecha_hora: str) -> str:
        try:
            dt = datetime.strptime(fecha_hora, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return fecha_hora
        return dt.strftime("%d/%m/%Y %H:%M")
