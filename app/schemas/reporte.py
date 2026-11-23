# Esquemas de los reportes
# Sirven para decir qué datos se responden en los reportes

# date es una fecha
from datetime import date

# BaseModel es la clase base
from pydantic import BaseModel


# Ventas de un tipo de cliente
class ventas_tipo(BaseModel):
    # Cuántos almuerzos se vendieron
    almuerzos: int
    # Cuánta plata entró
    ingresos: float


# Ventas de un día
class ventas_dia(BaseModel):
    # Fecha del día
    fecha: date
    # Cuántos almuerzos se vendieron
    almuerzos: int
    # Cuánta plata entró
    ingresos: float


# Lo que se responde en el reporte de ventas
class reporte_ventas_respuesta(BaseModel):
    # dia, semana, mes o anio
    periodo: str
    # Fecha inicial del periodo
    desde: date
    # Fecha final del periodo
    hasta: date
    # Almuerzos vendidos en todo el periodo
    total_almuerzos: int
    # Plata de todo el periodo
    total_ingresos: float
    # Ventas por tipo de cliente (APRENDIZ, BENEFICIARIO, INSTRUCTOR e INVITADO)
    por_tipo: dict[str, ventas_tipo]
    # Ventas de cada día
    por_dia: list[ventas_dia]


# Lo que se responde en los indicadores de hoy
class indicadores_respuesta(BaseModel):
    # Fecha de hoy
    fecha: date
    # Almuerzos vendidos hoy
    ventas_hoy: int
    # Plata de hoy
    ingresos_hoy: float
    # Cuántos instructores deben
    instructores_con_deuda: int
    # Cuánto deben entre todos
    deuda_pendiente: float
    # Sugerencias sin atender
    sugerencias_pendientes: int
