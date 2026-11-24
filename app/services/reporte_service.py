# Lógica de los reportes: ventas por periodo e indicadores del día

# date es una fecha y timedelta sirve para sumar o restar días
from datetime import date, timedelta

# Funciones para responder los errores
from app.core.excepciones import error_regla
# Repositorios que uso
from app.repositories import reporte_repository, menu_repository, reserva_repository, sugerencia_repository
# Servicio de cartera para saber cuánto deben los instructores
from app.services import cartera_service


# Función que suma el valor de una lista de reservas
def sumar_valores(reservas):
    # Aquí sumo la plata
    total = 0
    # Recorro las reservas
    for reserva in reservas:
        # Sumo el valor de cada una
        total = total + reserva.valor
    # Devuelvo el total
    return total


# Función que calcula la fecha inicial y final de un periodo
def fechas_del_periodo(periodo, fecha):
    # Si el periodo es un día
    if periodo == "dia":
        # Empieza y termina el mismo día
        return fecha, fecha
    # Si el periodo es una semana
    if periodo == "semana":
        # Busco el lunes de esa semana (weekday da 0 para el lunes)
        desde = fecha - timedelta(days=fecha.weekday())
        # El domingo es 6 días después del lunes
        return desde, desde + timedelta(days=6)
    # Si el periodo es un mes
    if periodo == "mes":
        # Si es diciembre el mes siguiente es enero del otro año
        if fecha.month == 12:
            # Primer día del mes siguiente
            primer_dia_siguiente = date(fecha.year + 1, 1, 1)
        # Si no es diciembre
        else:
            # Primer día del mes siguiente
            primer_dia_siguiente = date(fecha.year, fecha.month + 1, 1)
        # Del primer día del mes hasta un día antes del primer día del mes siguiente
        return date(fecha.year, fecha.month, 1), primer_dia_siguiente - timedelta(days=1)
    # Si el periodo es un año
    if periodo == "anio":
        # Del primero de enero al 31 de diciembre
        return date(fecha.year, 1, 1), date(fecha.year, 12, 31)
    # Si mandaron otra cosa respondo 400
    error_regla("El periodo debe ser dia, semana, mes o anio")


# Función para sacar las ventas de un día, semana, mes o año
def reporte_ventas(bd, periodo, fecha):
    # Si no mandaron fecha uso la de hoy
    if fecha is None:
        # Fecha de hoy
        fecha = date.today()
    # Saco la fecha inicial y la final del periodo
    desde, hasta = fechas_del_periodo(periodo, fecha)
    # Traigo los menús de ese periodo ordenados por fecha
    menus = reporte_repository.listar_menus_entre_fechas(bd, desde, hasta)
    # Aquí cuento todos los almuerzos
    total_almuerzos = 0
    # Aquí sumo toda la plata
    total_ingresos = 0
    # Aquí guardo las ventas de cada día
    por_dia = []
    # Aquí guardo las ventas por tipo de cliente
    por_tipo = {
        "APRENDIZ": {"almuerzos": 0, "ingresos": 0},  # Aprendices
        "BENEFICIARIO": {"almuerzos": 0, "ingresos": 0},  # Beneficiarios
        "INSTRUCTOR": {"almuerzos": 0, "ingresos": 0},  # Instructores
        "INVITADO": {"almuerzos": 0, "ingresos": 0},  # Invitados
    }
    # Recorro los menús
    for menu in menus:
        # Traigo las reservas del menú que no están canceladas
        reservas = reserva_repository.listar_activas_por_menu(bd, menu.id)
        # Almuerzos de ese día
        almuerzos_dia = len(reservas)
        # Plata de ese día: solo cuenta lo que ya está pagado, no lo que quedó reservado o pendiente
        ingresos_dia = sumar_valores([reserva for reserva in reservas if reserva.estado == "PAGADO"])
        # Recorro las reservas para separarlas por tipo
        for reserva in reservas:
            # Cuento el almuerzo en su tipo
            por_tipo[reserva.tipo]["almuerzos"] = por_tipo[reserva.tipo]["almuerzos"] + 1
            # Sumo la plata en su tipo solo si ya se cobró
            if reserva.estado == "PAGADO":
                por_tipo[reserva.tipo]["ingresos"] = por_tipo[reserva.tipo]["ingresos"] + reserva.valor
        # Si ese día se vendió algo
        if almuerzos_dia > 0:
            # Lo agrego a la lista de días
            por_dia.append({"fecha": menu.fecha, "almuerzos": almuerzos_dia, "ingresos": ingresos_dia})
        # Sumo los almuerzos del día al total
        total_almuerzos = total_almuerzos + almuerzos_dia
        # Sumo la plata del día al total
        total_ingresos = total_ingresos + ingresos_dia
    # Devuelvo el reporte
    return {
        "periodo": periodo,  # dia, semana, mes o anio
        "desde": desde,  # Fecha inicial
        "hasta": hasta,  # Fecha final
        "total_almuerzos": total_almuerzos,  # Almuerzos vendidos
        "total_ingresos": total_ingresos,  # Plata total
        "por_tipo": por_tipo,  # Ventas por tipo de cliente
        "por_dia": por_dia,  # Ventas de cada día
    }


# Función para sacar los indicadores de hoy
def indicadores(bd):
    # Fecha de hoy
    hoy = date.today()
    # Almuerzos vendidos hoy
    ventas_hoy = 0
    # Plata de hoy
    ingresos_hoy = 0
    # Busco el menú de hoy
    menu = menu_repository.buscar_por_fecha(bd, hoy)
    # Si hay menú hoy
    if menu is not None:
        # Traigo las reservas de hoy que no están canceladas
        reservas = reserva_repository.listar_activas_por_menu(bd, menu.id)
        # Cuento los almuerzos
        ventas_hoy = len(reservas)
        # Sumo la plata ya cobrada (las reservas sin pagar no son ingreso todavía)
        ingresos_hoy = sumar_valores([reserva for reserva in reservas if reserva.estado == "PAGADO"])
    # Traigo las deudas de los instructores que deben algo
    deudas = cartera_service.deudas_de_instructores(bd)
    # Toda la plata que deben
    deuda_pendiente = 0
    # Recorro las deudas
    for deuda in deudas:
        # Sumo cada deuda
        deuda_pendiente = deuda_pendiente + deuda["saldo"]
    # Devuelvo los indicadores
    return {
        "fecha": hoy,  # Fecha de hoy
        "ventas_hoy": ventas_hoy,  # Almuerzos de hoy
        "ingresos_hoy": ingresos_hoy,  # Plata de hoy
        "instructores_con_deuda": len(deudas),  # Cuántos instructores deben
        "deuda_pendiente": deuda_pendiente,  # Cuánto deben entre todos
        "sugerencias_pendientes": sugerencia_repository.contar_por_estado(bd, "PENDIENTE"),  # Sugerencias sin atender
    }
