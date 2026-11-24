# Funciones que consultan y guardan los menús en la base de datos

# Modelo de menú
from app.models.menu import modelo_menu
# Función para paginar
from app.repositories.paginacion import paginar



# Busca un menú y lo bloquea para que dos reservas no usen el mismo cupo al mismo tiempo
def buscar_para_reserva(bd, menu_id):
    return bd.query(modelo_menu).filter(modelo_menu.id == menu_id).with_for_update().first()


# Busca el menú de una fecha (activo o no)
def buscar_por_fecha(bd, fecha):
    # Hago la consulta y traigo el primero (o None si no existe)
    return bd.query(modelo_menu).filter(modelo_menu.fecha == fecha).first()


# Busca el menú activo de una fecha
def buscar_activo_por_fecha(bd, fecha):
    # Hago la consulta y traigo el primero (o None si no existe)
    return bd.query(modelo_menu).filter(modelo_menu.fecha == fecha, modelo_menu.activo == True).first()


# Trae los menús activos desde una fecha en adelante ordenados por fecha
def listar_proximos(bd, desde):
    # Hago la consulta
    return bd.query(modelo_menu).filter(modelo_menu.fecha >= desde, modelo_menu.activo == True).order_by(modelo_menu.fecha).all()


# Trae la lista de menús con los filtros
def listar(bd, desde, hasta, activo, saltar, limite):
    # Empiezo con todos los menús
    consulta = bd.query(modelo_menu)
    # Si mandaron fecha inicial
    if desde is not None:
        # Solo los menús desde esa fecha
        consulta = consulta.filter(modelo_menu.fecha >= desde)
    # Si mandaron fecha final
    if hasta is not None:
        # Solo los menús hasta esa fecha
        consulta = consulta.filter(modelo_menu.fecha <= hasta)
    # Si mandaron activo
    if activo is not None:
        # Filtro por activo
        consulta = consulta.filter(modelo_menu.activo == activo)
    # Ordeno del más nuevo al más viejo
    consulta = consulta.order_by(modelo_menu.fecha.desc())
    # Pagino y devuelvo la lista
    return paginar(consulta, saltar, limite)
