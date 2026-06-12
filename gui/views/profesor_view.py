"""Panel de Profesor: el profesor elige su nombre y consulta los reportes de
asistencia de los alumnos en las clases en las que está inscrito."""

from datetime import datetime
from typing import Callable

import customtkinter as ctk

from gui.views.base_view import BaseView
from services.asistencia_service import AsistenciaService
from services.inscripcion_service import InscripcionService
from services.usuario_service import UsuarioService


class ProfesorView(BaseView):
    def __init__(self, master, on_salir: Callable[[], None], **kwargs):
        super().__init__(master, **kwargs)

        self.on_salir = on_salir
        self.usuario_service = UsuarioService()
        self.inscripcion_service = InscripcionService()
        self.asistencia_service = AsistenciaService()

        self._idProfesor_actual: int | None = None
        self._idTipoProfesor: int | None = None
        self._idTipoAlumno: int | None = None
        self._clases_por_nombre: dict[str, int] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._construir_ui()

    def _construir_ui(self) -> None:
        # --- Página 1: selección de profesor -------------------------------------
        self.frame_seleccion = ctk.CTkFrame(self)
        self.frame_seleccion.grid(row=0, column=0, sticky="nsew")
        self.frame_seleccion.grid_columnconfigure(0, weight=1)
        self.frame_seleccion.grid_rowconfigure(1, weight=1)

        barra_seleccion = ctk.CTkFrame(self.frame_seleccion, fg_color="transparent")
        barra_seleccion.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkButton(barra_seleccion, text="‹ Volver", width=100, command=self.on_salir).pack(side="left")
        ctk.CTkLabel(
            barra_seleccion,
            text="Panel de Profesor: selecciona tu nombre",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left", padx=15)

        self.lista_profesores = ctk.CTkScrollableFrame(self.frame_seleccion, label_text="Profesores")
        self.lista_profesores.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # --- Página 2: reportes del profesor --------------------------------------
        self.frame_reportes = ctk.CTkFrame(self)
        self.frame_reportes.grid(row=0, column=0, sticky="nsew")
        self.frame_reportes.grid_columnconfigure(0, weight=1)
        self.frame_reportes.grid_rowconfigure(2, weight=1)

        barra_reportes = ctk.CTkFrame(self.frame_reportes, fg_color="transparent")
        barra_reportes.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkButton(
            barra_reportes, text="‹ Cambiar de profesor", width=160, command=self._volver_a_seleccion
        ).pack(side="left")
        self.label_profesor = ctk.CTkLabel(barra_reportes, text="", font=ctk.CTkFont(size=16, weight="bold"))
        self.label_profesor.pack(side="left", padx=15)

        self.combo_clase = ctk.CTkComboBox(
            self.frame_reportes, values=["Todas mis clases"], command=self._on_clase_cambiada
        )
        self.combo_clase.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        self.tabview = ctk.CTkTabview(self.frame_reportes)
        self.tabview.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.tab_historial = self.tabview.add("Historial")
        self.tab_metricas = self.tabview.add("Totales por alumno")

        self.tabla_historial = ctk.CTkScrollableFrame(self.tab_historial, fg_color="transparent")
        self.tabla_historial.pack(expand=True, fill="both")

        self.tabla_metricas = ctk.CTkScrollableFrame(self.tab_metricas, fg_color="transparent")
        self.tabla_metricas.pack(expand=True, fill="both")

    # --- Ciclo de vida -----------------------------------------------------

    def on_show(self) -> None:
        tipos = self.usuario_service.listar_tipos_usuario()
        self._idTipoProfesor = next((t["idTipoUsuario"] for t in tipos if t["nombreTipoUsuario"] == "Profesor"), None)
        self._idTipoAlumno = next((t["idTipoUsuario"] for t in tipos if t["nombreTipoUsuario"] == "Alumno"), None)

        self._cargar_profesores()
        self._volver_a_seleccion()

    # --- Selección de profesor ----------------------------------------------

    def _cargar_profesores(self) -> None:
        for widget in self.lista_profesores.winfo_children():
            widget.destroy()

        usuarios = self.usuario_service.listar_usuarios(solo_activos=True)
        profesores = [u for u in usuarios if u["tipoUsuario"] == self._idTipoProfesor]

        if not profesores:
            ctk.CTkLabel(self.lista_profesores, text="No hay profesores registrados").pack(
                anchor="w", padx=10, pady=5
            )
            return

        for profesor in profesores:
            apellidos = " ".join(filter(None, [profesor["apPaterno"], profesor["apMaterno"]]))
            nombre_completo = f"{profesor['nombre']} {apellidos}"
            ctk.CTkButton(
                self.lista_profesores,
                text=nombre_completo,
                anchor="w",
                fg_color="transparent",
                command=lambda idUsuario=profesor["idUsuario"], nombre=nombre_completo: self._seleccionar_profesor(
                    idUsuario, nombre
                ),
            ).pack(fill="x", padx=5, pady=2)

    def _seleccionar_profesor(self, idProfesor: int, nombre: str) -> None:
        self._idProfesor_actual = idProfesor
        self.label_profesor.configure(text=f"Profesor: {nombre}")
        self._cargar_clases()
        self.frame_reportes.tkraise()

    def _volver_a_seleccion(self) -> None:
        self._idProfesor_actual = None
        self.frame_seleccion.tkraise()

    # --- Reportes --------------------------------------------------------------

    def _cargar_clases(self) -> None:
        clases = self.inscripcion_service.listar_clases_de_usuario(self._idProfesor_actual)
        self._clases_por_nombre = {f"{c['nombreClase']} ({c['periodoClase']})": c["idClase"] for c in clases}

        valores = ["Todas mis clases", *self._clases_por_nombre]
        self.combo_clase.configure(values=valores)
        self.combo_clase.set(valores[0])
        self._cargar_reportes()

    def _on_clase_cambiada(self, _seleccion: str) -> None:
        self._cargar_reportes()

    def _cargar_reportes(self) -> None:
        idClase = self._clases_por_nombre.get(self.combo_clase.get())
        self._cargar_historial(idClase)
        self._cargar_metricas(idClase)

    def _cargar_historial(self, idClase: int | None) -> None:
        for widget in self.tabla_historial.winfo_children():
            widget.destroy()

        registros = self.asistencia_service.historial(idClase=idClase, idTipoUsuario=self._idTipoAlumno)
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

    def _cargar_metricas(self, idClase: int | None) -> None:
        for widget in self.tabla_metricas.winfo_children():
            widget.destroy()

        metricas = self.asistencia_service.metricas_por_usuario(idClase=idClase, idTipoUsuario=self._idTipoAlumno)
        if not metricas:
            ctk.CTkLabel(self.tabla_metricas, text="No hay registros de asistencia").pack(
                anchor="w", padx=10, pady=5
            )
            return

        for fila in metricas:
            apellidos = " ".join(filter(None, [fila["apPaterno"], fila["apMaterno"]]))
            texto = (
                f"{fila['nombre']} {apellidos} | "
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
