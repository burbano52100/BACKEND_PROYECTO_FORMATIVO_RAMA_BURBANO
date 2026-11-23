# Funciones que consultan y guardan las reservas en la base de datos

# Modelo de reserva
from app.models.reserva import modelo_reserva
# Función para paginar
from app.repositories.paginacion import paginar



# Busca la reserva que no está cancelada de una persona en un menú
def buscar_activa_de_usuario(bd, menu_id, usuario_id):
    # Hago la consulta y traigo la primera (o None si no tiene)
    return bd.query(modelo_reserva).filter(
        modelo_reserva.menu_id == menu_id,  # De este menú
        modelo_reserva.usuario_id == usuario_id,  # De esta persona
        modelo_reserva.estado != "CANCELADA",  # Que no esté cancelada
    ).first()


# Trae las reservas de una persona de la más nueva a la más vieja
def listar_de_usuario(bd, usuario_id, estado):
    # Traigo las reservas de la persona
    consulta = bd.query(modelo_reserva).filter(modelo_reserva.usuario_id == usuario_id)
    # Si mandaron estado
    if estado is not None:
        # Filtro por estado
        consulta = consulta.filter(modelo_reserva.estado == estado)
    # Ordeno de la más nueva a la más vieja y devuelvo la lista
    return consulta.order_by(modelo_reserva.id.desc()).all()


# Trae todas las reservas con los filtros
def listar(bd, menu_id, estado, tipo, saltar, limite):
    # Empiezo con todas las reservas
    consulta = bd.query(modelo_reserva)
    # Si mandaron el menú
    if menu_id is not None:
        # Filtro por el menú
        consulta = consulta.filter(modelo_reserva.menu_id == menu_id)
    # Si mandaron estado
    if estado is not None:
        # Filtro por estado
        consulta = consulta.filter(modelo_reserva.estado == estado)
    # Si mandaron tipo
    if tipo is not None:
        # Filtro por tipo
        consulta = consulta.filter(modelo_reserva.tipo == tipo)
    # Ordeno de la más nueva a la más vieja
    consulta = consulta.order_by(modelo_reserva.id.desc())
    # Pagino y devuelvo la lista
    return paginar(consulta, saltar, limite)


# Trae las reservas de un menú que no están canceladas
def listar_activas_por_menu(bd, menu_id):
    # Hago la consulta
    return bd.query(modelo_reserva).filter(modelo_reserva.menu_id == menu_id, modelo_reserva.estado != "CANCELADA").all()


# Cuenta todas las reservas de un menú
def contar_por_menu(bd, menu_id):
    # Hago la consulta y cuento
    return bd.query(modelo_reserva).filter(modelo_reserva.menu_id == menu_id).count()


# Cuenta las reservas de aprendices de un menú que no están canceladas
def contar_de_aprendices_por_menu(bd, menu_id):
    # Hago la consulta y cuento
    return bd.query(modelo_reserva).filter(
        modelo_reserva.menu_id == menu_id,  # Del menú de ese día
        modelo_reserva.tipo.in_(["APRENDIZ", "BENEFICIARIO"]),  # Solo aprendices
        modelo_reserva.estado != "CANCELADA",  # Que no estén canceladas
    ).count()
