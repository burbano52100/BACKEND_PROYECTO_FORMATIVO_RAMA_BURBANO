"""Endpoints de reportes de ventas e indicadores (solo el Encargado)."""

# Annotated asocia dependencias o fuentes de datos a un tipo
from typing import Annotated

# Herramientas de FastAPI
from fastapi import APIRouter, Depends, Query

# Documenta los errores en Swagger
from app.core.errores import respuestas_error
# Solo deja pasar al encargado
from app.core.permisos import Encargado
# Sesión de base de datos
from app.database.conexion import SesionDB
# Esquemas de reportes
from app.schemas.reporte import FiltrosVentas, Indicadores, ReporteVentas
# Servicio de reportes
from app.services.reporte_service import ReporteService

# Router con prefijo /reportes
router = APIRouter(prefix="/reportes", tags=["Reportes"])


# Dependencia que crea el servicio
def obtener_servicio(db: SesionDB) -> ReporteService:
    # Devuelve un ReporteService nuevo
    return ReporteService(db)


# Atajo para recibir el servicio
Servicio = Annotated[ReporteService, Depends(obtener_servicio)]


# Endpoint GET /api/v1/reportes/ventas
@router.get(
    "/ventas",  # Ruta
    response_model=ReporteVentas,  # Respuesta: el reporte
    summary="Ventas e ingresos por período (RF18, RF19, RF20)",  # Título
    description=(  # Explicación
        "Período: dia, semana, mes, trimestre, semestre o anio (por defecto, el día de hoy). Devuelve totales, "
        "ventas por tipo de cliente y ventas por día para el gráfico.\n\n**Rol requerido:** encargado."
    ),
    responses=respuestas_error(401, 403, 422),  # Errores posibles
)
# ?periodo=mes&fecha=2026-11-16 en la URL; solo el encargado
def reporte_ventas(filtros: Annotated[FiltrosVentas, Query()], servicio: Servicio, _: Encargado):
    # Devuelve el reporte de ventas
    return servicio.ventas(filtros)


# Endpoint GET /api/v1/reportes/indicadores
@router.get(
    "/indicadores",  # Ruta
    response_model=Indicadores,  # Respuesta: los indicadores
    summary="Indicadores del encabezado (RF21)",  # Título
    description="Ventas de hoy, ingresos de hoy, deudas pendientes y sugerencias pendientes.\n\n**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(401, 403),  # Errores posibles
)
# Solo el encargado
def indicadores(servicio: Servicio, _: Encargado):
    # Devuelve los indicadores de hoy
    return servicio.indicadores()
