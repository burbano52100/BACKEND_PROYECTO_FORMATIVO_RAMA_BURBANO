# Rutas de la cartera: lo que deben los instructores y los pagos que hacen

# date es una fecha
from datetime import date

# APIRouter agrupa las rutas, Depends es para dependencias y HTTPException para los errores
from fastapi import APIRouter, Depends, HTTPException
# Session es el tipo de la sesión de la base de datos
from sqlalchemy.orm import Session

# Función que da la sesión de la base de datos
from app.database import get_db
# Modelos que uso
from app.models import Usuario, Rol, Reserva, PagoInstructor
# Esquema que uso
from app.schemas import PagoCrear
# Funciones de seguridad
from app.seguridad import obtener_usuario_actual, verificar_rol

# Creo el router, todas las rutas empiezan con /cartera
router = APIRouter(prefix="/cartera", tags=["Cartera"])

# Formas de pago que se aceptan
METODOS_PAGO = ["EFECTIVO", "TRANSFERENCIA", "NOMINA"]
# Días que tiene el instructor para pagar, después la deuda queda vencida
DIAS_PARA_PAGAR = 30


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


# Función que calcula cuánto debe un instructor
def calcular_deuda(instructor, db):
    # Traigo los consumos del instructor que no están cancelados
    reservas = db.query(Reserva).filter(
        Reserva.usuario_id == instructor.id,  # Del instructor
        Reserva.tipo == "INSTRUCTOR",  # Que sean consumos de instructor
        Reserva.estado != "CANCELADA",  # Que no estén cancelados
    ).all()
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
    pagos = db.query(PagoInstructor).filter(PagoInstructor.instructor_id == instructor.id).all()
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
            if dias > DIAS_PARA_PAGAR:
                # La deuda está vencida
                estado = "VENCIDA"
                # Calculo cuántos días lleva vencida
                dias_vencidos = dias - DIAS_PARA_PAGAR
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


# Función que uso para ordenar las deudas por el saldo
def obtener_saldo(deuda):
    # Devuelvo el saldo de la deuda
    return deuda["saldo"]


# Ruta para ver los instructores que deben (solo el encargado)
@router.get("")
def listar_cartera(solo_vencidas: bool = False, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, ["encargado"])
    # Busco el rol de instructor
    rol_instructor = db.query(Rol).filter(Rol.nombre == "instructor").first()
    # Traigo todos los instructores
    instructores = db.query(Usuario).filter(Usuario.rol_id == rol_instructor.id).all()
    # Aquí voy a guardar los que deben
    deudores = []
    # Recorro los instructores
    for instructor in instructores:
        # Calculo la deuda de cada uno
        deuda = calcular_deuda(instructor, db)
        # Si debe algo
        if deuda["saldo"] > 0:
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


