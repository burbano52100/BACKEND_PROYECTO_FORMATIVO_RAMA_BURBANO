# Lógica de la cartera: lo que deben los instructores y los pagos que hacen

# date es una fecha
from datetime import date

# Modelo de pago para crear pagos nuevos
from app.models.reserva import modelo_pago_instructor
# Funciones para responder los errores
from app.core.excepciones import error_regla
# Funciones para guardar en la base de datos
from app.database.conexion import guardar
# Repositorios que uso
from app.repositories import cartera_repository, usuario_repository
# Servicio de usuarios para buscar el instructor
from app.services import usuario_service

# Métodos con los que se puede pagar
metodos_pago = ["EFECTIVO", "TRANSFERENCIA", "NOMINA"]
# Días que tiene el instructor para pagar antes de que la deuda quede vencida
dias_para_pagar = 30


# Función que convierte un pago en un diccionario para responder
def convertir_pago(pago):
    # Armo el diccionario con los datos del pago
    return {
        "id": pago.id,  # Id del pago
        "valor": pago.valor,  # Cuánto pagó
        "metodo": pago.metodo,  # Cómo pagó
        "observacion": pago.observacion,  # Nota del pago
        "fecha_pago": pago.fecha_pago,  # Cuándo pagó
    }


# Función que trae los pagos de un instructor ya convertidos
def lista_de_pagos(bd, instructor_id):
    # Traigo los pagos del más nuevo al más viejo
    pagos = cartera_repository.listar_pagos(bd, instructor_id)
    # Aquí voy a guardar los pagos convertidos
    lista = []
    # Recorro los pagos
    for pago in pagos:
        # Agrego cada pago convertido
        lista.append(convertir_pago(pago))
    # Devuelvo la lista
    return lista


# Función que busca un usuario y revisa que sea instructor
def buscar_instructor(bd, instructor_id):
    # Busco el usuario (si no existe responde 404)
    instructor = usuario_service.buscar_usuario_existente(bd, instructor_id)
    # Si no es instructor
    if instructor.rol.nombre != "instructor":
        # Respondo 400
        error_regla("El usuario no es instructor")
    # Devuelvo el instructor
    return instructor


# Función que calcula cuánto debe un instructor
def calcular_deuda(bd, instructor):
    # Traigo los consumos del instructor que no están cancelados
    reservas = cartera_repository.listar_consumos(bd, instructor.id)
    # Aquí sumo todo lo que ha consumido
    total_consumido = 0
    # Aquí cuento los almuerzos sin pagar
    almuerzos_pendientes = 0
    # Aquí guardo la fecha del consumo sin pagar más viejo
    fecha_mas_antigua = None
    # Recorro los consumos
    for reserva in reservas:
        # Sumo el valor del consumo
        total_consumido = total_consumido + reserva.valor
        # Si el consumo está pendiente
        if reserva.estado == "PENDIENTE":
            # Lo cuento
            almuerzos_pendientes = almuerzos_pendientes + 1
            # Si es el primero o es más viejo que el que tenía guardado
            if fecha_mas_antigua is None or reserva.menu.fecha < fecha_mas_antigua:
                # Guardo esta fecha
                fecha_mas_antigua = reserva.menu.fecha
    # Traigo los pagos del instructor
    pagos = cartera_repository.listar_pagos(bd, instructor.id)
    # Aquí sumo todo lo que ha pagado
    total_pagado = 0
    # Recorro los pagos
    for pago in pagos:
        # Sumo el valor del pago
        total_pagado = total_pagado + pago.valor
    # Lo que debe es lo que consumió menos lo que pagó (redondeado a 2 decimales)
    saldo = round(total_consumido - total_pagado, 2)
    # Al principio no tiene días vencidos
    dias_vencidos = 0
    # Si no debe nada
    if saldo <= 0:
        # Está al día
        estado = "AL_DIA"
    # Si debe algo
    else:
        # La deuda está activa
        estado = "ACTIVA"
        # Si tiene consumos pendientes
        if fecha_mas_antigua is not None:
            # Cuento los días desde el consumo más viejo hasta hoy
            dias = (date.today() - fecha_mas_antigua).days
            # Si ya pasaron más días de los que tiene para pagar
            if dias > dias_para_pagar:
                # La deuda está vencida
                estado = "VENCIDA"
                # Calculo cuántos días lleva vencida
                dias_vencidos = dias - dias_para_pagar
    # Devuelvo los datos de la deuda
    return {
        "instructor_id": instructor.id,  # Id del instructor
        "nombre": instructor.nombre,  # Nombre
        "documento": instructor.documento,  # Documento
        "total_consumido": total_consumido,  # Lo que ha consumido
        "total_pagado": total_pagado,  # Lo que ha pagado
        "saldo": saldo,  # Lo que debe
        "almuerzos_pendientes": almuerzos_pendientes,  # Almuerzos sin pagar
        "dias_vencidos": dias_vencidos,  # Días de retraso
        "estado": estado,  # AL_DIA, ACTIVA o VENCIDA
    }


# Función que trae las deudas de todos los instructores que deben algo
def deudas_de_instructores(bd):
    # Busco el rol de instructor
    rol_instructor = usuario_repository.buscar_rol_por_nombre(bd, "instructor")
    # Traigo todos los instructores
    instructores = usuario_repository.listar_por_rol(bd, rol_instructor.id)
    # Aquí voy a guardar los que deben
    deudas = []
    # Recorro los instructores
    for instructor in instructores:
        # Calculo la deuda de cada uno
        deuda = calcular_deuda(bd, instructor)
        # Si debe algo
        if deuda["saldo"] > 0:
            # Lo agrego a la lista
            deudas.append(deuda)
    # Devuelvo la lista
    return deudas


