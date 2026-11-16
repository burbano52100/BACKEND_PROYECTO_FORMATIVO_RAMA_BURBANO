"""Endpoints de recetas y productos (solo el Encargado)."""

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
# Esquemas de recetas
from app.schemas.receta import FiltrosReceta, RecetaActualizar, RecetaCrear, RecetaSalida
# Servicio con las reglas de recetas
from app.services.receta_service import RecetaService

# Router con prefijo /recetas
router = APIRouter(prefix="/recetas", tags=["Recetas"])


# Dependencia que crea el servicio
def obtener_servicio(db: SesionDB) -> RecetaService:
    # Devuelve un RecetaService nuevo
    return RecetaService(db)


# Atajo para recibir el servicio
Servicio = Annotated[RecetaService, Depends(obtener_servicio)]

# Texto compartido por varios endpoints (se reutiliza en las descripciones)
DESCRIPCION_COSTOS = (
    "Cada receta incluye el cálculo de costo de producción (suma de cantidad x costo unitario), margen, "
    "margen en porcentaje y alerta si el margen es negativo (RF34)."
)


# Endpoint GET /api/v1/recetas
@router.get(
    "",  # Ruta = /recetas
    response_model=Pagina[RecetaSalida],  # Respuesta: página de recetas
    summary="Listar recetas (RF33)",  # Título
    description=f"{DESCRIPCION_COSTOS}\n\n**Rol requerido:** encargado.",  # Explicación (f-string inserta el texto)
    responses=respuestas_error(401, 403, 422),  # Errores posibles
)
# Filtros en la URL; solo el encargado
def listar_recetas(filtros: Annotated[FiltrosReceta, Query()], servicio: Servicio, _: Encargado):
    # Devuelve la página de recetas con sus costos
    return servicio.listar(filtros)


# Endpoint GET /api/v1/recetas/{receta_id}
@router.get(
    "/{receta_id}",  # Ruta con el id
    response_model=RecetaSalida,  # Respuesta: una receta
    summary="Consultar una receta con su costo (RF34)",  # Título
    description=f"{DESCRIPCION_COSTOS}\n\n**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(401, 403, 404),  # Errores posibles
)
# Recibe el id
def obtener_receta(receta_id: int, servicio: Servicio, _: Encargado):
    # Devuelve la receta con sus costos
    return servicio.obtener(receta_id)


# Endpoint POST /api/v1/recetas
@router.post(
    "",  # Ruta = /recetas
    response_model=RecetaSalida,  # Respuesta: la receta creada
    status_code=status.HTTP_201_CREATED,  # Código 201
    summary="Crear una receta",  # Título
    description=(  # Explicación
        "Nombre único (409). Los ingredientes se eligen del inventario (404 si no existen), sin repetirse y con "
        "cantidad mayor a 0.\n\n**Rol requerido:** encargado."
    ),
    responses=respuestas_error(400, 401, 403, 404, 409, 422),  # Errores posibles
)
# Recibe el cuerpo, el servicio y el encargado
def crear_receta(datos: RecetaCrear, servicio: Servicio, encargado: Encargado):
    # Crea y devuelve la receta
    return servicio.crear(datos, encargado)


# Endpoint PATCH /api/v1/recetas/{receta_id}
@router.patch(
    "/{receta_id}",  # Ruta
    response_model=RecetaSalida,  # Respuesta: la receta actualizada
    summary="Actualizar una receta",  # Título
    description="Si se envían ingredientes, reemplazan la fórmula y el costo se recalcula.\n\n**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(400, 401, 403, 404, 409, 422),  # Errores posibles
)
# Recibe el id, los cambios, el servicio y el encargado
def actualizar_receta(receta_id: int, datos: RecetaActualizar, servicio: Servicio, encargado: Encargado):
    # Actualiza y devuelve la receta
    return servicio.actualizar(receta_id, datos, encargado)


# Endpoint DELETE /api/v1/recetas/{receta_id}
@router.delete(
    "/{receta_id}",  # Ruta
    response_model=Mensaje,  # Respuesta: un mensaje
    summary="Eliminar una receta",  # Título
    description="**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(401, 403, 404),  # Errores posibles
)
# Recibe el id; solo el encargado
def eliminar_receta(receta_id: int, servicio: Servicio, _: Encargado):
    # Elimina y devuelve el mensaje
    return {"mensaje": servicio.eliminar(receta_id)}
