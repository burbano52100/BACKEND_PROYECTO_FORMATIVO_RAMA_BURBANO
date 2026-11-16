"""Endpoints del inventario: materiales y kardex (solo el Encargado)."""

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
# Esquemas del inventario
from app.schemas.inventario import (
    # Filtros del kardex
    FiltrosKardex,
    # Filtros de materiales
    FiltrosMaterial,
    # Entrada para editar
    MaterialActualizar,
    # Entrada para crear
    MaterialCrear,
    # Salida de un material
    MaterialSalida,
    # Entrada de un movimiento
    MovimientoCrear,
    # Salida de un movimiento
    MovimientoSalida,
)
# Servicio con las reglas del inventario
from app.services.inventario_service import InventarioService

# Router con prefijo /inventario
router = APIRouter(prefix="/inventario", tags=["Inventario"])


# Dependencia que crea el servicio
def obtener_servicio(db: SesionDB) -> InventarioService:
    # Devuelve un InventarioService nuevo
    return InventarioService(db)


# Atajo para recibir el servicio
Servicio = Annotated[InventarioService, Depends(obtener_servicio)]


# Endpoint GET /api/v1/inventario/materiales
@router.get(
    "/materiales",  # Ruta
    response_model=Pagina[MaterialSalida],  # Respuesta: página de materiales
    summary="Control de stock (RF28, RF32)",  # Título
    description=(  # Explicación
        "Búsqueda por nombre o código de barras y filtros por categoría y estado. Cada material trae su estado: "
        "BUENO, BAJO, CRITICO o VENCIENDO.\n\n**Rol requerido:** encargado."
    ),
    responses=respuestas_error(401, 403, 422),  # Errores posibles
)
# Filtros en la URL; solo el encargado
def listar_materiales(filtros: Annotated[FiltrosMaterial, Query()], servicio: Servicio, _: Encargado):
    # Devuelve la página de materiales
    return servicio.listar_materiales(filtros)


# Endpoint GET /api/v1/inventario/materiales/{material_id}
@router.get(
    "/materiales/{material_id}",  # Ruta con el id
    response_model=MaterialSalida,  # Respuesta: un material
    summary="Consultar un material",  # Título
    description="**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(401, 403, 404),  # Errores posibles
)
# Recibe el id
def obtener_material(material_id: int, servicio: Servicio, _: Encargado):
    # Devuelve el material (o 404)
    return servicio.obtener_material(material_id)


# Endpoint POST /api/v1/inventario/materiales
@router.post(
    "/materiales",  # Ruta
    response_model=MaterialSalida,  # Respuesta: el material creado
    status_code=status.HTTP_201_CREATED,  # Código 201
    summary="Agregar un material (RF29)",  # Título
    description=(  # Explicación
        "Código de barras único (409). El stock inicial genera una ENTRADA en el kardex.\n\n"
        "**Rol requerido:** encargado."
    ),
    responses=respuestas_error(401, 403, 409, 422),  # Errores posibles
)
# Recibe el cuerpo, el servicio y el encargado
def crear_material(datos: MaterialCrear, servicio: Servicio, encargado: Encargado):
    # Crea y devuelve el material
    return servicio.crear_material(datos, encargado)


# Endpoint PATCH /api/v1/inventario/materiales/{material_id}
@router.patch(
    "/materiales/{material_id}",  # Ruta
    response_model=MaterialSalida,  # Respuesta: el material actualizado
    summary="Editar un material (RF30)",  # Título
    description="El stock no se edita aquí: cambia con movimientos del kardex.\n\n**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores posibles
)
# Recibe el id, los cambios, el servicio y el encargado
def actualizar_material(material_id: int, datos: MaterialActualizar, servicio: Servicio, encargado: Encargado):
    # Actualiza y devuelve el material
    return servicio.actualizar_material(material_id, datos, encargado)


# Endpoint DELETE /api/v1/inventario/materiales/{material_id}
@router.delete(
    "/materiales/{material_id}",  # Ruta
    response_model=Mensaje,  # Respuesta: un mensaje
    summary="Eliminar un material (RF31)",  # Título
    description=(  # Explicación
        "No se elimina si una receta activa lo usa (400). Con historial en el kardex se desactiva (borrado "
        "lógico); si no, se borra.\n\n**Rol requerido:** encargado."
    ),
    responses=respuestas_error(400, 401, 403, 404),  # Errores posibles
)
# Recibe el id, el servicio y el encargado
def eliminar_material(material_id: int, servicio: Servicio, encargado: Encargado):
    # Elimina y devuelve el mensaje
    return {"mensaje": servicio.eliminar_material(material_id, encargado)}


# Endpoint POST /api/v1/inventario/movimientos
@router.post(
    "/movimientos",  # Ruta
    response_model=MovimientoSalida,  # Respuesta: el movimiento creado
    status_code=status.HTTP_201_CREATED,  # Código 201
    summary="Registrar entrada, salida o merma (RF36, RF37)",  # Título
    description=(  # Explicación
        "Proceso de negocio. Actualiza el stock y crea la fila del kardex en una sola transacción. Una salida "
        "o merma no puede dejar el stock negativo (400). En una merma el concepto es la razón.\n\n"
        "**Rol requerido:** encargado."
    ),
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores posibles
)
# Recibe el cuerpo, el servicio y el encargado
def registrar_movimiento(datos: MovimientoCrear, servicio: Servicio, encargado: Encargado):
    # Registra y devuelve el movimiento
    return servicio.registrar_movimiento(datos, encargado)


# Endpoint GET /api/v1/inventario/kardex
@router.get(
    "/kardex",  # Ruta
    response_model=Pagina[MovimientoSalida],  # Respuesta: página de movimientos
    summary="Kardex e historial de mermas (RF35, RF38)",  # Título
    description=(  # Explicación
        "Movimientos con responsable, entrada, salida y saldo final. Filtros por material, tipo (use "
        "tipo=MERMA para el historial de mermas) y rango de fechas.\n\n**Rol requerido:** encargado."
    ),
    responses=respuestas_error(401, 403, 422),  # Errores posibles
)
# Filtros en la URL; solo el encargado
def kardex(filtros: Annotated[FiltrosKardex, Query()], servicio: Servicio, _: Encargado):
    # Devuelve la página del kardex
    return servicio.kardex(filtros)
