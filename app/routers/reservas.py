"""Endpoints de reservas, compras y consumos de almuerzo."""

# Annotated asocia dependencias o fuentes de datos a un tipo
from typing import Annotated

# Herramientas de FastAPI
from fastapi import APIRouter, Depends, Query, status

# Documenta los errores en Swagger
from app.core.errores import respuestas_error
# Comensal = aprendiz, instructor o invitado; CualquierRol; Encargado
from app.core.permisos import Comensal, CualquierRol, Encargado
# Sesión de base de datos
from app.database.conexion import SesionDB
# Respuesta paginada
from app.schemas.comunes import Pagina
# Esquemas de reservas
from app.schemas.reserva import EstadoPagoEntrada, FiltrosMisReservas, FiltrosReserva, ReservaCrear, ReservaSalida
# Servicio con las reglas de reservas
from app.services.reserva_service import ReservaService

# Router con prefijo /reservas
router = APIRouter(prefix="/reservas", tags=["Reservas y consumos"])


# Dependencia que crea el servicio
def obtener_servicio(db: SesionDB) -> ReservaService:
    # Devuelve un ReservaService nuevo
    return ReservaService(db)


# Atajo para recibir el servicio
Servicio = Annotated[ReservaService, Depends(obtener_servicio)]


# Endpoint POST /api/v1/reservas
@router.post(
    "",  # Ruta = /reservas
    response_model=ReservaSalida,  # Respuesta: la reserva creada
    status_code=status.HTTP_201_CREATED,  # Código 201
    summary="Reservar o comprar un almuerzo (RF09, RF11, RF12)",  # Título
    description=(  # Explicación
        "Proceso de negocio. Reglas: horario de 7:00 a. m. a 9:00 p. m., una reserva por persona y menú (409), "
        "menú activo, de hoy o futuro y con cupo (400). El precio lo calcula la API: aprendiz $5.000, "
        "beneficiario $0, invitado $8.000; al instructor se le carga a su cuenta mensual. Descuenta el cupo "
        "(RF17).\n\n**Rol requerido:** aprendiz, instructor o invitado."
    ),
    responses=respuestas_error(400, 401, 403, 404, 409, 422),  # Errores posibles
)
# Recibe {"menu_id": ...}, el servicio y el comensal autenticado
def reservar(datos: ReservaCrear, servicio: Servicio, usuario: Comensal):
    # Crea y devuelve la reserva
    return servicio.reservar(datos, usuario)


# Endpoint GET /api/v1/reservas/mias (va antes de /{reserva_id})
@router.get(
    "/mias",  # Ruta
    response_model=Pagina[ReservaSalida],  # Respuesta: página de reservas propias
    summary="Mis consumos (RF14, RF27)",  # Título
    description="Historial propio, del más reciente al más antiguo.\n\n**Rol requerido:** aprendiz, instructor o invitado.",  # Explicación
    responses=respuestas_error(401, 403, 422),  # Errores posibles
)
# Filtros en la URL y el comensal autenticado
def mis_reservas(filtros: Annotated[FiltrosMisReservas, Query()], servicio: Servicio, usuario: Comensal):
    # Devuelve sus reservas
    return servicio.listar_mias(usuario, filtros)


# Endpoint GET /api/v1/reservas
@router.get(
    "",  # Ruta = /reservas
    response_model=Pagina[ReservaSalida],  # Respuesta: página de reservas
    summary="Listar reservas y ventas (RF13)",  # Título
    description="Filtros por fecha, rango, estado, tipo, usuario y ficha.\n\n**Rol requerido:** encargado.",  # Explicación
    responses=respuestas_error(401, 403, 422),  # Errores posibles
)
# Filtros en la URL; solo el encargado
def listar_reservas(filtros: Annotated[FiltrosReserva, Query()], servicio: Servicio, _: Encargado):
    # Devuelve la página de reservas
    return servicio.listar(filtros)


# Endpoint GET /api/v1/reservas/{reserva_id}
@router.get(
    "/{reserva_id}",  # Ruta con el id
    response_model=ReservaSalida,  # Respuesta: una reserva
    summary="Consultar una reserva (RF10)",  # Título
    description="El Encargado ve cualquiera; los demás, solo las propias.\n\n**Rol requerido:** cualquiera.",  # Explicación
    responses=respuestas_error(401, 403, 404),  # Errores posibles
)
# Cualquier usuario autenticado (el servicio revisa que sea suya si no es encargado)
def obtener_reserva(reserva_id: int, servicio: Servicio, usuario: CualquierRol):
    # Devuelve la reserva
    return servicio.obtener(reserva_id, usuario)


# Endpoint PATCH /api/v1/reservas/{reserva_id}/cancelar
@router.patch(
    "/{reserva_id}/cancelar",  # Ruta
    response_model=ReservaSalida,  # Respuesta: la reserva cancelada
    summary="Cancelar mi reserva",  # Título
    description=(  # Explicación
        "Cambio de estado. Solo la propia reserva, sin pagar, de hoy o de un día futuro y dentro del horario. "
        "El cupo vuelve al menú.\n\n**Rol requerido:** aprendiz, instructor o invitado."
    ),
    responses=respuestas_error(400, 401, 403, 404),  # Errores posibles
)
# Recibe el id y el comensal autenticado
def cancelar_reserva(reserva_id: int, servicio: Servicio, usuario: Comensal):
    # Cancela y devuelve la reserva
    return servicio.cancelar(reserva_id, usuario)


# Endpoint PATCH /api/v1/reservas/{reserva_id}/pago
@router.patch(
    "/{reserva_id}/pago",  # Ruta
    response_model=ReservaSalida,  # Respuesta: la reserva actualizada
    summary="Marcar Pagado o No pagado (RF42)",  # Título
    description=(  # Explicación
        "Cambio de estado del pago de un aprendiz o invitado; queda guardado con fecha y usuario. Los "
        "instructores se pagan en la cartera.\n\n**Rol requerido:** encargado."
    ),
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores posibles
)
# Recibe el id, {"estado": "PAGADO" o "NO_PAGADO"}, el servicio y el encargado
def marcar_pago(reserva_id: int, datos: EstadoPagoEntrada, servicio: Servicio, encargado: Encargado):
    # Marca el pago y devuelve la reserva
    return servicio.marcar_pago(reserva_id, datos, encargado)
