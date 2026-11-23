# Lógica de las fichas (grupos de formación)

# date es una fecha
from datetime import date

# Modelo de ficha para crear fichas nuevas
from app.models.ficha import modelo_ficha
# Funciones para responder los errores
from app.core.excepciones import error_regla, error_no_encontrado, error_duplicado
# Funciones para buscar, guardar y borrar en la base de datos
from app.database.conexion import guardar, guardar_cambios, eliminar, buscar_por_id
# Repositorios que uso
from app.repositories import ficha_repository, usuario_repository, menu_repository, reserva_repository

# Jornadas que se pueden usar
jornadas = ["DIURNA", "NOCTURNA", "MIXTA", "FIN_DE_SEMANA"]


# Función que revisa que la jornada esté en la lista
def revisar_jornada(jornada):
    # Si la jornada no está en la lista
    if jornada not in jornadas:
        # Respondo 400
        error_regla("La jornada debe ser DIURNA, NOCTURNA, MIXTA o FIN_DE_SEMANA")


# Función que busca una ficha y si no existe responde 404
def buscar_ficha_existente(bd, ficha_id):
    # Busco la ficha
    ficha = buscar_por_id(bd, modelo_ficha, ficha_id)
    # Si no existe
    if ficha is None:
        # Respondo 404
        error_no_encontrado("La ficha no existe")
    # Devuelvo la ficha
    return ficha


# Función para traer la lista de fichas
def listar_fichas(bd, buscar, jornada, activo, saltar, limite):
    # Le pido la lista al repositorio
    return ficha_repository.listar(bd, buscar, jornada, activo, saltar, limite)


# Función para sacar las estadísticas de los grupos en una fecha
def estadisticas(bd, fecha):
    # Si no mandaron fecha uso la de hoy
    if fecha is None:
        # Fecha de hoy
        fecha = date.today()
    # Traigo las fichas activas
    fichas_activas = ficha_repository.listar_activas(bd)
    # Cuento los grupos
    total_grupos = len(fichas_activas)
    # Aquí voy a sumar los estudiantes
    total_estudiantes = 0
    # Recorro las fichas
    for ficha in fichas_activas:
        # Sumo los estudiantes de cada ficha
        total_estudiantes = total_estudiantes + ficha.cantidad_estudiantes
    # Busco el rol de aprendiz
    rol_aprendiz = usuario_repository.buscar_rol_por_nombre(bd, "aprendiz")
    # Cuento los aprendices activos que tienen cuenta
    aprendices_con_cuenta = usuario_repository.contar_activos_por_rol(bd, rol_aprendiz.id)
    # Busco el menú de esa fecha
    menu = menu_repository.buscar_por_fecha(bd, fecha)
    # Al principio no hay almuerzos reservados
    almuerzos_reservados = 0
    # Si hay menú ese día
    if menu is not None:
        # Cuento las reservas de aprendices que no están canceladas
        almuerzos_reservados = reserva_repository.contar_de_aprendices_por_menu(bd, menu.id)
    # El promedio empieza en 0
    promedio = 0
    # Si hay grupos calculo el promedio (para no dividir entre 0)
    if total_grupos > 0:
        # Promedio de almuerzos por grupo con 2 decimales
        promedio = round(almuerzos_reservados / total_grupos, 2)
    # Devuelvo las estadísticas
    return {
        "fecha": fecha,  # Fecha consultada
        "total_grupos": total_grupos,  # Cantidad de fichas activas
        "total_estudiantes": total_estudiantes,  # Suma de estudiantes
        "aprendices_con_cuenta": aprendices_con_cuenta,  # Aprendices registrados
        "almuerzos_reservados": almuerzos_reservados,  # Almuerzos de aprendices ese día
        "promedio_por_grupo": promedio,  # Promedio por grupo
    }


