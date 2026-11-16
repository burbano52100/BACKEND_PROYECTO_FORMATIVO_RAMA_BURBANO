"""Reportes de ventas e indicadores del Encargado (RF18 a RF21)."""

# Tipos fecha y duración
from datetime import date, timedelta
# Decimal = número decimal exacto
from decimal import Decimal

# Sesión de base de datos
from sqlalchemy.orm import Session

# Fecha de hoy y último día del mes
from app.core import tiempo
# Consultas de los reportes
from app.repositories.reporte_repository import ReporteRepository
# Consultas de sugerencias (para el indicador de pendientes)
from app.repositories.sugerencia_repository import SugerenciaRepository
# Filtros del reporte y períodos
from app.schemas.reporte import FiltrosVentas, Periodo
# Servicio de la cartera (para el indicador de deudas)
from app.services.cartera_service import CarteraService


# Calcula el primer y el último día del período que contiene una fecha
def rango_del_periodo(periodo: Periodo, fecha: date) -> tuple[date, date]:
    """Primer y último día del período que contiene la fecha."""
    # Día: desde y hasta son la misma fecha
    if periodo == Periodo.DIA:
        # Devuelve (fecha, fecha)
        return fecha, fecha
    # Semana: de lunes a domingo
    if periodo == Periodo.SEMANA:
        # weekday() da 0 para lunes; se restan esos días para llegar al lunes
        lunes = fecha - timedelta(days=fecha.weekday())
        # Devuelve (lunes, domingo)
        return lunes, lunes + timedelta(days=6)
    # Año: del 1 de enero al 31 de diciembre
    if periodo == Periodo.ANIO:
        # Devuelve (1 de enero, 31 de diciembre)
        return date(fecha.year, 1, 1), date(fecha.year, 12, 31)
    # Cantidad de meses del período (mes = 1, trimestre = 3, semestre = 6)
    meses = {Periodo.MES: 1, Periodo.TRIMESTRE: 3, Periodo.SEMESTRE: 6}[periodo]
    # Primer mes del período (ej.: noviembre en trimestres -> octubre = 10)
    mes_inicial = (fecha.month - 1) // meses * meses + 1
    # Primer día del período
    desde = date(fecha.year, mes_inicial, 1)
    # Último día del último mes del período
    hasta = tiempo.ultimo_dia_del_mes(date(fecha.year, mes_inicial + meses - 1, 1))
    # Devuelve (desde, hasta)
    return desde, hasta


# Clase con los reportes
class ReporteService:
    # Constructor: recibe la sesión y crea lo necesario
    def __init__(self, db: Session) -> None:
        # Repositorio de reportes
        self.reportes = ReporteRepository(db)
        # Repositorio de sugerencias
        self.sugerencias = SugerenciaRepository(db)
        # Servicio de la cartera
        self.cartera = CarteraService(db)

    # Reporte de ventas de un período
    def ventas(self, filtros: FiltrosVentas) -> dict:
        """Ventas (cantidad de almuerzos) e ingresos por período, por tipo y por día (RF18, RF19)."""
        # Rango del período (con hoy si no se envió fecha)
        desde, hasta = rango_del_periodo(filtros.periodo, filtros.fecha or tiempo.hoy())
        # Ventas por día convertidas a diccionarios
        por_dia = [dict(fila) for fila in self.reportes.ventas_por_dia(desde, hasta)]
        # Ventas por tipo convertidas a diccionarios
        por_tipo = [dict(fila) for fila in self.reportes.ventas_por_tipo(desde, hasta)]
        # Devuelve el reporte
        return {
            # Período pedido
            "periodo": filtros.periodo,
            # Primer día
            "desde": desde,
            # Último día
            "hasta": hasta,
            # Suma de los almuerzos de todos los días
            "total_almuerzos": sum(fila["almuerzos"] for fila in por_dia),
            # Suma de los ingresos de todos los días
            "total_ingresos": sum((fila["ingresos"] for fila in por_dia), Decimal(0)),
            # Detalle por tipo
            "por_tipo": por_tipo,
            # Detalle por día
            "por_dia": por_dia,
        }

    # Indicadores del panel del encargado
    def indicadores(self) -> dict:
        """Ventas de hoy, ingresos de hoy, deudas y sugerencias pendientes (RF21)."""
        # Fecha de hoy
        hoy = tiempo.hoy()
        # Ventas de hoy (lista con 0 o 1 fila)
        ventas_hoy = self.reportes.ventas_por_dia(hoy, hoy)
        # Resumen de la cartera
        cartera = self.cartera.listar()["resumen"]
        # Devuelve los indicadores
        return {
            # Hoy
            "fecha": hoy,
            # Almuerzos de hoy (0 si no hay ventas)
            "ventas_hoy": ventas_hoy[0]["almuerzos"] if ventas_hoy else 0,
            # Ingresos de hoy (0 si no hay ventas)
            "ingresos_hoy": ventas_hoy[0]["ingresos"] if ventas_hoy else Decimal(0),
            # Instructores con deuda
            "instructores_con_deuda": cartera["total_deudores"],
            # Deuda total
            "deuda_pendiente": cartera["deuda_total"],
            # Sugerencias pendientes
            "sugerencias_pendientes": self.sugerencias.contadores()["pendientes"],
        }
