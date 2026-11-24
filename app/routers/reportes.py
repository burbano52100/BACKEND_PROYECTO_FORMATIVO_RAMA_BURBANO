# Rutas de los reportes de ventas e indicadores (solo el encargado)

# date es una fecha
from datetime import date
# Optional quiere decir que un parámetro puede venir vacío
from typing import Optional

# APIRouter agrupa las rutas y Depends es para dependencias
from fastapi import APIRouter, Depends
# Session es el tipo de la sesión de la base de datos
from sqlalchemy.orm import Session

# Función que da la sesión de la base de datos
from app.database.conexion import obtener_bd
# Modelo de usuario
from app.models.usuario import modelo_usuario
# Funciones de permisos
from app.core.permisos import obtener_usuario_actual, verificar_rol
# Lista de roles que pueden entrar
from app.core.roles import solo_encargado
# Esquemas de las respuestas
from app.schemas.reporte import reporte_ventas_respuesta, indicadores_respuesta
# Servicio con la lógica de los reportes
from app.services import reporte_service

# Función que documenta en /docs los errores que puede responder cada ruta
from app.core.errores import respuestas_error

# Creo el enrutador, todas las rutas empiezan con /reportes
enrutador = APIRouter(prefix="/reportes", tags=["Reportes"])


# Ruta para ver las ventas de un día, semana, mes o año
@enrutador.get(
    "/ventas", response_model=reporte_ventas_respuesta,
    summary="Ventas por periodo",  # Título corto que sale en /docs
    description="Ventas del día, la semana, el mes o el año (periodo=dia, semana, mes o anio) desde una fecha. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 422),  # Errores que puede responder
)
def reporte_ventas(periodo: str = "dia", fecha: Optional[date] = None, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede ver los reportes
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido el reporte al servicio
    reporte = reporte_service.reporte_ventas(bd, periodo, fecha)
    # Devuelvo el reporte
    return reporte


# Ruta para ver los indicadores de hoy
@enrutador.get(
    "/indicadores", response_model=indicadores_respuesta,
    summary="Indicadores de hoy",  # Título corto que sale en /docs
    description="Reservas, ventas, deudas y sugerencias pendientes del día. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403),  # Errores que puede responder
)
def indicadores(bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede ver los indicadores
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido los indicadores al servicio
    resultado = reporte_service.indicadores(bd)
    # Devuelvo los indicadores
    return resultado