# Función para ver los aprendices de una ficha que reservaron almuerzo en una fecha
def reservas_de_ficha(bd, ficha_id, fecha):
    # Reviso que la ficha exista
    buscar_ficha_existente(bd, ficha_id)
    # Si no mandaron fecha uso la de hoy
    if fecha is None:
        # Fecha de hoy
        fecha = date.today()
    # Busco el menú de esa fecha
    menu = menu_repository.buscar_por_fecha(bd, fecha)
    # Si no hay menú ese día no hay reservas
    if menu is None:
        # Devuelvo una lista vacía
        return []
    # Traigo las reservas de ese menú que no están canceladas
    reservas = reserva_repository.listar_activas_por_menu(bd, menu.id)
    # Aquí voy a guardar los aprendices de la ficha
    lista = []
    # Recorro las reservas
    for reserva in reservas:
        # Si el usuario de la reserva es de esta ficha
        if reserva.usuario.ficha_id == ficha_id:
            # Lo agrego a la lista
            lista.append({
                "reserva_id": reserva.id,  # Id de la reserva
                "aprendiz_id": reserva.usuario.id,  # Id del aprendiz
                "nombre": reserva.usuario.nombre,  # Nombre del aprendiz
                "documento": reserva.usuario.documento,  # Documento del aprendiz
                "tipo": reserva.tipo,  # APRENDIZ o BENEFICIARIO
                "valor": reserva.valor,  # Lo que tiene que pagar
                "estado": reserva.estado,  # Si ya pagó o no
            })
    # Devuelvo la lista
    return lista


# Función para crear una ficha
def crear_ficha(bd, datos):
    # El código solo puede tener números
    if not datos.codigo.isdigit():
        # Respondo 400
        error_regla("El código de la ficha solo puede tener números")
    # La jornada tiene que estar en la lista
    revisar_jornada(datos.jornada)
    # Si ya existe una ficha con ese código
    if ficha_repository.buscar_por_codigo(bd, datos.codigo) is not None:
        # Respondo 409 porque ese valor no se puede repetir
        error_duplicado("Ya existe una ficha con ese código")
    # Creo la ficha
    nueva_ficha = modelo_ficha(
        codigo=datos.codigo,  # Código
        programa=datos.programa,  # Programa
        jornada=datos.jornada,  # Jornada
        vocero=datos.vocero,  # Vocero
        cantidad_estudiantes=datos.cantidad_estudiantes,  # Cantidad de estudiantes
    )
    # La guardo en la base de datos y la devuelvo
    return guardar(bd, nueva_ficha)


# Función para actualizar una ficha
def actualizar_ficha(bd, ficha_id, datos):
    # Busco la ficha
    ficha = buscar_ficha_existente(bd, ficha_id)
    # Si mandaron programa
    if datos.programa is not None:
        # Cambio el programa
        ficha.programa = datos.programa
    # Si mandaron jornada
    if datos.jornada is not None:
        # Reviso que la jornada esté en la lista
        revisar_jornada(datos.jornada)
        # Cambio la jornada
        ficha.jornada = datos.jornada
    # Si mandaron vocero
    if datos.vocero is not None:
        # Cambio el vocero
        ficha.vocero = datos.vocero
    # Si mandaron cantidad de estudiantes
    if datos.cantidad_estudiantes is not None:
        # Cambio la cantidad
        ficha.cantidad_estudiantes = datos.cantidad_estudiantes
    # Guardo los cambios y devuelvo la ficha
    return guardar_cambios(bd, ficha)


# Función para eliminar una ficha
def eliminar_ficha(bd, ficha_id):
    # Busco la ficha
    ficha = buscar_ficha_existente(bd, ficha_id)
    # Si ya está inactiva
    if ficha.activo == False:
        # Respondo 400
        error_regla("La ficha ya está inactiva")
    # Cuento cuántos aprendices tiene la ficha
    cantidad_aprendices = usuario_repository.contar_por_ficha(bd, ficha_id)
    # Si tiene aprendices no la puedo borrar
    if cantidad_aprendices > 0:
        # Solo la desactivo (borrado lógico)
        ficha.activo = False
        # Guardo los cambios
        guardar_cambios(bd, ficha)
        # Devuelvo un mensaje
        return {"mensaje": "La ficha tiene aprendices, por eso solo se desactivó"}
    # Si no tiene aprendices la borro de verdad
    eliminar(bd, ficha)
    # Devuelvo un mensaje
    return {"mensaje": "La ficha se eliminó"}