# Ruta para que el instructor vea su propia cuenta del mes
@router.get("/mi-cuenta")
def mi_cuenta(db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo los instructores tienen cuenta
    verificar_rol(usuario_actual, ["instructor"])
    # Calculo la deuda del instructor
    deuda = calcular_deuda(usuario_actual, db)
    # Fecha de hoy
    hoy = date.today()
    # Traigo los consumos del instructor que no están cancelados
    reservas = db.query(Reserva).filter(Reserva.usuario_id == usuario_actual.id, Reserva.estado != "CANCELADA").all()
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
    # Traigo los pagos del instructor del más nuevo al más viejo
    pagos = db.query(PagoInstructor).filter(PagoInstructor.instructor_id == usuario_actual.id).order_by(PagoInstructor.id.desc()).all()
    # Aquí voy a guardar los pagos convertidos
    lista_pagos = []
    # Recorro los pagos
    for pago in pagos:
        # Agrego cada pago convertido
        lista_pagos.append(convertir_pago(pago))
    # Agrego los datos del mes a la deuda
    deuda["almuerzos_mes"] = almuerzos_mes
    # Agrego el valor del mes
    deuda["valor_mes"] = valor_mes
    # Agrego la lista de pagos
    deuda["pagos"] = lista_pagos
    # Devuelvo la cuenta
    return deuda


# Ruta para ver la cuenta de un instructor (solo el encargado)
@router.get("/{instructor_id}")
def ver_cuenta_instructor(instructor_id: int, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede entrar
    verificar_rol(usuario_actual, ["encargado"])
    # Busco el usuario
    instructor = db.query(Usuario).filter(Usuario.id == instructor_id).first()
    # Si no existe
    if instructor is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="El usuario no existe")
    # Si no es instructor
    if instructor.rol.nombre != "instructor":
        # Respondo 400
        raise HTTPException(status_code=400, detail="El usuario no es instructor")
    # Calculo la deuda
    deuda = calcular_deuda(instructor, db)
    # Traigo los pagos del más nuevo al más viejo
    pagos = db.query(PagoInstructor).filter(PagoInstructor.instructor_id == instructor_id).order_by(PagoInstructor.id.desc()).all()
    # Aquí voy a guardar los pagos convertidos
    lista_pagos = []
    # Recorro los pagos
    for pago in pagos:
        # Agrego cada pago convertido
        lista_pagos.append(convertir_pago(pago))
    # Agrego la lista de pagos a la deuda
    deuda["pagos"] = lista_pagos
    # Devuelvo la cuenta
    return deuda


# Ruta para registrar un pago de un instructor (solo el encargado)
@router.post("/{instructor_id}/pagos", status_code=201)
def registrar_pago(instructor_id: int, datos: PagoCrear, db: Session = Depends(get_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # Solo el encargado puede registrar pagos
    verificar_rol(usuario_actual, ["encargado"])
    # Reviso que el método de pago sea válido
    if datos.metodo not in METODOS_PAGO:
        # Respondo 400
        raise HTTPException(status_code=400, detail="El método debe ser EFECTIVO, TRANSFERENCIA o NOMINA")
    # Busco el usuario
    instructor = db.query(Usuario).filter(Usuario.id == instructor_id).first()
    # Si no existe
    if instructor is None:
        # Respondo 404
        raise HTTPException(status_code=404, detail="El usuario no existe")
    # Si no es instructor
    if instructor.rol.nombre != "instructor":
        # Respondo 400
        raise HTTPException(status_code=400, detail="El usuario no es instructor")
    # Calculo lo que debe
    deuda = calcular_deuda(instructor, db)
    # Guardo el saldo antes del pago
    saldo_anterior = deuda["saldo"]
    # Si no debe nada
    if saldo_anterior <= 0:
        # Respondo 400
        raise HTTPException(status_code=400, detail="El instructor no tiene deuda")
    # El pago no puede ser mayor que lo que debe
    if datos.valor > saldo_anterior:
        # Respondo 400
        raise HTTPException(status_code=400, detail="El pago no puede ser mayor que la deuda (" + str(saldo_anterior) + ")")
    # Creo el pago
    nuevo_pago = PagoInstructor(
        instructor_id=instructor_id,  # Instructor
        valor=datos.valor,  # Valor
        metodo=datos.metodo,  # Método
        observacion=datos.observacion,  # Nota
    )
    # Lo agrego a la sesión
    db.add(nuevo_pago)
    # Calculo lo que queda debiendo
    saldo_actual = round(saldo_anterior - datos.valor, 2)
    # Si ya pagó todo
    if saldo_actual <= 0:
        # Traigo los consumos pendientes del instructor
        pendientes = db.query(Reserva).filter(Reserva.usuario_id == instructor_id, Reserva.estado == "PENDIENTE").all()
        # Recorro los consumos pendientes
        for reserva in pendientes:
            # Los marco como pagados
            reserva.estado = "PAGADO"
    # Guardo el pago y los consumos al mismo tiempo
    db.commit()
    # Vuelvo a leer el pago
    db.refresh(nuevo_pago)
    # Respondo con los datos del pago
    return {
        "mensaje": "Pago registrado",  # Mensaje
        "pago": convertir_pago(nuevo_pago),  # El pago
        "saldo_anterior": saldo_anterior,  # Lo que debía antes
        "saldo_actual": saldo_actual,  # Lo que debe ahora
    }
