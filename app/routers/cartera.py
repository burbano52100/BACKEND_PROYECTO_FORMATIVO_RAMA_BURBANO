# Rutas de la cartera: lo que deben los instructores y los pagos que hacen

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
from app.core.roles import solo_encargado, solo_instructor
# Esquema para registrar un pago
from app.schemas.cartera import pago_crear
# Servicio con la lógica de la cartera
from app.services import cartera_service

# Función que documenta en /docs los errores que puede responder cada ruta
from app.core.errores import respuestas_error

# Creo el enrutador, todas las rutas empiezan con /cartera
enrutador = APIRouter(prefix="/cartera", tags=["Cartera"])


# Ruta para ver los instructores que deben (solo el encargado)
@enrutador.get(
    "",
    summary="Instructores que deben",  # Título corto que sale en /docs
    description="Lista los instructores con deuda, cuánto deben y si la deuda está VENCIDA (un consumo sin pagar de hace más de 30 días). **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403),  # Errores que puede responder
)
def listar_cartera(solo_vencidas: bool = False, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido la cartera al servicio
    cartera = cartera_service.listar_cartera(bd, solo_vencidas)
    # Devuelvo el resumen y la lista
    return cartera


# Ruta para que el instructor vea su propia cuenta del mes
@enrutador.get(
    "/mi-cuenta",
    summary="Mi cuenta del mes",  # Título corto que sale en /docs
    description="El instructor ve sus consumos del mes, lo que pagó y lo que debe. **Rol requerido:** instructor.",  # Explicación y rol que se necesita
    responses=respuestas_error(401, 403),  # Errores que puede responder
)
def mi_cuenta(bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo los instructores tienen cuenta
    verificar_rol(usuario_actual, solo_instructor)
    # Le pido mi cuenta al servicio
    cuenta = cartera_service.mi_cuenta(bd, usuario_actual)
    # Devuelvo la cuenta
    return cuenta


# Ruta para ver la cuenta de un instructor (solo el encargado)
@enrutador.get(
    "/{instructor_id}",
    summary="Cuenta de un instructor",  # Título corto que sale en /docs
    description="Consumos, pagos y deuda de un instructor. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores que puede responder
)
def ver_cuenta_instructor(instructor_id: int, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido la cuenta del instructor al servicio
    cuenta = cartera_service.ver_cuenta_instructor(bd, instructor_id)
    # Devuelvo la cuenta
    return cuenta


# Ruta para registrar un pago de un instructor (solo el encargado)
@enrutador.post(
    "/{instructor_id}/pagos", status_code=201,
    summary="Registrar un pago",  # Título corto que sale en /docs
    description="Registra un pago de un instructor. No puede ser mayor que lo que debe; si paga todo, sus consumos quedan PAGADOS. **Rol requerido:** encargado.",  # Explicación y rol que se necesita
    responses=respuestas_error(400, 401, 403, 404, 422),  # Errores que puede responder
)
def registrar_pago(instructor_id: int, datos: pago_crear, bd: Session = Depends(obtener_bd), usuario_actual: modelo_usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede registrar pagos
    verificar_rol(usuario_actual, solo_encargado)
    # Le pido al servicio que registre el pago
    respuesta = cartera_service.registrar_pago(bd, instructor_id, datos)
    # Devuelvo los datos del pago
    return respuesta
