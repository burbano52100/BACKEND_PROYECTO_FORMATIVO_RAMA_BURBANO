# Lógica de las reservas: reservar, cancelar y marcar los pagos

# date es una fecha
from datetime import date

# Modelo de reserva para crear reservas nuevas
from app.models.reserva import modelo_reserva
# Horario en el que se puede reservar (para los mensajes)
from app.core.config import hora_apertura, hora_cierre
# Funciones para responder los errores
from app.core.excepciones import error_regla, error_sin_permiso, error_no_encontrado, error_duplicado
# Función que dice si se puede reservar a esta hora
from app.core.tiempo import esta_en_horario
# Funciones para buscar y guardar en la base de datos
from app.database.conexion import guardar, guardar_cambios, buscar_por_id
# Repositorios que uso
from app.repositories import menu_repository, reserva_repository
# Servicio de menús para buscar el menú y calcular el precio
from app.services import menu_service


# Función que convierte una reserva en un diccionario para responder
def convertir_reserva(reserva):
    # Armo el diccionario con los datos de la reserva
    return {
        "id": reserva.id,  # Id de la reserva
        "menu_id": reserva.menu_id,  # Id del menú
        "fecha_menu": reserva.menu.fecha,  # Fecha del menú
        "nombre_menu": reserva.menu.nombre,  # Nombre del plato
        "usuario_id": reserva.usuario_id,  # Id de quien reservó
        "nombre_usuario": reserva.usuario.nombre,  # Nombre de quien reservó
        "tipo": reserva.tipo,  # APRENDIZ, BENEFICIARIO, INSTRUCTOR o INVITADO
        "valor": reserva.valor,  # Lo que tiene que pagar
        "estado": reserva.estado,  # Estado de la reserva
        "fecha_creacion": reserva.fecha_creacion,  # Cuándo se hizo
    }


# Función que convierte una lista de reservas
def convertir_lista(reservas):
    # Aquí voy a guardar las reservas convertidas
    lista = []
    # Recorro las reservas
    for reserva in reservas:
        # Agrego cada reserva convertida
        lista.append(convertir_reserva(reserva))
    # Devuelvo la lista
    return lista


# Función que busca una reserva y si no existe responde 404
def buscar_reserva_existente(bd, reserva_id):
    # Busco la reserva
    reserva = buscar_por_id(bd, modelo_reserva, reserva_id)
    # Si no existe
    if reserva is None:
        # Respondo 404
        error_no_encontrado("La reserva no existe")
    # Devuelvo la reserva
    return reserva


# Función para reservar o comprar un almuerzo
def reservar(bd, datos, usuario):
    # Reviso que esté en el horario
    if not esta_en_horario():
        # Respondo 400
        error_regla("Solo se puede reservar entre las " + str(hora_apertura) + ":00 y las " + str(hora_cierre) + ":00")
    # Busco el menú (si no existe responde 404)
    menu = menu_service.buscar_menu_existente(bd, datos.menu_id)
    # Si el menú está inactivo
    if menu.activo == False:
        # Respondo 400
        error_regla("El menú no está disponible")
    # Si el menú es de un día que ya pasó
    if menu.fecha < date.today():
        # Respondo 400
        error_regla("No se puede reservar el menú de un día que ya pasó")
    # Si ya no quedan almuerzos
    if menu.cantidad_disponible <= 0:
        # Respondo 400
        error_regla("El menú está agotado")
    # Si la persona ya tiene una reserva para este menú
    if reserva_repository.buscar_activa_de_usuario(bd, menu.id, usuario.id) is not None:
        # Respondo 409 porque ese valor no se puede repetir
        error_duplicado("Ya tiene una reserva para este menú")
    # Lo que tiene que pagar es el mismo precio que le sale en el menú
    valor = menu_service.calcular_precio(usuario, menu)
    # Saco el nombre del rol
    rol = usuario.rol.nombre
    # Si es aprendiz beneficiario
    if rol == "aprendiz" and usuario.es_beneficiario == True:
        # El tipo es beneficiario
        tipo = "BENEFICIARIO"
        # Queda pagado de una vez porque no paga nada
        estado = "PAGADO"
    # Si es aprendiz normal
    elif rol == "aprendiz":
        # El tipo es aprendiz
        tipo = "APRENDIZ"
        # Queda reservado hasta que pague
        estado = "RESERVADO"
    # Si es instructor
    elif rol == "instructor":
        # El tipo es instructor
        tipo = "INSTRUCTOR"
        # Queda pendiente porque lo paga en su cuenta del mes
        estado = "PENDIENTE"
    # Si es invitado
    else:
        # El tipo es invitado
        tipo = "INVITADO"
        # Queda reservado hasta que pague
        estado = "RESERVADO"
    # Le quito un almuerzo a los disponibles
    menu.cantidad_disponible = menu.cantidad_disponible - 1
    # Creo la reserva
    nueva_reserva = modelo_reserva(
        menu_id=menu.id,  # Menú
        usuario_id=usuario.id,  # Persona
        tipo=tipo,  # Tipo
        valor=valor,  # Valor
        estado=estado,  # Estado
    )
    # Guardo la reserva y el menú al mismo tiempo
    guardar(bd, nueva_reserva)
    # Devuelvo la reserva
    return convertir_reserva(nueva_reserva)


