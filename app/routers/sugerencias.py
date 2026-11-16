"""Endpoints del buzón de sugerencias."""

# Annotated asocia dependencias o fuentes de datos a un tipo
from typing import Annotated

# Herramientas de FastAPI
from fastapi import APIRouter, Depends, Query, status

# Documenta los errores en Swagger
from app.core.errores import respuestas_error
# CualquierRol y Encargado
from app.core.permisos import CualquierRol, Encargado
# Sesión de base de datos
from app.database.conexion import SesionDB
# Respuesta paginada y paginación base
from app.schemas.comunes import Pagina, PaginacionBase
# Esquemas de sugerencias
from app.schemas.sugerencia import (
    # Entrada para atender
    AtenderEntrada,
    # Filtros del buzón
    FiltrosSugerencia,
    # Página del buzón con contadores
    PaginaSugerencias,
    # Entrada para enviar
    SugerenciaCrear,
    # Salida de una sugerencia
    SugerenciaSalida,
)
# Servicio con las reglas del buzón
from app.services.sugerencia_service import SugerenciaService

# Router con prefijo /sugerencias
router = APIRouter(prefix="/sugerencias", tags=["Sugerencias"])


# Dependencia que crea el servicio
def obtener_servicio(db: SesionDB) -> SugerenciaService:
    # Devuelve un SugerenciaService nuevo
    return SugerenciaService(db)


# Atajo para recibir el servicio
Servicio = Annotated[SugerenciaService, Depends(obtener_servicio)]


# Endpoint POST /api/v1/sugerencias
@router.post(
    "",  # Ruta = /sugerencias
    response_model=SugerenciaSalida,  # Respuesta: la sugerencia creada
    status_code=status.HTTP_201_CREATED,  # Código 201
    summary="Enviar una sugerencia (RF47)",  # Título
    description="Asunto y mensaje obligatorios (mensaje de máximo 500 caracteres).\n\n**Rol requerido:** cualquiera.",  # Explicación
    responses=respuestas_error(401, 422),  # Errores posibles
)
# Recibe el cuerpo y el usuario autenticado (cualquier rol)
def enviar_sugerencia(datos: SugerenciaCrear, servicio: Servicio, usuario: CualquierRol):
    # Crea y devuelve la sugerencia
    return servicio.crear(datos, usuario)


# Endpoint GET /api/v1/sugerencias/mias
@router.get(
    "/mias",  # Ruta
    response_model=Pagina[SugerenciaSalida],  # Respuesta: página de sugerencias propias
    summary="Mis sugerencias",  # Título
    description="Sugerencias enviadas por quien consulta, con su respuesta.\n\n**Rol requerido:** cualquiera.",  # Explicación
    responses=respuestas_error(401, 422),  # Errores posibles
)
# Paginación en la URL y el usuario autenticado
def mis_sugerencias(filtros: Annotated[PaginacionBase, Query()], servicio: Servicio, usuario: CualquierRol):
    # Devuelve sus sugerencias
    return servicio.listar_mias(usuario, filtros)


# Endpoint GET /api/v1/sugerencias
@router.get(
    "",  # Ruta = /sugerencias
    response_model=PaginaSugerencias,  # Respuesta: página con contadores
    summary="Buzón del Encargado (RF48)",  # Título
    description="Contadores de recibidas, atendidas y pendientes; las pendientes aparecen primero.\n\n**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(401, 403, 422),  # Errores posibles
)
# Filtros en la URL; solo el encargado
def listar_sugerencias(filtros: Annotated[FiltrosSugerencia, Query()], servicio: Servicio, _: Encargado):
    # Devuelve el buzón
    return servicio.listar(filtros)


# Endpoint PATCH /api/v1/sugerencias/{sugerencia_id}/atender
@router.patch(
    "/{sugerencia_id}/atender",  # Ruta
    response_model=SugerenciaSalida,  # Respuesta: la sugerencia atendida
    summary="Marcar como atendida o responder (RF49)",  # Título
    description="Cambio de estado PENDIENTE a ATENDIDA, con respuesta opcional.\n\n**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores posibles
)
# Recibe el id, {"respuesta": ...}, el servicio y el encargado
def atender_sugerencia(sugerencia_id: int, datos: AtenderEntrada, servicio: Servicio, encargado: Encargado):
    # Atiende y devuelve la sugerencia
    return servicio.atender(sugerencia_id, datos, encargado)