# Función que uso para ordenar las deudas por el saldo
def obtener_saldo(deuda):
    # Devuelvo el saldo de la deuda
    return deuda["saldo"]


# Función para ver los instructores que deben con el resumen
def listar_cartera(bd, solo_vencidas):
    # Aquí voy a guardar los deudores que se van a mostrar
    deudores = []
    # Recorro las deudas de los instructores
    for deuda in deudas_de_instructores(bd):
        # Si no pidieron solo vencidas, o si la deuda está vencida
        if solo_vencidas == False or deuda["estado"] == "VENCIDA":
            # Lo agrego a la lista
            deudores.append(deuda)
    # Ordeno de mayor a menor deuda
    deudores.sort(key=obtener_saldo, reverse=True)
    # Aquí sumo toda la deuda
    deuda_total = 0
    # Aquí guardo la deuda más grande
    mayor_deuda = 0
    # Recorro los deudores
    for deuda in deudores:
        # Sumo la deuda
        deuda_total = deuda_total + deuda["saldo"]
        # Si esta deuda es más grande que la que tenía
        if deuda["saldo"] > mayor_deuda:
            # La guardo como la mayor
            mayor_deuda = deuda["saldo"]
    # El promedio empieza en 0
    promedio = 0
    # Si hay deudores calculo el promedio
    if len(deudores) > 0:
        # Promedio con 2 decimales
        promedio = round(deuda_total / len(deudores), 2)
    # Devuelvo el resumen y la lista
    return {
        "resumen": {  # Resumen de toda la cartera
            "total_deudores": len(deudores),  # Cuántos deben
            "deuda_total": deuda_total,  # Suma de todas las deudas
            "promedio_deuda": promedio,  # Promedio de deuda
            "mayor_deuda": mayor_deuda,  # La deuda más grande
        },
        "deudores": deudores,  # Lista de los que deben
    }


# Función para que el instructor vea su propia cuenta del mes
def mi_cuenta(bd, instructor):
    # Calculo la deuda del instructor
    deuda = calcular_deuda(bd, instructor)
    # Fecha de hoy
    hoy = date.today()
    # Traigo los consumos del instructor que no están cancelados
    reservas = cartera_repository.listar_consumos(bd, instructor.id)
    # Aquí cuento los almuerzos de este mes
    almuerzos_mes = 0
    # Aquí sumo el valor de este mes
    valor_mes = 0
    # Recorro los consumos
    for reserva in reservas:
        # Si el consumo es de este mes y de este año
        if reserva.menu.fecha.month == hoy.month and reserva.menu.fecha.year == hoy.year:
            # Lo cuento
            almuerzos_mes = almuerzos_mes + 1
            # Sumo el valor
            valor_mes = valor_mes + reserva.valor
    # Agrego los datos del mes a la deuda
    deuda["almuerzos_mes"] = almuerzos_mes
    # Agrego el valor del mes
    deuda["valor_mes"] = valor_mes
    # Agrego la lista de pagos
    deuda["pagos"] = lista_de_pagos(bd, instructor.id)
    # Devuelvo la cuenta
    return deuda


# Función para ver la cuenta de un instructor
def ver_cuenta_instructor(bd, instructor_id):
    # Busco el instructor
    instructor = buscar_instructor(bd, instructor_id)
    # Calculo la deuda
    deuda = calcular_deuda(bd, instructor)
    # Agrego la lista de pagos a la deuda
    deuda["pagos"] = lista_de_pagos(bd, instructor_id)
    # Devuelvo la cuenta
    return deuda


# Función para registrar un pago de un instructor
def registrar_pago(bd, instructor_id, datos):
    # Reviso que el método de pago sea válido
    if datos.metodo not in metodos_pago:
        # Respondo 400
        error_regla("El método debe ser EFECTIVO, TRANSFERENCIA o NOMINA")
    # Busco el instructor
    instructor = buscar_instructor(bd, instructor_id)
    # Calculo lo que debe
    deuda = calcular_deuda(bd, instructor)
    # Guardo el saldo antes del pago
    saldo_anterior = deuda["saldo"]
    # Si no debe nada
    if saldo_anterior <= 0:
        # Respondo 400
        error_regla("El instructor no tiene deuda")
    # El pago no puede ser mayor que lo que debe
    if datos.valor > saldo_anterior:
        # Respondo 400
        error_regla("El pago no puede ser mayor que la deuda (" + str(saldo_anterior) + ")")
    # Creo el pago
    nuevo_pago = modelo_pago_instructor(
        instructor_id=instructor_id,  # Instructor
        valor=datos.valor,  # Valor
        metodo=datos.metodo,  # Método
        observacion=datos.observacion,  # Nota
    )
    # Calculo lo que queda debiendo
    saldo_actual = round(saldo_anterior - datos.valor, 2)
    # Si ya pagó todo
    if saldo_actual <= 0:
        # Recorro los consumos pendientes del instructor
        for reserva in cartera_repository.listar_consumos_pendientes(bd, instructor_id):
            # Los marco como pagados
            reserva.estado = "PAGADO"
    # Guardo el pago y los consumos al mismo tiempo
    guardar(bd, nuevo_pago)
    # Devuelvo los datos del pago
    return {
        "mensaje": "Pago registrado",  # Mensaje
        "pago": convertir_pago(nuevo_pago),  # El pago
        "saldo_anterior": saldo_anterior,  # Lo que debía antes
        "saldo_actual": saldo_actual,  # Lo que debe ahora
    }
