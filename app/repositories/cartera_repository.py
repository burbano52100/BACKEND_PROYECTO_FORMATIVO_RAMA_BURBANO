# Funciones que consultan y guardan lo de la cartera de los instructores

# Modelos de reservas y pagos
from app.models.reserva import modelo_reserva, modelo_pago_instructor


# Trae los consumos de un instructor que no están cancelados
def listar_consumos(bd, instructor_id):
    # Hago la consulta
    return bd.query(modelo_reserva).filter(
        modelo_reserva.usuario_id == instructor_id,  # Del instructor
        modelo_reserva.tipo == "INSTRUCTOR",  # Que sean consumos de instructor
        modelo_reserva.estado != "CANCELADA",  # Que no estén cancelados
    ).all()


# Trae los consumos de un instructor que están pendientes de pago
def listar_consumos_pendientes(bd, instructor_id):
    # Hago la consulta
    return bd.query(modelo_reserva).filter(modelo_reserva.usuario_id == instructor_id, modelo_reserva.estado == "PENDIENTE").all()



# Trae los pagos de un instructor del más nuevo al más viejo
def listar_pagos(bd, instructor_id):
    # Hago la consulta
    return bd.query(modelo_pago_instructor).filter(modelo_pago_instructor.instructor_id == instructor_id).order_by(modelo_pago_instructor.id.desc()).all()
