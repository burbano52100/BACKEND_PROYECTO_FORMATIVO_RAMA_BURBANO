"""Endpoints del Menú del Día."""

# Annotated asocia dependencias o fuentes de datos a un tipo
from typing import Annotated

# Herramientas de FastAPI
from fastapi import APIRouter, Depends, Query, status

# Documenta los errores en Swagger
from app.core.errores import respuestas_error
# CualquierRol = cualquier usuario autenticado; Encargado = solo el encargado
from app.core.permisos import CualquierRol, Encargado
# Sesión de base de datos
from app.database.conexion import SesionDB
# Respuesta con mensaje y respuesta paginada
from app.schemas.comunes import Mensaje, Pagina
# Esquemas de menús
from app.schemas.menu import FiltrosMenu, MenuActualizar, MenuCrear, MenuParaComensal, MenuSalida
# Servicio con las reglas del menú
from app.services.menu_service import MenuService

# Router con prefijo /menus
router = APIRouter(prefix="/menus", tags=["Menú del Día"])


# Dependencia que crea el servicio
def obtener_servicio(db: SesionDB) -> MenuService:
    # Devuelve un MenuService nuevo
    return MenuService(db)


# Atajo para recibir el servicio
Servicio = Annotated[MenuService, Depends(obtener_servicio)]


# Endpoint GET /api/v1/menus/hoy
@router.get(
    "/hoy",  # Ruta
    response_model=MenuParaComensal,  # Respuesta: menú con el precio de quien consulta
    summary="Menú de hoy (RF08, RF15)",  # Título
    description=(  # Explicación
        "Menú activo de hoy con el precio que le corresponde a quien consulta (aprendiz $5.000, "
        "beneficiario $0, invitado $8.000), lo vendido, si está agotado y la reserva propia.\n\n"
        "**Rol requerido:** cualquiera."
    ),
    responses=respuestas_error(401, 404),  # Errores posibles
)
# Cualquier usuario autenticado
def menu_de_hoy(servicio: Servicio, usuario: CualquierRol):
    # Devuelve el menú de hoy (o 404)
    return servicio.del_dia(usuario)


# Endpoint GET /api/v1/menus/proximos
@router.get(
    "/proximos",  # Ruta
    response_model=list[MenuParaComensal],  # Respuesta: lista de menús
    summary="Próximos menús",  # Título
    description="Menús activos desde hoy, para elegir cuál reservar.\n\n**Rol requerido:** cualquiera.",  # Explicación
    responses=respuestas_error(401),  # Errores posibles
)
# Cualquier usuario autenticado
def proximos_menus(servicio: Servicio, usuario: CualquierRol):
    # Devuelve los próximos menús
    return servicio.proximos(usuario)


# Endpoint GET /api/v1/menus
@router.get(
    "",  # Ruta = /menus
    response_model=Pagina[MenuSalida],  # Respuesta: página de menús
    summary="Listar menús",  # Título
    description="Historial de menús con filtros por rango de fechas y estado.\n\n**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(401, 403, 422),  # Errores posibles
)
# Filtros en la URL; solo el encargado
def listar_menus(filtros: Annotated[FiltrosMenu, Query()], servicio: Servicio, _: Encargado):
    # Devuelve la página de menús
    return servicio.listar(filtros)


# Endpoint GET /api/v1/menus/{menu_id}
@router.get(
    "/{menu_id}",  # Ruta con el id
    response_model=MenuSalida,  # Respuesta: un menú
    summary="Consultar un menú",  # Título
    description="**Rol requerido:** cualquiera.",  # Explicación
    responses=respuestas_error(401, 404),  # Errores posibles
)
# Cualquier usuario autenticado
def obtener_menu(menu_id: int, servicio: Servicio, _: CualquierRol):
    # Devuelve el menú (o 404)
    return servicio.obtener(menu_id)


# Endpoint POST /api/v1/menus
@router.post(
    "",  # Ruta = /menus
    response_model=MenuSalida,  # Respuesta: el menú creado
    status_code=status.HTTP_201_CREATED,  # Código 201
    summary="Configurar un menú (RF16)",  # Título
    description=(  # Explicación
        "Un solo menú por fecha (409). La fecha no puede ser anterior a hoy, los precios son mayores o iguales "
        "a 0 y el cupo es un entero mayor a 0.\n\n**Rol requerido:** encargado."
    ),
    responses=respuestas_error(401, 403, 409, 422),  # Errores posibles
)
# Recibe el cuerpo, el servicio y el encargado
def crear_menu(datos: MenuCrear, servicio: Servicio, encargado: Encargado):
    # Crea y devuelve el menú
    return servicio.crear(datos, encargado)


# Endpoint PATCH /api/v1/menus/{menu_id}
@router.patch(
    "/{menu_id}",  # Ruta
    response_model=MenuSalida,  # Respuesta: el menú actualizado
    summary="Actualizar un menú",  # Título
    description=(  # Explicación
        "No se modifican menús de fechas pasadas y el cupo no puede quedar por debajo de lo vendido.\n\n"
        "**Rol requerido:** encargado."
    ),
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores posibles
)
# Recibe el id, los cambios, el servicio y el encargado
def actualizar_menu(menu_id: int, datos: MenuActualizar, servicio: Servicio, encargado: Encargado):
    # Actualiza y devuelve el menú
    return servicio.actualizar(menu_id, datos, encargado)


# Endpoint DELETE /api/v1/menus/{menu_id}
@router.delete(
    "/{menu_id}",  # Ruta
    response_model=Mensaje,  # Respuesta: un mensaje
    summary="Eliminar un menú",  # Título
    description="Si tiene reservas se desactiva (borrado lógico); si no, se borra.\n\n**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(400, 401, 403, 404),  # Errores posibles
)
# Recibe el id, el servicio y el encargado
def eliminar_menu(menu_id: int, servicio: Servicio, encargado: Encargado):
    # Elimina (lógico o físico) y devuelve el mensaje
    return {"mensaje": servicio.eliminar(menu_id, encargado)}
