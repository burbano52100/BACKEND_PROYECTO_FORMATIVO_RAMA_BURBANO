# Lógica del menú del día

# date es una fecha
from datetime import date

# Modelo de menú para crear menús nuevos
from app.models.menu import modelo_menu
# Funciones para responder los errores
from app.core.excepciones import error_regla, error_no_encontrado, error_duplicado
# Funciones para buscar, guardar y borrar en la base de datos
from app.database.conexion import guardar, guardar_cambios, eliminar, buscar_por_id
# Repositorios que uso
from app.repositories import menu_repository, reserva_repository


# Función que dice cuánto le toca pagar a un usuario según su rol
def calcular_precio(usuario, menu):
    # Si es aprendiz
    if usuario.rol.nombre == "aprendiz":
        # Si es beneficiario no paga nada
        if usuario.es_beneficiario == True:
            # Precio 0
            return 0
        # Si no es beneficiario paga el precio de aprendiz
        return menu.precio_aprendiz
    # El instructor paga lo mismo que el aprendiz (se le carga a su cuenta del mes)
    if usuario.rol.nombre == "instructor":
        # Precio de aprendiz
        return menu.precio_aprendiz
    # El invitado paga el precio de invitado
    if usuario.rol.nombre == "invitado":
        # Precio de invitado
        return menu.precio_invitado
    # El encargado no compra almuerzo
    return None


# Función que arma el menú con el precio que le toca a la persona que consulta
def menu_con_mi_precio(bd, menu, usuario):
    # Busco si la persona ya tiene una reserva para ese menú
    mi_reserva = reserva_repository.buscar_activa_de_usuario(bd, menu.id, usuario.id)
    # Al principio digo que no tiene reserva
    mi_reserva_id = None
    # Si sí tiene reserva
    if mi_reserva is not None:
        # Guardo el id de la reserva
        mi_reserva_id = mi_reserva.id
    # Devuelvo el menú con los datos extra
    return {
        "id": menu.id,  # Id del menú
        "fecha": menu.fecha,  # Fecha
        "nombre": menu.nombre,  # Nombre del plato
        "descripcion": menu.descripcion,  # Lo que trae
        "precio_aprendiz": menu.precio_aprendiz,  # Precio de aprendiz
        "precio_invitado": menu.precio_invitado,  # Precio de invitado
        "cantidad_total": menu.cantidad_total,  # Cuántos hay en total
        "cantidad_disponible": menu.cantidad_disponible,  # Cuántos quedan
        "vendidos": menu.cantidad_total - menu.cantidad_disponible,  # Cuántos se vendieron
        "agotado": menu.cantidad_disponible == 0,  # True si ya no quedan
        "precio_para_mi": calcular_precio(usuario, menu),  # Lo que me toca pagar a mí
        "mi_reserva_id": mi_reserva_id,  # Id de mi reserva (None si no he reservado)
    }


# Función que busca un menú y si no existe responde 404
def buscar_menu_existente(bd, menu_id):
    # Busco el menú
    menu = buscar_por_id(bd, modelo_menu, menu_id)
    # Si no existe
    if menu is None:
        # Respondo 404
        error_no_encontrado("El menú no existe")
    # Devuelvo el menú
    return menu


# Función para ver el menú de hoy con mi precio
def menu_de_hoy(bd, usuario):
    # Busco el menú activo de hoy
    menu = menu_repository.buscar_activo_por_fecha(bd, date.today())
    # Si no hay menú hoy
    if menu is None:
        # Respondo 404
        error_no_encontrado("Todavía no hay menú para hoy")
    # Devuelvo el menú con mi precio
    return menu_con_mi_precio(bd, menu, usuario)


# Función para ver los menús de hoy en adelante con mi precio
def proximos_menus(bd, usuario):
    # Traigo los menús activos desde hoy
    menus = menu_repository.listar_proximos(bd, date.today())
    # Aquí voy a guardar los menús con mi precio
    lista = []
    # Recorro los menús
    for menu in menus:
        # Agrego cada menú con mi precio
        lista.append(menu_con_mi_precio(bd, menu, usuario))
    # Devuelvo la lista
    return lista


