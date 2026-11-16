"""Endpoints de la cartera de deudas y la cuenta mensual de instructores."""

# Annotated asocia dependencias o fuentes de datos a un tipo
from typing import Annotated

# Herramientas de FastAPI
from fastapi import APIRouter, Depends, Query, status

# Documenta los errores en Swagger
from app.core.errores import respuestas_error
# Encargado y Instructor (cada uno deja pasar solo a su rol)
from app.core.permisos import Encargado, Instructor
# Sesión de base de datos
from app.database.conexion import SesionDB
# Esquemas de la cartera
from app.schemas.cartera import CarteraSalida, DetalleCartera, MiCuenta, PagoCrear, PagoRegistrado
# Servicio con las reglas de la cartera
from app.services.cartera_service import CarteraService

# Router con prefijo /cartera
router = APIRouter(prefix="/cartera", tags=["Cartera de deudas"])


# Dependencia que crea el servicio
def obtener_servicio(db: SesionDB) -> CarteraService:
    # Devuelve un CarteraService nuevo
    return CarteraService(db)


# Atajo para recibir el servicio
Servicio = Annotated[CarteraService, Depends(obtener_servicio)]


# Endpoint GET /api/v1/cartera
@router.get(
    "",  # Ruta = /cartera
    response_model=CarteraSalida,  # Respuesta: resumen y deudores
    summary="Instructores con deuda (RF22, RF24, RF25)",  # Título
    description=(  # Explicación
        "Cálculo: saldo = consumido - pagado; días vencidos y estado (ACTIVA o VENCIDA) según el corte "
        "mensual. Incluye resumen: deudores, deuda total, promedio y mayor deuda.\n\n**Rol requerido:** encargado."
    ),
    responses=respuestas_error(401, 403, 422),  # Errores posibles
)
# Función con los parámetros en varias líneas
def listar_cartera(
    # Servicio de la cartera
    servicio: Servicio,
    # Exige el rol encargado
    _: Encargado,
    # Parámetro ?solo_vencidas=true en la URL (falso por defecto)
    solo_vencidas: Annotated[bool, Query(description="true para ver solo las deudas vencidas")] = False,
):
    # Devuelve el resumen y la lista de deudores
    return servicio.listar(solo_vencidas)


# Endpoint GET /api/v1/cartera/mi-cuenta (va antes de /{instructor_id})
@router.get(
    "/mi-cuenta",  # Ruta
    response_model=MiCuenta,  # Respuesta: la cuenta mensual
    summary="Mi cuenta mensual (RF26)",  # Título
    description="Total consumido, saldo, consumos del mes y próximo corte.\n\n**Rol requerido:** instructor.",  # Explicación
    responses=respuestas_error(401, 403),  # Errores posibles
)
# Solo el instructor
def mi_cuenta(servicio: Servicio, instructor: Instructor):
    # Devuelve su cuenta mensual
    return servicio.mi_cuenta(instructor)


# Endpoint GET /api/v1/cartera/{instructor_id}
@router.get(
    "/{instructor_id}",  # Ruta con el id
    response_model=DetalleCartera,  # Respuesta: deuda e historial de pagos
    summary="Detalle de la cuenta de un instructor",  # Título
    description="Deuda e historial de pagos.\n\n**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(400, 401, 403, 404),  # Errores posibles
)
# Recibe el id del instructor; solo el encargado
def detalle_cartera(instructor_id: int, servicio: Servicio, _: Encargado):
    # Devuelve el detalle
    return servicio.detalle(instructor_id)


# Endpoint POST /api/v1/cartera/{instructor_id}/pagos
@router.post(
    "/{instructor_id}/pagos",  # Ruta
    response_model=PagoRegistrado,  # Respuesta: pago y saldos
    status_code=status.HTTP_201_CREATED,  # Código 201
    summary="Registrar un pago (RF23)",  # Título
    description=(  # Explicación
        "Proceso de negocio. El pago no puede ser mayor que la deuda; si la salda, los consumos pendientes "
        "quedan PAGADOS y la cuenta queda al día.\n\n**Rol requerido:** encargado."
    ),
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores posibles
)
# Recibe el id, {"valor", "metodo", "observacion"}, el servicio y el encargado
def registrar_pago(instructor_id: int, datos: PagoCrear, servicio: Servicio, encargado: Encargado):
    # Registra el pago y devuelve el resultado
    return servicio.registrar_pago(instructor_id, datos, encargado)
