# Rutas del buzón de sugerencias

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
# Esquemas que uso
from app.schemas.sugerencia import sugerencia_crear, atender_datos, sugerencia_respuesta
# Servicio con la lógica de las sugerencias
from app.services import sugerencia_service

# Función que documenta en /docs los errores que puede responder cada ruta
from app.core.errores import respuestas_error

# Creo el enrutador, todas las rutas empiezan con /sugerencias
enrutador = APIRouter(prefix="/sugerencias", tags=["Sugerencias"])


# Ruta para mandar una sugerencia (todos los roles)
@enrutador.post(
    "", response_model=sugerencia_respuesta, status_code=201,
    summary="Mandar una sugerencia",  # Título corto que sale en /docs
    description="Envía una sugerencia al buzón del encargado. **Rol requerido:** cualquiera con sesión iniciada.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 422),  # Errores que puede responder
)
def enviar_sugerencia(datos: sugerencia_crear, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Le pido al servicio que guarde la sugerencia
    sugerencia = sugerencia_service.enviar_sugerencia(bd, datos, usuario_actual)
    # Devuelvo la sugerencia
    return sugerencia


# Ruta para ver mis sugerencias (todos los roles)
@enrutador.get(
    "/mias", response_model=list[sugerencia_respuesta],
    summary="Ver mis sugerencias",  # Título corto que sale en /docs
    description="Lista las sugerencias que mandó quien inició sesión, con la respuesta del encargado. **Rol requerido:** cualquiera con sesión iniciada.",  # Explicación y rol que se necesita
    responses=respuestas_error(401),  # Errores que puede responder
)
def mis_sugerencias(bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Le pido mis sugerencias al servicio
    sugerencias = sugerencia_service.mis_sugerencias(bd, usuario_actual)
    # Devuelvo la lista
    return sugerencias


# Ruta para ver todas las sugerencias con los contadores (solo el encargado)
@enrutador.get(
    "",
    summary="Ver el buzón",  # Título corto que sale en /docs
    description="Lista todas las sugerencias con los contadores de pendientes y atendidas, con filtro por estado y paginación. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403, 422),  # Errores que puede responder
)
def listar_sugerencias(
    estado: Optional[str] = None,  # Filtrar por PENDIENTE o ATENDIDA
    saltar: int = 0,  # Cuántos registros me salto
    limite: int = 100,  # Cuántos registros traigo como máximo
    bd: Session = Depends(obtener_bd),  # Sesión de la base de datos
    usuario_actual: modelo_usuario = Depends(obtener_usuario_actual),  # Usuario que hace la petición
):
    # Solo el encargado puede ver el buzón
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido el buzón al servicio
    buzon = sugerencia_service.listar_sugerencias(bd, estado, saltar, limite)
    # Devuelvo los contadores y la lista
    return buzon


# Ruta para atender o responder una sugerencia (solo el encargado)
@enrutador.patch(
    "/{sugerencia_id}/atender",
    summary="Atender una sugerencia",  # Título corto que sale en /docs
    description="Marca la sugerencia como ATENDIDA y guarda la respuesta del encargado. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores que puede responder
)
def atender_sugerencia(sugerencia_id: int, datos: atender_datos, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede atender sugerencias
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que atienda la sugerencia
    sugerencia = sugerencia_service.atender_sugerencia(bd, sugerencia_id, datos)
    # Devuelvo la sugerencia
    return sugerencia
