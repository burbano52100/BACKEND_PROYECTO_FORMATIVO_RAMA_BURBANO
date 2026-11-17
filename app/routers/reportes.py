# Rutas de los reportes de ventas y los indicadores del encargado

# date es una fecha y timedelta sirve para sumar o restar días
from datetime import date, timedelta
# Optional quiere decir que un parámetro puede venir vacío
from typing import Optional

# APIRouter agrupa las rutas, Depends es para dependencias y HTTPException para los errores
from fastapi import APIRouter, Depends, HTTPException
# Session es el tipo de la sesión de la base de datos
from sqlalchemy.orm import Session

# Función que da la sesión de la base de datos
from app.database import get_db
# Modelos que uso
from app.models import Menu, Reserva, Rol, Sugerencia, Usuario
# Uso la función de la cartera para calcular lo que deben los instructores
from app.routers.cartera import calcular_deuda
# Funciones de seguridad
from app.seguridad import obtener_usuario_actual, verificar_rol

# Creo el router, todas las rutas empiezan con /reportes
router = APIRouter(prefix="/reportes", tags=["Reportes"])


# Ruta para ver las ventas de un día, semana, mes o año (solo el encargado)
@router.get("/ventas")
def reporte_ventas(periodo: str = "dia", fecha: Optional[date] = None, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede ver los reportes
    verificar_rol(usuario_actual, ["encargado"])
    # Si no mandaron fecha uso la de hoy
    if fecha is None:
        # Fecha de hoy
        fecha = date.today()
    # Si el periodo es un día
    if periodo == "dia":
        # Empieza y termina el mismo día
        desde = fecha
        # Termina ese mismo día
        hasta = fecha
    # Si el periodo es una semana
    elif periodo == "semana":
        # Busco el lunes de esa semana (weekday da 0 para el lunes)
        desde = fecha - timedelta(days=fecha.weekday())
        # El domingo es 6 días después del lunes
        hasta = desde + timedelta(days=6)
    # Si el periodo es un mes
    elif periodo == "mes":
        # El primer día del mes
        desde = date(fecha.year, fecha.month, 1)
        # Si es diciembre el mes siguiente es enero del otro año
        if fecha.month == 12:
            # Primer día del mes siguiente
            primer_dia_siguiente = date(fecha.year + 1, 1, 1)
        # Si no es diciembre
        else:
            # Primer día del mes siguiente
            primer_dia_siguiente = date(fecha.year, fecha.month + 1, 1)
        # El último día del mes es un día antes del primer día del mes siguiente
        hasta = primer_dia_siguiente - timedelta(days=1)
    # Si el periodo es un año
    elif periodo == "anio":
        # Primero de enero
        desde = date(fecha.year, 1, 1)
        # 31 de diciembre
        hasta = date(fecha.year, 12, 31)
    # Si mandaron otra cosa
    else:
        # Respondo 400
        raise HTTPException(status_code=400, detail="El periodo debe ser dia, semana, mes o anio")
    # Traigo los menús de ese periodo ordenados por fecha
    menus = db.query(Menu).filter(Menu.fecha >= desde, Menu.fecha <= hasta).order_by(Menu.fecha).all()
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
        reservas = db.query(Reserva).filter(Reserva.menu_id == menu.id, Reserva.estado != "CANCELADA").all()
        # Almuerzos de ese día
        almuerzos_dia = 0
        # Plata de ese día
        ingresos_dia = 0
        # Recorro las reservas
        for reserva in reservas:
            # Cuento el almuerzo
            almuerzos_dia = almuerzos_dia + 1
            # Sumo la plata
            ingresos_dia = ingresos_dia + reserva.valor
            # Cuento el almuerzo en su tipo
            por_tipo[reserva.tipo]["almuerzos"] = por_tipo[reserva.tipo]["almuerzos"] + 1
            # Sumo la plata en su tipo
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


# Ruta para ver los indicadores de hoy (solo el encargado)
@router.get("/indicadores")
def indicadores(db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede ver los indicadores
    verificar_rol(usuario_actual, ["encargado"])
    # Fecha de hoy
    hoy = date.today()
    # Almuerzos vendidos hoy
    ventas_hoy = 0
    # Plata de hoy
    ingresos_hoy = 0
    # Busco el menú de hoy
    menu = db.query(Menu).filter(Menu.fecha == hoy).first()
    # Si hay menú hoy
    if menu is not None:
        # Traigo las reservas de hoy que no están canceladas
        reservas = db.query(Reserva).filter(Reserva.menu_id == menu.id, Reserva.estado != "CANCELADA").all()
        # Recorro las reservas
        for reserva in reservas:
            # Cuento el almuerzo
            ventas_hoy = ventas_hoy + 1
            # Sumo la plata
            ingresos_hoy = ingresos_hoy + reserva.valor
    # Busco el rol de instructor
    rol_instructor = db.query(Rol).filter(Rol.nombre == "instructor").first()
    # Traigo todos los instructores
    instructores = db.query(Usuario).filter(Usuario.rol_id == rol_instructor.id).all()
    # Instructores que deben
    instructores_con_deuda = 0
    # Toda la plata que deben
    deuda_pendiente = 0
    # Recorro los instructores
    for instructor in instructores:
        # Calculo lo que debe
        deuda = calcular_deuda(instructor, db)
        # Si debe algo
        if deuda["saldo"] > 0:
            # Lo cuento
            instructores_con_deuda = instructores_con_deuda + 1
            # Sumo su deuda
            deuda_pendiente = deuda_pendiente + deuda["saldo"]
    # Cuento las sugerencias que faltan por atender
    sugerencias_pendientes = db.query(Sugerencia).filter(Sugerencia.estado == "PENDIENTE").count()
    # Devuelvo los indicadores
    return {
        "fecha": hoy,  # Fecha de hoy
        "ventas_hoy": ventas_hoy,  # Almuerzos de hoy
        "ingresos_hoy": ingresos_hoy,  # Plata de hoy
        "instructores_con_deuda": instructores_con_deuda,  # Cuántos instructores deben
        "deuda_pendiente": deuda_pendiente,  # Cuánto deben entre todos
        "sugerencias_pendientes": sugerencias_pendientes,  # Sugerencias sin atender
    }