# Función para ver mis reservas
def mis_reservas(bd, usuario, estado):
    # Traigo las reservas de la persona
    reservas = reserva_repository.listar_de_usuario(bd, usuario.id, estado)
    # Devuelvo la lista convertida
    return convertir_lista(reservas)


# Función para ver todas las reservas
def listar_reservas(bd, fecha, estado, tipo, saltar, limite):
    # Al principio no filtro por menú
    menu_id = None
    # Si mandaron fecha
    if fecha is not None:
        # Busco el menú de esa fecha
        menu = menu_repository.buscar_por_fecha(bd, fecha)
        # Si no hay menú ese día
        if menu is None:
            # No hay reservas
            return []
        # Filtro por el menú de ese día
        menu_id = menu.id
    # Traigo las reservas
    reservas = reserva_repository.listar(bd, menu_id, estado, tipo, saltar, limite)
    # Devuelvo la lista convertida
    return convertir_lista(reservas)


# Función para ver una reserva
def ver_reserva(bd, reserva_id, usuario):
    # Busco la reserva
    reserva = buscar_reserva_existente(bd, reserva_id)
    # Si no es el encargado solo puede ver sus propias reservas
    if usuario.rol.nombre != "encargado" and reserva.usuario_id != usuario.id:
        # Respondo 403
        error_sin_permiso("Solo puede ver sus propias reservas")
    # Devuelvo la reserva
    return convertir_reserva(reserva)


# Función para cancelar mi reserva
def cancelar_reserva(bd, reserva_id, usuario):
    # Busco la reserva
    reserva = buscar_reserva_existente(bd, reserva_id)
    # Solo puede cancelar sus propias reservas
    if reserva.usuario_id != usuario.id:
        # Respondo 403
        error_sin_permiso("Solo puede cancelar sus propias reservas")
    # Al principio digo que no se puede cancelar
    se_puede_cancelar = False
    # Si está reservada o pendiente sí se puede
    if reserva.estado == "RESERVADO" or reserva.estado == "PENDIENTE":
        # Sí se puede
        se_puede_cancelar = True
    # Si es de un beneficiario (no pagó nada) también se puede
    if reserva.tipo == "BENEFICIARIO" and reserva.estado == "PAGADO":
        # Sí se puede
        se_puede_cancelar = True
    # Si no se puede cancelar
    if se_puede_cancelar == False:
        # Respondo 400
        error_regla("No se puede cancelar una reserva en estado " + reserva.estado)
    # Si el menú es de un día que ya pasó
    if reserva.menu.fecha < date.today():
        # Respondo 400
        error_regla("No se puede cancelar la reserva de un día que ya pasó")
    # Reviso que esté en el horario
    if not esta_en_horario():
        # Respondo 400
        error_regla("Solo se puede cancelar entre las " + str(hora_apertura) + ":00 y las " + str(hora_cierre) + ":00")
    # Le devuelvo el almuerzo al menú
    reserva.menu.cantidad_disponible = reserva.menu.cantidad_disponible + 1
    # Cambio el estado a cancelada
    reserva.estado = "CANCELADA"
    # Guardo los cambios de la reserva y del menú
    guardar_cambios(bd, reserva)
    # Devuelvo la reserva
    return convertir_reserva(reserva)


# Función para marcar si una reserva se pagó o no
def marcar_pago(bd, reserva_id, datos):
    # El estado solo puede ser PAGADO o NO_PAGADO
    if datos.estado != "PAGADO" and datos.estado != "NO_PAGADO":
        # Respondo 400
        error_regla("El estado debe ser PAGADO o NO_PAGADO")
    # Busco la reserva
    reserva = buscar_reserva_existente(bd, reserva_id)
    # Los instructores pagan en la cartera, no aquí
    if reserva.tipo == "INSTRUCTOR":
        # Respondo 400
        error_regla("Los consumos de los instructores se pagan en la cartera")
    # Los beneficiarios no pagan
    if reserva.tipo == "BENEFICIARIO":
        # Respondo 400
        error_regla("La reserva de un beneficiario no tiene costo")
    # Si la reserva está cancelada
    if reserva.estado == "CANCELADA":
        # Respondo 400
        error_regla("La reserva está cancelada")
    # Cambio el estado
    reserva.estado = datos.estado
    # Guardo los cambios
    guardar_cambios(bd, reserva)
    # Devuelvo la reserva
    return convertir_reserva(reserva)
