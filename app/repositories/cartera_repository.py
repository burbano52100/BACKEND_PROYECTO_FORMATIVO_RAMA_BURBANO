# Funciones que consultan y guardan lo de la cartera de los instructores

# Modelos de reservas y pagos
from app.models.reserva import modelo_reserva, modelo_pago_instructor
# Modelo de usuarios para bloquear al instructor mientras se registra un pago
from app.models.usuario import modelo_usuario


def buscar_instructor_para_pago(bd, instructor_id):
    return bd.query(modelo_usuario).filter(modelo_usuario.id == instructor_id).with_for_update().first()


# Trae los consumos de un instructor que todavía están pendientes de pago
def listar_consumos(bd, instructor_id):
    # Hago la consulta
    return bd.query(modelo_reserva).filter(
        modelo_reserva.usuario_id == instructor_id,  # Del instructor
        modelo_reserva.tipo == "INSTRUCTOR",  # Que sean consumos de instructor
        modelo_reserva.estado.in_(["PENDIENTE", "NO_PAGADO"]),  # Que no estén pagados ni cancelados
    ).all()


# Trae los consumos de un instructor que están pendientes de pago
def listar_consumos_pendientes(bd, instructor_id):
    # Hago la consulta
    return bd.query(modelo_reserva).filter(modelo_reserva.usuario_id == instructor_id, modelo_reserva.estado == "PENDIENTE").all()



# Trae los pagos de un instructor del más nuevo al más viejo
def listar_pagos(bd, instructor_id):
    # Hago la consulta
    return bd.query(modelo_pago_instructor).filter(modelo_pago_instructor.instructor_id == instructor_id).order_by(modelo_pago_instructor.id.desc()).all()