# Función para traer todos los menús (historial)
def listar_menus(bd, desde, hasta, activo, saltar, limite):
    # Le pido la lista al repositorio
    return menu_repository.listar(bd, desde, hasta, activo, saltar, limite)


# Función para crear un menú
def crear_menu(bd, datos):
    # La fecha no puede ser de un día que ya pasó
    if datos.fecha < date.today():
        # Respondo 400
        error_regla("No se puede crear un menú para un día que ya pasó")
    # Si ya hay un menú en esa fecha
    if menu_repository.buscar_por_fecha(bd, datos.fecha) is not None:
        # Respondo 409 porque ese valor no se puede repetir
        error_duplicado("Ya existe un menú para esa fecha")
    # Creo el menú
    nuevo_menu = modelo_menu(
        fecha=datos.fecha,  # Fecha
        nombre=datos.nombre,  # Nombre
        descripcion=datos.descripcion,  # Descripción
        precio_aprendiz=datos.precio_aprendiz,  # Precio de aprendiz
        precio_invitado=datos.precio_invitado,  # Precio de invitado
        cantidad_total=datos.cantidad_total,  # Cantidad total
        cantidad_disponible=datos.cantidad_total,  # Al principio están todos disponibles
    )
    # Lo guardo en la base de datos y lo devuelvo
    return guardar(bd, nuevo_menu)


# Función para actualizar un menú
def actualizar_menu(bd, menu_id, datos):
    # Busco el menú
    menu = buscar_menu_existente(bd, menu_id)
    # No se puede cambiar un menú de un día que ya pasó
    if menu.fecha < date.today():
        # Respondo 400
        error_regla("No se puede cambiar el menú de un día que ya pasó")
    # Si mandaron nombre
    if datos.nombre is not None:
        # Cambio el nombre
        menu.nombre = datos.nombre
    # Si mandaron descripción
    if datos.descripcion is not None:
        # Cambio la descripción
        menu.descripcion = datos.descripcion
    # Si mandaron precio de aprendiz
    if datos.precio_aprendiz is not None:
        # Cambio el precio
        menu.precio_aprendiz = datos.precio_aprendiz
    # Si mandaron precio de invitado
    if datos.precio_invitado is not None:
        # Cambio el precio
        menu.precio_invitado = datos.precio_invitado
    # Si mandaron cantidad total
    if datos.cantidad_total is not None:
        # Calculo cuántos almuerzos ya se vendieron
        vendidos = menu.cantidad_total - menu.cantidad_disponible
        # La cantidad nueva no puede ser menor que lo vendido
        if datos.cantidad_total < vendidos:
            # Respondo 400
            error_regla("La cantidad no puede ser menor que los " + str(vendidos) + " almuerzos ya vendidos")
        # Cambio la cantidad total
        menu.cantidad_total = datos.cantidad_total
        # Lo disponible es lo nuevo menos lo vendido
        menu.cantidad_disponible = datos.cantidad_total - vendidos
    # Guardo los cambios y devuelvo el menú
    return guardar_cambios(bd, menu)


# Función para eliminar un menú
def eliminar_menu(bd, menu_id):
    # Busco el menú
    menu = buscar_menu_existente(bd, menu_id)
    # Si ya está inactivo
    if menu.activo == False:
        # Respondo 400
        error_regla("El menú ya está inactivo")
    # Si tiene reservas no lo puedo borrar
    if reserva_repository.contar_por_menu(bd, menu_id) > 0:
        # Solo lo desactivo (borrado lógico)
        menu.activo = False
        # Guardo los cambios
        guardar_cambios(bd, menu)
        # Devuelvo un mensaje
        return {"mensaje": "El menú tiene reservas, por eso solo se desactivó"}
    # Si no tiene reservas lo borro de verdad
    eliminar(bd, menu)
    # Devuelvo un mensaje
    return {"mensaje": "El menú se eliminó"}
