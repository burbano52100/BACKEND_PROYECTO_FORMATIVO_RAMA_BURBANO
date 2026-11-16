"""Esquemas de los reportes de ventas e indicadores."""

# Tipo fecha
from datetime import date
# Lista cerrada de valores de texto
from enum import StrEnum

# Clase base de los esquemas
from pydantic import BaseModel

# Dinero de salida (número en el JSON)
from app.schemas.comunes import Dinero


# Períodos que acepta el reporte de ventas
class Periodo(StrEnum):
    # Un día
    DIA = "dia"
    # Lunes a domingo
    SEMANA = "semana"
    # Mes completo
    MES = "mes"
    # 3 meses
    TRIMESTRE = "trimestre"
    # 6 meses
    SEMESTRE = "semestre"
    # Año completo
    ANIO = "anio"


# Parámetros de GET /reportes/ventas
class FiltrosVentas(BaseModel):
    # Período (día por defecto)
    periodo: Periodo = Periodo.DIA
    # Fecha de referencia (hoy por defecto)
    fecha: date | None = None


# Ventas de un tipo de cliente
class VentasPorTipo(BaseModel):
    # APRENDIZ, BENEFICIARIO, INSTRUCTOR o INVITADO
    tipo: str
    # Cantidad de almuerzos
    almuerzos: int
    # Dinero recibido
    ingresos: Dinero


# Ventas de un día
class VentasPorDia(BaseModel):
    # Fecha
    fecha: date
    # Cantidad de almuerzos
    almuerzos: int
    # Dinero recibido
    ingresos: Dinero


# Respuesta de GET /reportes/ventas
class ReporteVentas(BaseModel):
    # Período consultado
    periodo: Periodo
    # Primer día del período
    desde: date
    # Último día del período
    hasta: date
    # Total de almuerzos del período
    total_almuerzos: int
    # Total de ingresos del período
    total_ingresos: Dinero
    # Ventas separadas por tipo de cliente
    por_tipo: list[VentasPorTipo]
    # Ventas separadas por día (para el gráfico)
    por_dia: list[VentasPorDia]


# Respuesta de GET /reportes/indicadores
class Indicadores(BaseModel):
    """Encabezado de estadísticas del Encargado (RF21)."""

    # Fecha de hoy
    fecha: date
    # Almuerzos vendidos hoy
    ventas_hoy: int
    # Dinero de hoy
    ingresos_hoy: Dinero
    # Instructores que deben algo
    instructores_con_deuda: int
    # Suma de las deudas
    deuda_pendiente: Dinero
    # Sugerencias sin atender
    sugerencias_pendientes: int
