"""Endpoints de fichas y del módulo de Grupos (solo el Encargado)."""

# Tipo fecha
from datetime import date
# Annotated asocia dependencias o fuentes de datos a un tipo
from typing import Annotated

# Herramientas de FastAPI
from fastapi import APIRouter, Depends, Query, status

# Documenta los errores en Swagger
from app.core.errores import respuestas_error
# Solo deja pasar al encargado
from app.core.permisos import Encargado
# Sesión de base de datos
from app.database.conexion import SesionDB
# Respuesta con mensaje y respuesta paginada
from app.schemas.comunes import Mensaje, Pagina
# Esquemas de fichas
from app.schemas.ficha import (
    # Salida de las estadísticas
    EstadisticasGrupos,
    # Entrada para actualizar
    FichaActualizar,
    # Entrada para crear
    FichaCrear,
    # Salida de una ficha
    FichaSalida,
    # Filtros del listado
    FiltrosFicha,
    # Salida de cada aprendiz que reservó
    ReservaDeFicha,
)
# Servicio con las reglas de fichas
from app.services.ficha_service import FichaService

# Router con prefijo /fichas
router = APIRouter(prefix="/fichas", tags=["Fichas y grupos"])

# Parámetro opcional ?fecha=AAAA-MM-DD que viene en la URL
Fecha = Annotated[date | None, Query(description="AAAA-MM-DD; por defecto hoy")]


# Dependencia que crea el servicio
def obtener_servicio(db: SesionDB) -> FichaService:
    # Devuelve un FichaService nuevo
    return FichaService(db)


# Atajo para recibir el servicio
Servicio = Annotated[FichaService, Depends(obtener_servicio)]


# Endpoint GET /api/v1/fichas
@router.get(
    "",  # Ruta vacía = /fichas
    response_model=Pagina[FichaSalida],  # Respuesta: página de fichas
    summary="Listar fichas",  # Título
    description="Filtros por código o programa, jornada y estado.\n\n**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(401, 403, 422),  # Errores posibles
)
# Filtros en la URL; "_" exige el rol encargado
def listar_fichas(filtros: Annotated[FiltrosFicha, Query()], servicio: Servicio, _: Encargado):
    # Devuelve la página de fichas
    return servicio.listar(filtros)


# Endpoint GET /api/v1/fichas/estadisticas (va antes de /{ficha_id} para que "estadisticas" no se lea como id)
@router.get(
    "/estadisticas",  # Ruta
    response_model=EstadisticasGrupos,  # Respuesta: estadísticas
    summary="Estadísticas de grupos (RF40)",  # Título
    description="Total de grupos y estudiantes, y promedio de almuerzos por grupo en la fecha.\n\n**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(401, 403, 422),  # Errores posibles
)
# fecha es opcional (None = hoy)
def estadisticas(servicio: Servicio, _: Encargado, fecha: Fecha = None):
    # Devuelve las estadísticas
    return servicio.estadisticas(fecha)


# Endpoint GET /api/v1/fichas/{ficha_id}
@router.get(
    "/{ficha_id}",  # Ruta con el id
    response_model=FichaSalida,  # Respuesta: una ficha
    summary="Consultar una ficha",  # Título
    description="**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(401, 403, 404),  # Errores posibles
)
# Recibe el id de la ruta
def obtener_ficha(ficha_id: int, servicio: Servicio, _: Encargado):
    # Devuelve la ficha (o 404)
    return servicio.obtener(ficha_id)


# Endpoint GET /api/v1/fichas/{ficha_id}/reservas
@router.get(
    "/{ficha_id}/reservas",  # Ruta
    response_model=list[ReservaDeFicha],  # Respuesta: lista de aprendices que reservaron
    summary="Aprendices de la ficha que reservaron (RF41)",  # Título
    description="Lista con el estado de pago de cada aprendiz en la fecha.\n\n**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(401, 403, 404, 422),  # Errores posibles
)
# Recibe el id de la ficha y la fecha opcional
def reservas_de_ficha(ficha_id: int, servicio: Servicio, _: Encargado, fecha: Fecha = None):
    # Devuelve la lista
    return servicio.reservas_del_dia(ficha_id, fecha)


# Endpoint POST /api/v1/fichas
@router.post(
    "",  # Ruta = /fichas
    response_model=FichaSalida,  # Respuesta: la ficha creada
    status_code=status.HTTP_201_CREATED,  # Código 201
    summary="Crear una ficha",  # Título
    description="El código de la ficha es único.\n\n**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(401, 403, 409, 422),  # Errores posibles
)
# Recibe el cuerpo, el servicio y el encargado
def crear_ficha(datos: FichaCrear, servicio: Servicio, encargado: Encargado):
    # Crea y devuelve la ficha
    return servicio.crear(datos, encargado)


# Endpoint PATCH /api/v1/fichas/{ficha_id}
@router.patch(
    "/{ficha_id}",  # Ruta
    response_model=FichaSalida,  # Respuesta: la ficha actualizada
    summary="Actualizar una ficha",  # Título
    description="**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(401, 403, 404, 422),  # Errores posibles
)
# Recibe el id, los cambios, el servicio y el encargado
def actualizar_ficha(ficha_id: int, datos: FichaActualizar, servicio: Servicio, encargado: Encargado):
    # Actualiza y devuelve la ficha
    return servicio.actualizar(ficha_id, datos, encargado)


# Endpoint DELETE /api/v1/fichas/{ficha_id}
@router.delete(
    "/{ficha_id}",  # Ruta
    response_model=Mensaje,  # Respuesta: un mensaje
    summary="Eliminar una ficha",  # Título
    description="Si tiene aprendices se desactiva (borrado lógico); si no, se borra.\n\n**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(400, 401, 403, 404),  # Errores posibles
)
# Recibe el id, el servicio y el encargado
def eliminar_ficha(ficha_id: int, servicio: Servicio, encargado: Encargado):
    # Elimina (lógico o físico) y devuelve el mensaje
    return {"mensaje": servicio.eliminar(ficha_id, encargado)}
