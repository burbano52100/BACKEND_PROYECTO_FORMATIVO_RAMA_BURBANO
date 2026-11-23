# Rutas para reservar almuerzos, cancelarlos y marcar los pagos

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
# Listas de roles que pueden entrar
from app.core.roles import solo_encargado, comensales
# Esquemas que uso
from app.schemas.reserva import reserva_crear, pago_reserva_datos
# Servicio con la lógica de las reservas
from app.services import reserva_service

# Función que documenta en /docs los errores que puede responder cada ruta
from app.core.errores import respuestas_error

# Creo el enrutador, todas las rutas empiezan con /reservas
enrutador = APIRouter(prefix="/reservas", tags=["Reservas"])


# Ruta para reservar o comprar un almuerzo (aprendiz, instructor e invitado)
@enrutador.post(
    "", status_code=201,
    summary="Reservar o comprar un almuerzo",  # Título corto que sale en /docs
    description="La API pone el precio según el rol: aprendiz $5.000, beneficiario $0, instructor $5.000 a su cuenta del mes e invitado $8.000. Solo se reserva entre las 7:00 a. m. y las 9:00 p. m., una vez por menú (409), y no se reservan menús agotados, inactivos o de días pasados. **Rol requerido:** aprendiz, instructor o invitado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 404, 409, 422),  # Errores que puede responder
)
def reservar(datos: reserva_crear, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo los que comen pueden reservar (el encargado no)
    verificar_rol(usuario_actual, comensales)
    # Le pido al servicio que haga la reserva
    reserva = reserva_service.reservar(bd, datos, usuario_actual)
    # Devuelvo la reserva
    return reserva


# Ruta para ver mis reservas (aprendiz, instructor e invitado)
@enrutador.get(
    "/mias",
    summary="Ver mis reservas",  # Título corto que sale en /docs
    description="Lista las reservas de quien inició sesión. **Rol requerido:** aprendiz, instructor o invitado.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403),  # Errores que puede responder
)
def mis_reservas(estado: Optional[str] = None, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo los que comen tienen reservas
    verificar_rol(usuario_actual, comensales)
    # Le pido mis reservas al servicio
    lista = reserva_service.mis_reservas(bd, usuario_actual, estado)
    # Devuelvo la lista
    return lista


# Ruta para ver todas las reservas (solo el encargado)
@enrutador.get(
    "",
    summary="Ver todas las reservas",  # Título corto que sale en /docs
    description="Lista las reservas con filtros (fecha, estado y tipo) y paginación. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403, 422),  # Errores que puede responder
)
def listar_reservas(
    fecha: Optional[date] = None,  # Fecha del menú
    estado: Optional[str] = None,  # Estado de la reserva
    tipo: Optional[str] = None,  # Tipo de reserva
    saltar: int = 0,  # Cuántos registros me salto
    limite: int = 100,  # Cuántos registros traigo como máximo
    bd: Session = Depends(obtener_bd),  # Sesión de la base de datos
    usuario_actual: modelo_usuario = Depends(obtener_usuario_actual),  # Usuario que hace la petición
):
    # Solo el encargado puede ver todas las reservas
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido la lista al servicio
    lista = reserva_service.listar_reservas(bd, fecha, estado, tipo, saltar, limite)
    # Devuelvo la lista
    return lista


# Ruta para ver una reserva por su id
@enrutador.get(
    "/{reserva_id}",
    summary="Ver una reserva",  # Título corto que sale en /docs
    description="Cada persona solo puede ver sus propias reservas; el encargado puede ver todas. **Rol requerido:** cualquiera con sesión iniciada.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403, 404, 422),  # Errores que puede responder
)
def ver_reserva(reserva_id: int, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Le pido la reserva al servicio (revisa que sea mía o que yo sea el encargado)
    reserva = reserva_service.ver_reserva(bd, reserva_id, usuario_actual)
    # Devuelvo la reserva
    return reserva


# Ruta para cancelar mi reserva
@enrutador.patch(
    "/{reserva_id}/cancelar",
    summary="Cancelar mi reserva",  # Título corto que sale en /docs
    description="Cancela una reserva propia dentro del horario de reservas. El almuerzo vuelve a quedar disponible. **Rol requerido:** aprendiz, instructor o invitado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores que puede responder
)
def cancelar_reserva(reserva_id: int, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo los que comen pueden cancelar
    verificar_rol(usuario_actual, comensales)
    # Le pido al servicio que cancele la reserva
    reserva = reserva_service.cancelar_reserva(bd, reserva_id, usuario_actual)
    # Devuelvo la reserva
    return reserva


# Ruta para marcar si una reserva se pagó o no (solo el encargado)
@enrutador.patch(
    "/{reserva_id}/pago",
    summary="Marcar el pago de una reserva",  # Título corto que sale en /docs
    description="Marca una reserva como PAGADO o NO_PAGADO. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores que puede responder
)
def marcar_pago(reserva_id: int, datos: pago_reserva_datos, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede marcar pagos
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que marque el pago
    reserva = reserva_service.marcar_pago(bd, reserva_id, datos)
    # Devuelvo la reserva
    return reserva
